#include "feedback_reader.h"
#include "../utils/parser.h"
#include "../utils/types.h"
#include <spdlog/spdlog.h>
#include <json/json.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <netinet/tcp.h>
#include <unistd.h>
#include <fcntl.h>
#include <cstring>
#include <cerrno>
#include <chrono>
#include <thread>

namespace modhost_bridge {

FeedbackReader::FeedbackReader(zmq::context_t& zmq_context,
                               zmq::socket_t& pub_socket,
                               const std::string& mod_host_host,
                               uint16_t mod_host_feedback_port,
                               std::shared_ptr<HealthState> health_state)
    : zmq_context_(zmq_context)
    , pub_socket_(pub_socket)
    , mod_host_host_(mod_host_host)
    , mod_host_feedback_port_(mod_host_feedback_port)
    , health_state_(health_state)
    , running_(false) {
}

FeedbackReader::~FeedbackReader() {
    stop();
}

void FeedbackReader::start() {
    if (running_) return;

    running_ = true;

    reader_thread_ = std::thread(&FeedbackReader::reader_loop, this);
}

void FeedbackReader::stop() {
    if (!running_) return;

    running_ = false;
    if (reader_thread_.joinable()) {
        reader_thread_.join();
    }
    if (tcp_socket_ >= 0) {
        close(tcp_socket_);
        tcp_socket_ = -1;
    }
}

void FeedbackReader::reader_loop() {
    // Starting backoff at 100ms, exponential up to 5s.
    const std::chrono::milliseconds MIN_DELAY(100);
    const std::chrono::milliseconds MAX_DELAY(5000);

    std::chrono::milliseconds current_delay = MIN_DELAY;

    while (running_) {
        try {
            if (connect_to_modhost()) {
                spdlog::info("Connected to mod-host feedback {}:{}",
                           mod_host_host_, mod_host_feedback_port_);
                health_state_->update_feedback_connection(true);

                char buffer[4096];
                std::string line_buffer;

                // Reset backoff on successful connect
                current_delay = MIN_DELAY;

                while (running_ && tcp_socket_ >= 0) {
                    ssize_t bytes_read = recv(tcp_socket_, buffer, sizeof(buffer) - 1, 0);
                    if (bytes_read > 0) {
                        buffer[bytes_read] = '\0';

                        // Process the received data (null-terminated messages)
                        for (size_t i = 0; i < static_cast<size_t>(bytes_read); ++i) {
                            char c = buffer[i];
                            if (c == '\0') {
                                if (!line_buffer.empty()) {
                                    try {
                                        auto message = parse_feedback_line(line_buffer);
                                        if (message) {
                                            Json::Value json_msg = to_json(*message);
                                            Json::StreamWriterBuilder writer;
                                            std::string json_str = Json::writeString(writer, json_msg);

                                            zmq::message_t zmq_msg(json_str.size());
                                            memcpy(zmq_msg.data(), json_str.c_str(), json_str.size());

                                            // Best-effort send
                                            try {
                                                pub_socket_.send(zmq_msg, zmq::send_flags::none);
                                            } catch (const std::exception& e) {
                                                spdlog::warn("Failed to publish feedback message: {}", e.what());
                                            }
                                        }
                                    } catch (const std::exception& e) {
                                        spdlog::warn("Failed parsing feedback line: {}", e.what());
                                    }
                                    line_buffer.clear();
                                }
                            } else {
                                line_buffer += c;
                            }
                        }
                    } else if (bytes_read == 0) {
                        // Connection closed by peer
                        spdlog::warn("Feedback connection closed by peer");
                        break;
                    } else {
                        // Timeout or error
                        if (errno == EWOULDBLOCK || errno == EAGAIN) {
                            // No data, small sleep to yield
                            std::this_thread::sleep_for(std::chrono::milliseconds(10));
                            continue;
                        }

                        spdlog::warn("Feedback connection error: {}", strerror(errno));
                        break;
                    }
                }

                health_state_->update_feedback_connection(false);
                if (tcp_socket_ >= 0) {
                    close(tcp_socket_);
                    tcp_socket_ = -1;
                }
            } else {
                health_state_->update_feedback_connection(false);
            }
        } catch (const std::exception& e) {
            spdlog::error("Feedback reader exception: {}", e.what());
            health_state_->update_feedback_connection(false);
            if (tcp_socket_ >= 0) {
                close(tcp_socket_);
                tcp_socket_ = -1;
            }
        }

        // Backoff before reconnect attempt
        if (running_) {
            spdlog::info("Feedback reader sleeping for {} ms before reconnect", current_delay.count());
            std::this_thread::sleep_for(current_delay);
            // Exponential backoff
            current_delay = std::min(std::chrono::duration_cast<std::chrono::milliseconds>(current_delay * 2), MAX_DELAY);
        }
    }
}

bool FeedbackReader::connect_to_modhost() {
    // Try resolving hostnames with getaddrinfo first so 'localhost' and
    // other names work. We'll attempt each returned address until one
    // successfully connects.
    struct addrinfo hints;
    struct addrinfo* res = nullptr;
    memset(&hints, 0, sizeof(hints));
    // Prefer IPv4 to avoid IPv6/localhost resolution issues in Docker host-networked tests
    hints.ai_family = AF_INET;
    hints.ai_socktype = SOCK_STREAM;

    std::string port_str = std::to_string(mod_host_feedback_port_);
    int gai = getaddrinfo(mod_host_host_.c_str(), port_str.c_str(), &hints, &res);
    if (gai == 0 && res != nullptr) {
        for (struct addrinfo* ai = res; ai != nullptr; ai = ai->ai_next) {
            int s = socket(ai->ai_family, ai->ai_socktype, ai->ai_protocol);
            if (s < 0) continue;

            // Log attempted address for diagnostics
            char addrbuf[INET6_ADDRSTRLEN] = {0};
            if (ai->ai_family == AF_INET) {
                struct sockaddr_in* sa = reinterpret_cast<struct sockaddr_in*>(ai->ai_addr);
                inet_ntop(AF_INET, &sa->sin_addr, addrbuf, sizeof(addrbuf));
            } else if (ai->ai_family == AF_INET6) {
                struct sockaddr_in6* sa6 = reinterpret_cast<struct sockaddr_in6*>(ai->ai_addr);
                inet_ntop(AF_INET6, &sa6->sin6_addr, addrbuf, sizeof(addrbuf));
            }
            spdlog::debug("FeedbackReader trying connect to %s:%s", addrbuf, port_str.c_str());

            // Set receive timeout to allow checking shutdown flag
            struct timeval timeout;
            timeout.tv_sec = 0;
            timeout.tv_usec = 100000;  // 100ms timeout
            setsockopt(s, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));

            // Enable TCP_NODELAY to avoid Nagle delays and enable keepalive
            int one = 1;
            setsockopt(s, IPPROTO_TCP, TCP_NODELAY, &one, sizeof(one));
            setsockopt(s, SOL_SOCKET, SO_KEEPALIVE, &one, sizeof(one));

            // Tuning keepalive parameters (Linux)
#if defined(TCP_KEEPIDLE)
            int keepidle = 10;   // seconds of idle before keepalive probes
            setsockopt(s, IPPROTO_TCP, TCP_KEEPIDLE, &keepidle, sizeof(keepidle));
#endif
#if defined(TCP_KEEPINTVL)
            int keepintvl = 5;   // seconds between keepalive probes
            setsockopt(s, IPPROTO_TCP, TCP_KEEPINTVL, &keepintvl, sizeof(keepintvl));
#endif
#if defined(TCP_KEEPCNT)
            int keepcnt = 3;     // number of keepalive probes
            setsockopt(s, IPPROTO_TCP, TCP_KEEPCNT, &keepcnt, sizeof(keepcnt));
#endif

            if (connect(s, ai->ai_addr, ai->ai_addrlen) == 0) {
                // Success
                tcp_socket_ = s;
                freeaddrinfo(res);
                return true;
            }

            close(s);
        }

        freeaddrinfo(res);
    }

    // Fallback: try interpreting host as literal IPv4 address
    tcp_socket_ = socket(AF_INET, SOCK_STREAM, 0);
    if (tcp_socket_ < 0) {
        return false;
    }

    // Set receive timeout to allow checking shutdown flag
    struct timeval timeout;
    timeout.tv_sec = 0;
    timeout.tv_usec = 100000;  // 100ms timeout
    setsockopt(tcp_socket_, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));

    // Enable TCP_NODELAY and keepalive on fallback socket as well
    int one = 1;
    setsockopt(tcp_socket_, IPPROTO_TCP, TCP_NODELAY, &one, sizeof(one));
    setsockopt(tcp_socket_, SOL_SOCKET, SO_KEEPALIVE, &one, sizeof(one));
#if defined(TCP_KEEPIDLE)
    int keepidle = 10;
    setsockopt(tcp_socket_, IPPROTO_TCP, TCP_KEEPIDLE, &keepidle, sizeof(keepidle));
#endif
#if defined(TCP_KEEPINTVL)
    int keepintvl = 5;
    setsockopt(tcp_socket_, IPPROTO_TCP, TCP_KEEPINTVL, &keepintvl, sizeof(keepintvl));
#endif
#if defined(TCP_KEEPCNT)
    int keepcnt = 3;
    setsockopt(tcp_socket_, IPPROTO_TCP, TCP_KEEPCNT, &keepcnt, sizeof(keepcnt));
#endif

    struct sockaddr_in server_addr;
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(mod_host_feedback_port_);

    if (inet_pton(AF_INET, mod_host_host_.c_str(), &server_addr.sin_addr) <= 0) {
        close(tcp_socket_);
        tcp_socket_ = -1;
        return false;
    }

    if (connect(tcp_socket_, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
        close(tcp_socket_);
        tcp_socket_ = -1;
        return false;
    }

    return true;
}

} // namespace modhost_bridge
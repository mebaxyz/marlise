#include "utils/types.h"
#include "feedback_reader.h"
#include "command_service.h"
#include "health_monitor.h"
#include "plugin_manager.h"
#include "../audio/audio_system_manager.h"
#include "../audio/jack_manager.h"
#include <spdlog/spdlog.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <unistd.h>
#include <fcntl.h>
#include <cstdlib>
#include <csignal>
#include <atomic>
#include <chrono>
#include <thread>

namespace {

// Default configuration constants
const std::string DEFAULT_MOD_HOST_HOST = "127.0.0.1";
const uint16_t DEFAULT_MOD_HOST_PORT = 5555;
const uint16_t DEFAULT_MOD_HOST_FEEDBACK_PORT = 5556;
const std::string DEFAULT_ZMQ_REP_ADDR = "tcp://127.0.0.1:6000";
const std::string DEFAULT_ZMQ_PUB_ADDR = "tcp://127.0.0.1:6001";
const std::string DEFAULT_ZMQ_HEALTH_ADDR = "tcp://127.0.0.1:6002";

// Connection retry constants
const std::chrono::milliseconds CONNECTION_RETRY_DELAY(1000);
const std::chrono::seconds CONNECTION_TIMEOUT(5);

// Global shutdown flag
std::atomic<bool> shutdown_requested(false);

void signal_handler(int signal) {
    spdlog::info("Received signal {}, initiating shutdown...", signal);
    shutdown_requested = true;
}

} // anonymous namespace

namespace modhost_bridge {

/**
 * Test TCP connection to mod-host with timeout
 */
bool test_connection(const std::string& host, uint16_t port) {
    struct addrinfo hints;
    struct addrinfo* res = nullptr;
    char portstr[6];
    snprintf(portstr, sizeof(portstr), "%u", port);

    memset(&hints, 0, sizeof(hints));
    // Prefer IPv4 for test connections in our integration/test environments.
    // Using AF_INET avoids IPv6/::1 vs 127.0.0.1 resolution differences that
    // caused intermittent failures in host-networked Docker tests.
    hints.ai_family = AF_INET; // IPv4 only
    hints.ai_socktype = SOCK_STREAM;

    int gai = getaddrinfo(host.c_str(), portstr, &hints, &res);
    if (gai != 0) {
        spdlog::warn("getaddrinfo failed for {}:{} -> {}", host, port, gai == EAI_SYSTEM ? std::strerror(errno) : gai == 0 ? "" : gai);
        return false;
    }

    bool ok = false;
    for (struct addrinfo* ai = res; ai != nullptr; ai = ai->ai_next) {
        int sock = socket(ai->ai_family, ai->ai_socktype, ai->ai_protocol);
        if (sock < 0) {
            continue;
        }

        // Log the address we are attempting to connect to for easier debugging
        char addrbuf[INET6_ADDRSTRLEN] = {0};
        if (ai->ai_family == AF_INET) {
            struct sockaddr_in* sa = reinterpret_cast<struct sockaddr_in*>(ai->ai_addr);
            inet_ntop(AF_INET, &sa->sin_addr, addrbuf, sizeof(addrbuf));
        } else if (ai->ai_family == AF_INET6) {
            struct sockaddr_in6* sa6 = reinterpret_cast<struct sockaddr_in6*>(ai->ai_addr);
            inet_ntop(AF_INET6, &sa6->sin6_addr, addrbuf, sizeof(addrbuf));
        }
        spdlog::debug("Attempting socket connect to %s:%u (family=%d)", addrbuf, port, ai->ai_family);

        // Set non-blocking
        int flags = fcntl(sock, F_GETFL, 0);
        fcntl(sock, F_SETFL, flags | O_NONBLOCK);

        int result = connect(sock, ai->ai_addr, ai->ai_addrlen);
        if (result < 0) {
            if (errno == EINPROGRESS) {
                // Wait with timeout
                fd_set write_fds;
                FD_ZERO(&write_fds);
                FD_SET(sock, &write_fds);

                struct timeval timeout;
                timeout.tv_sec = CONNECTION_TIMEOUT.count();
                timeout.tv_usec = 0;

                result = select(sock + 1, nullptr, &write_fds, nullptr, &timeout);
                if (result > 0) {
                    int error = 0;
                    socklen_t len = sizeof(error);
                    if (getsockopt(sock, SOL_SOCKET, SO_ERROR, &error, &len) == 0) {
                        if (error == 0) {
                            ok = true;
                        } else {
                            spdlog::warn("Connect attempt to {}:{} failed: {}", host, port, std::strerror(error));
                        }
                    }
                }
            } else {
                spdlog::warn("Immediate connect to {}:{} failed: {}", host, port, std::strerror(errno));
            }
        } else {
            // Immediate success
            ok = true;
        }

        close(sock);
        if (ok) break;
    }

    freeaddrinfo(res);
    return ok;
}

/**
 * Wait for mod-host to become available
 */
bool wait_for_modhost(const std::string& host, uint16_t command_port, uint16_t feedback_port,
                      std::shared_ptr<HealthState> health_state) {
    spdlog::info("Waiting for mod-host to become available at {}:{} (command) and {}:{} (feedback)",
                host, command_port, host, feedback_port);

    while (!shutdown_requested) {
        // Try command port first
        if (test_connection(host, command_port)) {
            spdlog::info("Successfully connected to mod-host command port {}:{}", host, command_port);
            health_state->update_command_connection(true);

            // Now try feedback port
            if (test_connection(host, feedback_port)) {
                spdlog::info("Successfully connected to mod-host feedback port {}:{}", host, feedback_port);
                health_state->update_feedback_connection(true);
                return true;
            } else {
                spdlog::warn("Cannot connect to mod-host feedback port {}:{}", host, feedback_port);
                health_state->update_feedback_connection(false);
            }
        } else {
            spdlog::warn("Cannot connect to mod-host command port {}:{}", host, command_port);
            health_state->update_command_connection(false);
            health_state->update_feedback_connection(false);
        }

        // Wait before retrying
        std::this_thread::sleep_for(CONNECTION_RETRY_DELAY);
    }

    return false;
}

} // namespace modhost_bridge

int main(int argc, char* argv[]) {
    try {
        // Initialize logging
        spdlog::set_level(spdlog::level::info);
        spdlog::set_pattern("[%Y-%m-%d %H:%M:%S] [%l] %v");

        // Set up signal handlers
        std::signal(SIGINT, signal_handler);
        std::signal(SIGTERM, signal_handler);

        spdlog::info("Main function started");

        // Read configuration from environment variables
        std::string mod_host_host = std::getenv("MOD_HOST_HOST") ?
            std::getenv("MOD_HOST_HOST") : DEFAULT_MOD_HOST_HOST;
        uint16_t mod_host_port = std::getenv("MOD_HOST_PORT") ?
            static_cast<uint16_t>(std::stoi(std::getenv("MOD_HOST_PORT"))) : DEFAULT_MOD_HOST_PORT;
        uint16_t mod_host_feedback_port = std::getenv("MOD_HOST_FEEDBACK_PORT") ?
            static_cast<uint16_t>(std::stoi(std::getenv("MOD_HOST_FEEDBACK_PORT"))) : DEFAULT_MOD_HOST_FEEDBACK_PORT;

        std::string zmq_rep_addr = std::getenv("MODHOST_BRIDGE_REP") ?
            std::getenv("MODHOST_BRIDGE_REP") : DEFAULT_ZMQ_REP_ADDR;
        std::string zmq_pub_addr = std::getenv("MODHOST_BRIDGE_PUB") ?
            std::getenv("MODHOST_BRIDGE_PUB") : DEFAULT_ZMQ_PUB_ADDR;
        std::string zmq_health_addr = std::getenv("MODHOST_BRIDGE_HEALTH") ?
            std::getenv("MODHOST_BRIDGE_HEALTH") : DEFAULT_ZMQ_HEALTH_ADDR;

        spdlog::info("Starting mod-host-bridge");
        spdlog::info("mod-host: {}:{} (command), {}:{} (feedback)",
                    mod_host_host, mod_host_port, mod_host_host, mod_host_feedback_port);
        spdlog::info("ZeroMQ: {} (REP), {} (PUB), {} (Health)",
                    zmq_rep_addr, zmq_pub_addr, zmq_health_addr);

        // Initialize health state
        auto health_state = std::make_shared<modhost_bridge::HealthState>();

        // Create ZeroMQ context
        spdlog::info("Creating ZeroMQ context");
        zmq::context_t zmq_context(1);
        spdlog::info("ZeroMQ context created");

        // Create and start health monitor early so it can respond even if mod-host is unavailable
        spdlog::info("Creating health monitor...");
        modhost_bridge::HealthMonitor health_monitor(zmq_context, zmq_health_addr, health_state);
        spdlog::info("Starting health monitor...");
        health_monitor.start();
        spdlog::info("Health monitor started successfully");

        // Wait for mod-host to become available
        if (!modhost_bridge::wait_for_modhost(mod_host_host, mod_host_port, mod_host_feedback_port, health_state)) {
            spdlog::error("Shutdown requested while waiting for mod-host");
            health_monitor.stop();
            return 1;
        }

        // Create and start services
        auto plugin_manager = std::make_shared<modhost_bridge::PluginManager>(
            zmq_context, zmq_pub_addr, mod_host_host, mod_host_port, health_state);
        auto audio_system_manager = std::make_shared<modhost_bridge::JackManager>();
        auto command_service = std::make_shared<modhost_bridge::CommandService>(
            zmq_context, zmq_rep_addr, mod_host_host, mod_host_port,
            plugin_manager, audio_system_manager, health_state);
        modhost_bridge::FeedbackReader feedback_reader(zmq_context, *plugin_manager->get_pub_socket(),
                                                      mod_host_host, mod_host_feedback_port, health_state);

        // Initialize plugin manager
        plugin_manager->initialize();

        command_service->start();
        feedback_reader.start();
        // health_monitor.start(); // Already started early

        spdlog::info("All services started successfully");

        // Wait for shutdown signal
        while (!shutdown_requested) {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }

        spdlog::info("Shutting down services...");

        // Stop services
        feedback_reader.stop();
        command_service->stop();
        health_monitor.stop();
        plugin_manager->shutdown();

        spdlog::info("Shutdown complete");
        return 0;

    } catch (const std::exception& e) {
        spdlog::error("Fatal error: {}", e.what());
        return 1;
    }
}
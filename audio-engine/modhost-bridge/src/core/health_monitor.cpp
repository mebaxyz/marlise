#include "health_monitor.h"
#include "../utils/types.h"
#include <spdlog/spdlog.h>
#include <json/json.h>
#include <chrono>
#include <thread>

namespace modhost_bridge {

HealthMonitor::HealthMonitor(zmq::context_t& zmq_context,
                             const std::string& health_endpoint,
                             std::shared_ptr<HealthState> health_state)
    : zmq_context_(zmq_context)
    , health_endpoint_(health_endpoint)
    , health_state_(health_state)
    , running_(false) {
}

HealthMonitor::~HealthMonitor() {
    stop();
}

void HealthMonitor::start() {
    if (running_) return;

    running_ = true;
    health_socket_ = std::make_unique<zmq::socket_t>(zmq_context_, ZMQ_REP);
    health_socket_->bind(health_endpoint_.c_str());
    
    // Set receive timeout to allow checking shutdown flag
    int timeout_ms = 100;  // 100ms timeout
    health_socket_->set(zmq::sockopt::rcvtimeo, timeout_ms);
    
    spdlog::info("ZMQ Health REP bound to {}", health_endpoint_);

    monitor_thread_ = std::thread(&HealthMonitor::monitor_loop, this);
}

void HealthMonitor::stop() {
    if (!running_) return;

    running_ = false;
    if (monitor_thread_.joinable()) {
        monitor_thread_.join();
    }
}

void HealthMonitor::monitor_loop() {
    while (running_) {
        try {
            zmq::message_t request;
            auto result = health_socket_->recv(request, zmq::recv_flags::none);

            if (result) {
                std::string json_str(static_cast<char*>(request.data()), request.size());

                try {
                    Json::Value json_req;
                    Json::Reader reader;
                    if (!reader.parse(json_str, json_req)) {
                        throw std::runtime_error("Invalid JSON format");
                    }

                    // Check if it's a health request
                    if (json_req.isMember("action") && json_req["action"].asString() == "health") {
                        HealthResponse response = health_state_->get_health_response();
                        Json::Value json_resp = to_json(response);
                        Json::StreamWriterBuilder writer;
                        std::string resp_str = Json::writeString(writer, json_resp);

                        zmq::message_t zmq_resp(resp_str.size());
                        memcpy(zmq_resp.data(), resp_str.c_str(), resp_str.size());
                        health_socket_->send(zmq_resp, zmq::send_flags::none);
                    } else {
                        // Invalid request
                        Json::Value error_resp;
                        error_resp["error"] = "Invalid health request format";
                        Json::StreamWriterBuilder writer;
                        std::string resp_str = Json::writeString(writer, error_resp);

                        zmq::message_t zmq_resp(resp_str.size());
                        memcpy(zmq_resp.data(), resp_str.c_str(), resp_str.size());
                        health_socket_->send(zmq_resp, zmq::send_flags::none);
                    }

                } catch (const std::exception& e) {
                    spdlog::error("Failed to parse health request: {}", e.what());

                    Json::Value error_resp;
                    error_resp["error"] = "Invalid JSON format";
                    Json::StreamWriterBuilder writer;
                    std::string resp_str = Json::writeString(writer, error_resp);

                    zmq::message_t zmq_resp(resp_str.size());
                    memcpy(zmq_resp.data(), resp_str.c_str(), resp_str.size());
                    health_socket_->send(zmq_resp, zmq::send_flags::none);
                }
            } else {
                // Timeout - continue loop to check running_ flag
                std::this_thread::sleep_for(std::chrono::milliseconds(10));
            }
        } catch (const std::exception& e) {
            spdlog::error("Health monitor error: {}", e.what());
            std::this_thread::sleep_for(std::chrono::milliseconds(500));
        }
    }
}

} // namespace modhost_bridge
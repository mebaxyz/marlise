#include "command_service.h"
#include "types.h"
#include "plugin_manager.h"
#include <spdlog/spdlog.h>
#include <json/json.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <cstring>
#include <cerrno>
#include <chrono>
#include <thread>

namespace modhost_bridge {

CommandService::CommandService(zmq::context_t& zmq_context,
                               const std::string& rep_endpoint,
                               const std::string& mod_host_host,
                               uint16_t mod_host_port,
                               std::shared_ptr<PluginManager> plugin_manager,
                               std::shared_ptr<AudioSystemManager> audio_system_manager,
                               std::shared_ptr<HealthState> health_state)
    : zmq_context_(zmq_context)
    , rep_endpoint_(rep_endpoint)
    , mod_host_host_(mod_host_host)
    , mod_host_port_(mod_host_port)
    , plugin_manager_(plugin_manager)
    , audio_system_manager_(audio_system_manager)
    , health_state_(health_state)
    , running_(false) {
}

CommandService::~CommandService() {
    stop();
}

void CommandService::start() {
    if (running_) return;

    running_ = true;
    rep_socket_ = std::make_unique<zmq::socket_t>(zmq_context_, ZMQ_REP);
    rep_socket_->bind(rep_endpoint_.c_str());
    
    // Set receive timeout to allow checking shutdown flag
    int timeout_ms = 100;  // 100ms timeout
    rep_socket_->set(zmq::sockopt::rcvtimeo, timeout_ms);
    
    spdlog::info("ZMQ REP bound to {}", rep_endpoint_);

    service_thread_ = std::thread(&CommandService::service_loop, this);
}

void CommandService::stop() {
    if (!running_) return;

    running_ = false;
    if (service_thread_.joinable()) {
        service_thread_.join();
    }
}

void CommandService::service_loop() {
    while (running_) {
        try {
            zmq::message_t request;
            auto result = rep_socket_->recv(request, zmq::recv_flags::none);

            if (result) {
                // Process the request...
                std::string json_str(static_cast<char*>(request.data()), request.size());

                try {
                    Json::Value json_req;
                    Json::Reader reader;
                    if (!reader.parse(json_str, json_req)) {
                        throw std::runtime_error("Invalid JSON format");
                    }
                    
                    Json::Value json_resp;

                    // Check if this is a plugin command
                    if (json_req.isMember("action") && json_req["action"].asString() == "plugin") {
                        json_resp = process_plugin_command(json_req);
                    } else {
                        // Legacy command processing
                        CommandRequest cmd_req;

                        // Parse command request
                        if (json_req.isMember("command")) {
                            cmd_req = RawCommand{json_req["command"].asString()};
                        } else if (json_req.isMember("name") && json_req.isMember("args")) {
                            std::vector<std::string> args;
                            const Json::Value& args_array = json_req["args"];
                            for (const auto& arg : args_array) {
                                args.push_back(arg.asString());
                            }
                            cmd_req = StructuredCommand{json_req["name"].asString(), args};
                        } else {
                            throw std::runtime_error("Invalid command format");
                        }

                        // Process command
                        Json::Value json_resp = process_command(cmd_req);
                    }

                    // Send response
                    Json::StreamWriterBuilder writer;
                    std::string resp_str = Json::writeString(writer, json_resp);

                    zmq::message_t zmq_resp(resp_str.size());
                    memcpy(zmq_resp.data(), resp_str.c_str(), resp_str.size());
                    rep_socket_->send(zmq_resp, zmq::send_flags::none);

                } catch (const std::exception& e) {
                    spdlog::error("Failed to parse command request: {}", e.what());

                    Json::Value error_resp;
                    error_resp["error"] = "Invalid request format";
                    Json::StreamWriterBuilder writer;
                    std::string resp_str = Json::writeString(writer, error_resp);

                    zmq::message_t zmq_resp(resp_str.size());
                    memcpy(zmq_resp.data(), resp_str.c_str(), resp_str.size());
                    rep_socket_->send(zmq_resp, zmq::send_flags::none);
                }
            } else {
                // Timeout or error - continue loop to check running_ flag
                std::this_thread::sleep_for(std::chrono::milliseconds(10));
            }
        } catch (const std::exception& e) {
            spdlog::error("Command service error: {}", e.what());
            std::this_thread::sleep_for(std::chrono::milliseconds(500));
        }
    }
}

Json::Value CommandService::process_command(const CommandRequest& request) {
    std::string command;

    // Extract command string
    std::visit([&command](const auto& req) {
        using T = std::decay_t<decltype(req)>;
        if constexpr (std::is_same_v<T, RawCommand>) {
            command = req.command;
        } else if constexpr (std::is_same_v<T, StructuredCommand>) {
            command = req.name;
            for (const auto& arg : req.args) {
                command += " " + arg;
            }
        }
    }, request);

    // Send to mod-host
    auto result = send_to_modhost(command);
    if (result) {
        CommandResponse response = CommandSuccess{*result, *result};
        return to_json(response);
    } else {
        CommandResponse response = CommandError{"Failed to communicate with mod-host"};
        return to_json(response);
    }
}

Json::Value CommandService::process_plugin_command(const Json::Value& request) {
    try {
        if (!request.isMember("method")) {
            throw std::runtime_error("Plugin command missing 'method' field");
        }

        std::string method = request["method"].asString();
        PluginCommand cmd;

        if (method == "load_plugin") {
            LoadPluginRequest req;
            if (request.isMember("uri")) req.uri = request["uri"].asString();
            if (request.isMember("x")) req.x = request["x"].asDouble();
            if (request.isMember("y")) req.y = request["y"].asDouble();
            if (request.isMember("parameters") && request["parameters"].isObject()) {
                const Json::Value& params = request["parameters"];
                for (const auto& key : params.getMemberNames()) {
                    req.parameters[key] = params[key].asDouble();
                }
            }
            cmd = req;
        } else if (method == "unload_plugin") {
            UnloadPluginRequest req;
            if (request.isMember("instance_id")) req.instance_id = request["instance_id"].asString();
            cmd = req;
        } else if (method == "set_parameter") {
            SetParameterRequest req;
            if (request.isMember("instance_id")) req.instance_id = request["instance_id"].asString();
            if (request.isMember("parameter")) req.parameter = request["parameter"].asString();
            if (request.isMember("value")) req.value = request["value"].asDouble();
            cmd = req;
        } else if (method == "get_parameter") {
            GetParameterRequest req;
            if (request.isMember("instance_id")) req.instance_id = request["instance_id"].asString();
            if (request.isMember("parameter")) req.parameter = request["parameter"].asString();
            cmd = req;
        } else if (method == "get_plugin_info") {
            GetPluginInfoRequest req;
            if (request.isMember("instance_id")) req.instance_id = request["instance_id"].asString();
            cmd = req;
        } else if (method == "list_instances") {
            cmd = ListInstancesRequest{};
        } else if (method == "clear_all") {
            cmd = ClearAllRequest{};
        } else if (method == "get_available_plugins") {
            cmd = GetAvailablePluginsRequest{};
        } else if (method == "search_plugins") {
            SearchPluginsRequest req;
            if (request.isMember("query")) req.query = request["query"].asString();
            if (request.isMember("criteria") && request["criteria"].isObject()) {
                const Json::Value& criteria_json = request["criteria"];
                PluginSearchCriteria criteria;

                if (criteria_json.isMember("category")) criteria.category = criteria_json["category"].asString();
                if (criteria_json.isMember("author")) criteria.author = criteria_json["author"].asString();
                if (criteria_json.isMember("min_audio_inputs")) criteria.min_audio_inputs = criteria_json["min_audio_inputs"].asInt();
                if (criteria_json.isMember("min_audio_outputs")) criteria.min_audio_outputs = criteria_json["min_audio_outputs"].asInt();
                if (criteria_json.isMember("max_audio_inputs")) criteria.max_audio_inputs = criteria_json["max_audio_inputs"].asInt();
                if (criteria_json.isMember("max_audio_outputs")) criteria.max_audio_outputs = criteria_json["max_audio_outputs"].asInt();
                if (criteria_json.isMember("requires_realtime")) criteria.requires_realtime = criteria_json["requires_realtime"].asBool();
                if (criteria_json.isMember("has_parameter")) criteria.has_parameter = criteria_json["has_parameter"].asString();
                if (criteria_json.isMember("required_features") && criteria_json["required_features"].isArray()) {
                    const Json::Value& features = criteria_json["required_features"];
                    for (const auto& feature : features) {
                        criteria.required_features.push_back(feature.asString());
                    }
                }

                req.criteria = criteria;
            }
            cmd = req;
        } else if (method == "get_plugin_presets") {
            GetPluginPresetsRequest req;
            if (request.isMember("plugin_uri")) req.plugin_uri = request["plugin_uri"].asString();
            cmd = req;
        } else if (method == "load_preset") {
            LoadPresetRequest req;
            if (request.isMember("plugin_uri")) req.plugin_uri = request["plugin_uri"].asString();
            if (request.isMember("preset_uri")) req.preset_uri = request["preset_uri"].asString();
            cmd = req;
        } else if (method == "save_preset") {
            SavePresetRequest req;
            if (request.isMember("plugin_uri")) req.plugin_uri = request["plugin_uri"].asString();
            if (request.isMember("preset") && request["preset"].isObject()) {
                const Json::Value& preset_json = request["preset"];
                PluginPreset preset;

                if (preset_json.isMember("uri")) preset.uri = preset_json["uri"].asString();
                if (preset_json.isMember("label")) preset.label = preset_json["label"].asString();
                if (preset_json.isMember("path")) preset.path = preset_json["path"].asString();

                req.preset = preset;
            }
            cmd = req;
        } else if (method == "rescan_plugins") {
            cmd = RescanPluginsRequest{};
        } else if (method == "validate_preset") {
            ValidatePresetRequest req;
            if (request.isMember("plugin_uri")) req.plugin_uri = request["plugin_uri"].asString();
            if (request.isMember("preset_uri")) req.preset_uri = request["preset_uri"].asString();
            cmd = req;
        } else if (method == "rescan_presets") {
            RescanPresetsRequest req;
            if (request.isMember("plugin_uri")) req.plugin_uri = request["plugin_uri"].asString();
            cmd = req;
        } else if (method == "get_plugin_gui") {
            GetPluginGUIRequest req;
            if (request.isMember("plugin_uri")) req.plugin_uri = request["plugin_uri"].asString();
            cmd = req;
        } else if (method == "get_plugin_gui_mini") {
            GetPluginGUIMiniRequest req;
            if (request.isMember("plugin_uri")) req.plugin_uri = request["plugin_uri"].asString();
            cmd = req;
        } else if (method == "get_plugin_essentials") {
            GetPluginEssentialsRequest req;
            if (request.isMember("plugin_uri")) req.plugin_uri = request["plugin_uri"].asString();
            cmd = req;
        } else if (method == "is_bundle_loaded") {
            IsBundleLoadedRequest req;
            if (request.isMember("bundle_path")) req.bundle_path = request["bundle_path"].asString();
            cmd = req;
        } else if (method == "add_bundle") {
            AddBundleRequest req;
            if (request.isMember("bundle_path")) req.bundle_path = request["bundle_path"].asString();
            cmd = req;
        } else if (method == "remove_bundle") {
            RemoveBundleRequest req;
            if (request.isMember("bundle_path")) req.bundle_path = request["bundle_path"].asString();
            if (request.isMember("resource_path")) req.resource_path = request["resource_path"].asString();
            cmd = req;
        } else if (method == "list_bundle_plugins") {
            ListBundlePluginsRequest req;
            if (request.isMember("bundle_path")) req.bundle_path = request["bundle_path"].asString();
            cmd = req;
        } else {
            throw std::runtime_error("Unknown command method: " + method);
        }

        // Process the command
        PluginResponse response = plugin_manager_->process_command(cmd);
        return to_json(response);

    } catch (const std::exception& e) {
        Json::Value error_resp;
        error_resp["error"] = std::string("Plugin command failed: ") + e.what();
        return error_resp;
    }
}

std::optional<std::string> CommandService::send_to_modhost(const std::string& command) {
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) {
        spdlog::error("Failed to create socket");
        return std::nullopt;
    }

    // Set receive timeout to prevent blocking during shutdown
    struct timeval timeout;
    timeout.tv_sec = 1;  // 1 second timeout
    timeout.tv_usec = 0;
    setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));

    struct sockaddr_in server_addr;
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(mod_host_port_);

    if (inet_pton(AF_INET, mod_host_host_.c_str(), &server_addr.sin_addr) <= 0) {
        spdlog::error("Invalid address: {}", mod_host_host_);
        close(sock);
        return std::nullopt;
    }

    if (connect(sock, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
        spdlog::error("Failed to connect to mod-host command port");
        health_state_->update_command_connection(false);
        close(sock);
        return std::nullopt;
    }

    health_state_->update_command_connection(true);

    // Send command with null termination
    std::string payload = command + "\0";
    if (send(sock, payload.c_str(), payload.size(), 0) < 0) {
        spdlog::error("Failed to send command to mod-host");
        close(sock);
        return std::nullopt;
    }

    // Read response
    char buffer[4096];
    ssize_t bytes_read = recv(sock, buffer, sizeof(buffer) - 1, 0);
    close(sock);

    if (bytes_read > 0) {
        buffer[bytes_read] = '\0';
        std::string response(buffer);

        // Remove trailing null
        if (!response.empty() && response.back() == '\0') {
            response.pop_back();
        }

        return response;
    } else if (bytes_read == 0) {
        // Connection closed
        return std::nullopt;
    } else {
        // Timeout or error
        if (errno == EWOULDBLOCK || errno == EAGAIN) {
            spdlog::warn("Timeout waiting for mod-host response");
        } else {
            spdlog::error("Error reading from mod-host: {}", strerror(errno));
        }
        return std::nullopt;
    }
}

} // namespace modhost_bridge
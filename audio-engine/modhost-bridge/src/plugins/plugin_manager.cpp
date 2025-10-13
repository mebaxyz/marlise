#include "plugin_manager.h"
#include "../utils/types.h"
#include <spdlog/spdlog.h>
#include <json/json.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <unistd.h>
#include <cstring>
#include <cerrno>
#include <random>
#include <sstream>
#include <iomanip>

namespace modhost_bridge {

PluginManager::PluginManager(zmq::context_t& zmq_context,
                             const std::string& pub_endpoint,
                             const std::string& mod_host_host,
                             uint16_t mod_host_port,
                             std::shared_ptr<HealthState> health_state)
    : zmq_context_(zmq_context)
    , pub_endpoint_(pub_endpoint)
    , mod_host_host_(mod_host_host)
    , mod_host_port_(mod_host_port)
    , health_state_(health_state) {
}

PluginManager::~PluginManager() {
    shutdown();
}

void PluginManager::initialize() {
    if (initialized_) return;

    // Initialize ZeroMQ PUB socket for events
    pub_socket_ = std::make_unique<zmq::socket_t>(zmq_context_, ZMQ_PUB);
    pub_socket_->bind(pub_endpoint_.c_str());
    spdlog::info("Plugin manager PUB socket bound to {}", pub_endpoint_);

    // Initialize plugin scanner
    plugin_scanner_ = std::make_unique<PluginScanner>();
    plugin_scanner_->initialize();

    // Initialize plugin validator
    plugin_validator_ = std::make_unique<PluginValidator>();

    // Initialize plugin search engine
    search_engine_ = std::make_unique<PluginSearchEngine>();

    // Initialize bundle monitor
    bundle_monitor_ = std::make_unique<PluginBundleMonitor>([this]() {
        this->rescan_plugins();
    });

    // Load available plugins
    load_available_plugins();

    initialized_ = true;
    spdlog::info("Plugin manager initialized with {} available plugins",
                available_plugins_.size());
}

void PluginManager::shutdown() {
    if (!initialized_) return;

    spdlog::info("Shutting down plugin manager");

    // Clear all instances
    {
        std::lock_guard<std::mutex> lock(mutex_);
        for (const auto& [instance_id, _] : instances_) {
            try {
                std::string command = "remove " + instance_id;
                send_to_modhost(command);
            } catch (const std::exception& e) {
                spdlog::error("Error removing plugin {} during shutdown: {}", instance_id, e.what());
            }
        }
        instances_.clear();
    }

    // Shutdown plugin scanner
    if (plugin_scanner_) {
        plugin_scanner_->shutdown();
        plugin_scanner_.reset();
    }

    // Shutdown bundle monitor
    if (bundle_monitor_) {
        bundle_monitor_->stopMonitoring();
        bundle_monitor_.reset();
    }

    // Clean up other components
    plugin_validator_.reset();
    search_engine_.reset();

    pub_socket_.reset();
    initialized_ = false;
    spdlog::info("Plugin manager shutdown complete");
}

PluginResponse PluginManager::process_command(const PluginCommand& command) {
    std::lock_guard<std::mutex> lock(mutex_);

    return std::visit([this](const auto& cmd) -> PluginResponse {
        using T = std::decay_t<decltype(cmd)>;

        if constexpr (std::is_same_v<T, LoadPluginRequest>) {
            return this->process_load_plugin(cmd);
        } else if constexpr (std::is_same_v<T, UnloadPluginRequest>) {
            return this->process_unload_plugin(cmd);
        } else if constexpr (std::is_same_v<T, SetParameterRequest>) {
            return this->process_set_parameter(cmd);
        } else if constexpr (std::is_same_v<T, GetParameterRequest>) {
            return this->process_get_parameter(cmd);
        } else if constexpr (std::is_same_v<T, GetPluginInfoRequest>) {
            return this->process_get_plugin_info(cmd);
        } else if constexpr (std::is_same_v<T, ListInstancesRequest>) {
            return this->process_list_instances(cmd);
        } else if constexpr (std::is_same_v<T, ClearAllRequest>) {
            return this->process_clear_all(cmd);
        } else if constexpr (std::is_same_v<T, GetAvailablePluginsRequest>) {
            return this->process_get_available_plugins(cmd);
        } else if constexpr (std::is_same_v<T, SearchPluginsRequest>) {
            return this->process_search_plugins(cmd);
        } else if constexpr (std::is_same_v<T, GetPluginPresetsRequest>) {
            return this->process_get_plugin_presets(cmd);
        } else if constexpr (std::is_same_v<T, LoadPresetRequest>) {
            return this->process_load_preset(cmd);
        } else if constexpr (std::is_same_v<T, SavePresetRequest>) {
            return this->process_save_preset(cmd);
        } else if constexpr (std::is_same_v<T, RescanPluginsRequest>) {
            return this->process_rescan_plugins(cmd);
        } else if constexpr (std::is_same_v<T, ValidatePresetRequest>) {
            return this->process_validate_preset(cmd);
        } else if constexpr (std::is_same_v<T, RescanPresetsRequest>) {
            return this->process_rescan_presets(cmd);
        } else if constexpr (std::is_same_v<T, GetPluginGUIRequest>) {
            return this->process_get_plugin_gui(cmd);
        } else if constexpr (std::is_same_v<T, GetPluginGUIMiniRequest>) {
            return this->process_get_plugin_gui_mini(cmd);
        } else if constexpr (std::is_same_v<T, GetPluginEssentialsRequest>) {
            return this->process_get_plugin_essentials(cmd);
        } else if constexpr (std::is_same_v<T, IsBundleLoadedRequest>) {
            return this->process_is_bundle_loaded(cmd);
        } else if constexpr (std::is_same_v<T, AddBundleRequest>) {
            return this->process_add_bundle(cmd);
        } else if constexpr (std::is_same_v<T, RemoveBundleRequest>) {
            return this->process_remove_bundle(cmd);
        } else if constexpr (std::is_same_v<T, ListBundlePluginsRequest>) {
            return this->process_list_bundle_plugins(cmd);
        }
    }, command);
}

PluginResponse PluginManager::process_load_plugin(const LoadPluginRequest& req) {
    // Check if plugin exists
    auto plugin_it = available_plugins_.find(req.uri);
    if (plugin_it == available_plugins_.end()) {
        throw std::runtime_error("Plugin not found: " + req.uri);
    }

    const PluginInfo& plugin_info = plugin_it->second;

    // Generate instance ID for bridge tracking
    std::string instance_id = generate_instance_id();
    
    // Get numeric instance for mod-host
    int numeric_instance = get_next_numeric_instance();

    // Add to mod-host using the numeric instance
    // mod-host command: add <uri> <instance_number>
    // mod-host returns the instance number on success, or negative error code on failure
    std::string command = "add " + req.uri + " " + std::to_string(numeric_instance);
    auto result = send_to_modhost(command);
    if (!result) {
        throw std::runtime_error("Failed to add plugin to mod-host");
    }

    // Parse the returned instance number from mod-host response
    int returned_instance = -1;
    try {
        std::string resp = *result;
        // Remove "resp " prefix if present
        size_t pos = resp.find("resp ");
        if (pos != std::string::npos) {
            resp = resp.substr(pos + 5);
        }
        // Parse the first integer
        returned_instance = std::stoi(resp);
        
        if (returned_instance < 0) {
            throw std::runtime_error("mod-host returned error code: " + std::to_string(returned_instance));
        }
        
        spdlog::info("mod-host confirmed plugin loaded with instance {}", returned_instance);
    } catch (const std::exception& e) {
        spdlog::error("Failed to parse mod-host response '{}': {}", *result, e.what());
        throw std::runtime_error("Failed to parse mod-host response");
    }

    // Create plugin instance
    PluginInstance instance;
    instance.uri = req.uri;
    instance.instance_id = instance_id;
    instance.name = plugin_info.name;
    instance.brand = plugin_info.brand;
    instance.version = plugin_info.version;
    instance.parameters = req.parameters;
    instance.ports = plugin_info.ports;
    instance.x = req.x;
    instance.y = req.y;
    instance.enabled = true;
    instance.host_instance = returned_instance;  // Use the instance number confirmed by mod-host
    
    // Log the successful load
    spdlog::info("Loaded plugin {} with instance_id={} and host_instance={}", 
                 req.uri, instance_id, returned_instance);

    // Set initial parameters
    for (const auto& [param, value] : req.parameters) {
        std::string param_command = "param_set " + instance_id + " " + param + " " + std::to_string(value);
        send_to_modhost(param_command);
    }

    // Store instance
    instances_[instance_id] = instance;

    // Publish event
    Json::Value payload;
    payload["instance_id"] = instance_id;
    payload["uri"] = req.uri;
    payload["name"] = instance.name;
    publish_event("plugin_loaded", payload);

    spdlog::info("Loaded plugin {} as {}", req.uri, instance_id);

    return LoadPluginResponse{instance_id, instance};
}

PluginResponse PluginManager::process_unload_plugin(const UnloadPluginRequest& req) {
    // Check if instance exists
    auto instance_it = instances_.find(req.instance_id);
    if (instance_it == instances_.end()) {
        throw std::runtime_error("Plugin instance not found: " + req.instance_id);
    }

    const PluginInstance& instance = instance_it->second;

    // Remove from mod-host
    std::string command = "remove " + req.instance_id;
    auto result = send_to_modhost(command);
    if (!result) {
        spdlog::warn("Failed to remove plugin {} from mod-host", req.instance_id);
    }

    // Remove from instances
    instances_.erase(instance_it);

    // Publish event
    Json::Value payload;
    payload["instance_id"] = req.instance_id;
    payload["uri"] = instance.uri;
    publish_event("plugin_unloaded", payload);

    spdlog::info("Unloaded plugin {}", req.instance_id);

    return UnloadPluginResponse{"ok", req.instance_id};
}

PluginResponse PluginManager::process_set_parameter(const SetParameterRequest& req) {
    // Check if instance exists
    auto instance_it = instances_.find(req.instance_id);
    if (instance_it == instances_.end()) {
        throw std::runtime_error("Plugin instance not found: " + req.instance_id);
    }

    PluginInstance& instance = instance_it->second;

    // Set in mod-host
    std::string command = "param_set " + req.instance_id + " " + req.parameter + " " + std::to_string(req.value);
    auto result = send_to_modhost(command);
    if (!result) {
        throw std::runtime_error("Failed to set parameter in mod-host");
    }

    // Update local state
    instance.parameters[req.parameter] = req.value;

    // Publish event
    Json::Value payload;
    payload["instance_id"] = req.instance_id;
    payload["parameter"] = req.parameter;
    payload["value"] = req.value;
    publish_event("parameter_changed", payload);

    spdlog::debug("Set parameter {}.{} = {}", req.instance_id, req.parameter, req.value);

    return SetParameterResponse{"ok", req.value};
}

PluginResponse PluginManager::process_get_parameter(const GetParameterRequest& req) {
    // Check if instance exists
    auto instance_it = instances_.find(req.instance_id);
    if (instance_it == instances_.end()) {
        throw std::runtime_error("Plugin instance not found: " + req.instance_id);
    }

    const PluginInstance& instance = instance_it->second;

    // Try to get from mod-host first
    std::string command = "param_get " + req.instance_id + " " + req.parameter;
    auto result = send_to_modhost(command);

    double value = 0.0;
    if (result) {
        try {
            value = std::stod(*result);
        } catch (const std::exception&) {
            // Fallback to stored value
            auto param_it = instance.parameters.find(req.parameter);
            if (param_it != instance.parameters.end()) {
                value = param_it->second;
            }
        }
    } else {
        // Fallback to stored value
        auto param_it = instance.parameters.find(req.parameter);
        if (param_it != instance.parameters.end()) {
            value = param_it->second;
        }
    }

    return GetParameterResponse{req.parameter, value};
}

PluginResponse PluginManager::process_get_plugin_info(const GetPluginInfoRequest& req) {
    // Check if instance exists
    auto instance_it = instances_.find(req.instance_id);
    if (instance_it == instances_.end()) {
        throw std::runtime_error("Plugin instance not found: " + req.instance_id);
    }

    return GetPluginInfoResponse{instance_it->second};
}

PluginResponse PluginManager::process_list_instances(const ListInstancesRequest&) {
    return ListInstancesResponse{instances_};
}

PluginResponse PluginManager::process_clear_all(const ClearAllRequest&) {
    std::vector<std::string> instance_ids;
    for (const auto& [id, _] : instances_) {
        instance_ids.push_back(id);
    }

    for (const std::string& instance_id : instance_ids) {
        try {
            UnloadPluginRequest req{instance_id};
            process_unload_plugin(req);
        } catch (const std::exception& e) {
            spdlog::error("Error unloading plugin {} during clear_all: {}", instance_id, e.what());
        }
    }

    spdlog::info("Cleared all plugin instances");

    return ClearAllResponse{"ok"};
}

PluginResponse PluginManager::process_get_available_plugins(const GetAvailablePluginsRequest&) {
    return GetAvailablePluginsResponse{available_plugins_};
}

PluginResponse PluginManager::process_search_plugins(const SearchPluginsRequest& req) {
    if (!search_engine_) {
        throw std::runtime_error("Plugin search engine not initialized");
    }

    std::vector<PluginInfo> results;

    if (req.criteria.has_value()) {
        // Use criteria-based filtering
        results = search_engine_->filterPlugins(req.criteria.value(), available_plugins_);
    } else if (!req.query.empty()) {
        // Use text search
        results = search_engine_->searchByText(req.query, available_plugins_);
    } else {
        // Return all plugins if no criteria or query
        results.reserve(available_plugins_.size());
        for (const auto& pair : available_plugins_) {
            results.push_back(pair.second);
        }
    }

    spdlog::debug("Plugin search returned {} results", results.size());
    return SearchPluginsResponse{results};
}

PluginResponse PluginManager::process_get_plugin_presets(const GetPluginPresetsRequest& req) {
    if (!plugin_scanner_) {
        throw std::runtime_error("Plugin scanner not initialized");
    }

    // Check if plugin exists
    auto plugin_it = available_plugins_.find(req.plugin_uri);
    if (plugin_it == available_plugins_.end()) {
        throw std::runtime_error("Plugin not found: " + req.plugin_uri);
    }

    // Get presets from scanner
    std::vector<PluginPreset> presets = plugin_scanner_->get_plugin_presets(req.plugin_uri);

    spdlog::debug("Retrieved {} presets for plugin {}", presets.size(), req.plugin_uri);
    return GetPluginPresetsResponse{req.plugin_uri, presets};
}

PluginResponse PluginManager::process_load_preset(const LoadPresetRequest& req) {
    if (!plugin_scanner_) {
        throw std::runtime_error("Plugin scanner not initialized");
    }

    // Check if plugin exists
    auto plugin_it = available_plugins_.find(req.plugin_uri);
    if (plugin_it == available_plugins_.end()) {
        throw std::runtime_error("Plugin not found: " + req.plugin_uri);
    }

    // Load preset
    auto preset = plugin_scanner_->load_preset(req.plugin_uri, req.preset_uri);
    if (!preset) {
        throw std::runtime_error("Failed to load preset: " + req.preset_uri);
    }

    spdlog::info("Loaded preset {} for plugin {}", req.preset_uri, req.plugin_uri);
    return LoadPresetResponse{"ok", req.preset_uri};
}

PluginResponse PluginManager::process_save_preset(const SavePresetRequest& req) {
    if (!plugin_scanner_) {
        throw std::runtime_error("Plugin scanner not initialized");
    }

    // Check if plugin exists
    auto plugin_it = available_plugins_.find(req.plugin_uri);
    if (plugin_it == available_plugins_.end()) {
        throw std::runtime_error("Plugin not found: " + req.plugin_uri);
    }

    // Save preset
    bool success = plugin_scanner_->save_preset(req.plugin_uri, req.preset);
    if (!success) {
        throw std::runtime_error("Failed to save preset: " + req.preset.uri);
    }

    spdlog::info("Saved preset {} for plugin {}", req.preset.uri, req.plugin_uri);
    return SavePresetResponse{"ok", req.preset.uri};
}

PluginResponse PluginManager::process_rescan_plugins(const RescanPluginsRequest&) {
    int old_count = available_plugins_.size();

    rescan_plugins();

    int new_count = available_plugins_.size();
    int added = new_count - old_count;
    int removed = old_count - new_count;

    if (added > 0 || removed > 0) {
        spdlog::info("Plugin rescan: {} added, {} removed, total: {}",
                    added, removed, new_count);
    } else {
        spdlog::debug("Plugin rescan completed, no changes");
    }

    return RescanPluginsResponse{"ok", added, removed};
}

PluginResponse PluginManager::process_validate_preset(const ValidatePresetRequest& req) {
    if (!plugin_scanner_) {
        throw std::runtime_error("Plugin scanner not initialized");
    }

    // Check if plugin exists
    auto plugin_it = available_plugins_.find(req.plugin_uri);
    if (plugin_it == available_plugins_.end()) {
        throw std::runtime_error("Plugin not found: " + req.plugin_uri);
    }

    bool is_valid = plugin_scanner_->is_preset_valid(req.plugin_uri, req.preset_uri);
    spdlog::debug("Preset {} for plugin {} is {}", req.preset_uri, req.plugin_uri,
                 is_valid ? "valid" : "invalid");

    return ValidatePresetResponse{is_valid};
}

PluginResponse PluginManager::process_rescan_presets(const RescanPresetsRequest& req) {
    if (!plugin_scanner_) {
        throw std::runtime_error("Plugin scanner not initialized");
    }

    // Check if plugin exists
    auto plugin_it = available_plugins_.find(req.plugin_uri);
    if (plugin_it == available_plugins_.end()) {
        throw std::runtime_error("Plugin not found: " + req.plugin_uri);
    }

    plugin_scanner_->rescan_presets(req.plugin_uri);
    spdlog::info("Triggered preset rescan for plugin {}", req.plugin_uri);

    return RescanPresetsResponse{"ok"};
}

PluginResponse PluginManager::process_get_plugin_gui(const GetPluginGUIRequest& req) {
    if (!plugin_scanner_) {
        throw std::runtime_error("Plugin scanner not initialized");
    }

    // Check if plugin exists
    auto plugin_it = available_plugins_.find(req.plugin_uri);
    if (plugin_it == available_plugins_.end()) {
        throw std::runtime_error("Plugin not found: " + req.plugin_uri);
    }

    auto gui = plugin_scanner_->get_plugin_gui(req.plugin_uri);
    spdlog::debug("Retrieved GUI info for plugin {}", req.plugin_uri);

    return GetPluginGUIResponse{req.plugin_uri, std::move(gui)};
}

PluginResponse PluginManager::process_get_plugin_gui_mini(const GetPluginGUIMiniRequest& req) {
    if (!plugin_scanner_) {
        throw std::runtime_error("Plugin scanner not initialized");
    }

    // Check if plugin exists
    auto plugin_it = available_plugins_.find(req.plugin_uri);
    if (plugin_it == available_plugins_.end()) {
        throw std::runtime_error("Plugin not found: " + req.plugin_uri);
    }

    auto gui_mini = plugin_scanner_->get_plugin_gui_mini(req.plugin_uri);
    spdlog::debug("Retrieved mini GUI info for plugin {}", req.plugin_uri);

    return GetPluginGUIMiniResponse{req.plugin_uri, std::move(gui_mini)};
}

PluginResponse PluginManager::process_get_plugin_essentials(const GetPluginEssentialsRequest& req) {
    if (!plugin_scanner_) {
        throw std::runtime_error("Plugin scanner not initialized");
    }

    // Check if plugin exists
    auto plugin_it = available_plugins_.find(req.plugin_uri);
    if (plugin_it == available_plugins_.end()) {
        throw std::runtime_error("Plugin not found: " + req.plugin_uri);
    }

    auto essentials = plugin_scanner_->get_plugin_essentials(req.plugin_uri);
    spdlog::debug("Retrieved essentials for plugin {}", req.plugin_uri);

    return GetPluginEssentialsResponse{req.plugin_uri, std::move(essentials)};
}

PluginResponse PluginManager::process_is_bundle_loaded(const IsBundleLoadedRequest& req) {
    if (!plugin_scanner_) {
        throw std::runtime_error("Plugin scanner not initialized");
    }

    bool is_loaded = plugin_scanner_->is_bundle_loaded(req.bundle_path);
    spdlog::debug("Bundle {} is {}", req.bundle_path, is_loaded ? "loaded" : "not loaded");

    return IsBundleLoadedResponse{is_loaded};
}

PluginResponse PluginManager::process_add_bundle(const AddBundleRequest& req) {
    if (!plugin_scanner_) {
        throw std::runtime_error("Plugin scanner not initialized");
    }

    std::vector<std::string> added_plugins = plugin_scanner_->add_bundle(req.bundle_path);
    spdlog::info("Added bundle {} with {} plugins", req.bundle_path, added_plugins.size());

    return AddBundleResponse{added_plugins};
}

PluginResponse PluginManager::process_remove_bundle(const RemoveBundleRequest& req) {
    if (!plugin_scanner_) {
        throw std::runtime_error("Plugin scanner not initialized");
    }

    std::vector<std::string> removed_plugins = plugin_scanner_->remove_bundle(req.bundle_path, req.resource_path);
    spdlog::info("Removed bundle {} with {} plugins", req.bundle_path, removed_plugins.size());

    return RemoveBundleResponse{removed_plugins};
}

PluginResponse PluginManager::process_list_bundle_plugins(const ListBundlePluginsRequest& req) {
    if (!plugin_scanner_) {
        throw std::runtime_error("Plugin scanner not initialized");
    }

    std::vector<std::string> plugins = plugin_scanner_->list_plugins_in_bundle(req.bundle_path);
    spdlog::debug("Bundle {} contains {} plugins", req.bundle_path, plugins.size());

    return ListBundlePluginsResponse{plugins};
}

void PluginManager::rescan_plugins() {
    if (!plugin_scanner_) {
        spdlog::error("Plugin scanner not initialized for rescan");
        return;
    }

    spdlog::info("Rescanning plugins for changes");

    try {
        // Mini scan first to get URIs
        auto mini_plugins = plugin_scanner_->scan_plugins();

        // Get detailed info for each plugin
        std::unordered_map<std::string, PluginInfo> new_plugins;
        for (const auto& [uri, mini_plugin] : mini_plugins) {
            auto detailed_plugin = plugin_scanner_->get_plugin_info(uri);
            if (detailed_plugin) {
                new_plugins[uri] = std::move(*detailed_plugin);
            } else {
                spdlog::warn("Failed to get detailed info for plugin {} during rescan", uri);
            }
        }

        // Validate new plugins
        std::unordered_map<std::string, PluginInfo> validated_plugins;
        for (auto& [uri, plugin] : new_plugins) {
            if (plugin_validator_) {
                ValidationResult validation = plugin_validator_->validatePlugin(plugin);
                if (validation.is_valid) {
                    validated_plugins[uri] = std::move(plugin);
                } else {
                    spdlog::warn("Plugin {} failed validation: {}", uri, validation.error_message);
                }
            } else {
                validated_plugins[uri] = std::move(plugin);
            }
        }

        // Update available plugins
        available_plugins_ = std::move(validated_plugins);

        // Publish rescan event
        Json::Value payload;
        payload["plugin_count"] = static_cast<int>(available_plugins_.size());
        publish_event("plugins_rescanned", payload);

    } catch (const std::exception& e) {
        spdlog::error("Error during plugin rescan: {}", e.what());
    }
}

void PluginManager::load_available_plugins() {
    if (!plugin_scanner_) {
        throw std::runtime_error("Plugin scanner not initialized");
    }

    // Scan for available plugins using the plugin scanner (mini scan first)
    auto mini_plugins = plugin_scanner_->scan_plugins();

    // Get detailed info for each plugin to populate port information
    for (const auto& [uri, mini_plugin] : mini_plugins) {
        auto detailed_plugin = plugin_scanner_->get_plugin_info(uri);
        if (detailed_plugin) {
            // Validate the detailed plugin info
            if (plugin_validator_) {
                ValidationResult validation = plugin_validator_->validatePlugin(*detailed_plugin);
                if (validation.is_valid) {
                    available_plugins_[uri] = std::move(*detailed_plugin);
                } else {
                    spdlog::warn("Plugin {} failed validation: {}", uri, validation.error_message);
                }
            } else {
                available_plugins_[uri] = std::move(*detailed_plugin);
            }
        } else {
            spdlog::warn("Failed to get detailed info for plugin {}", uri);
        }
    }

    if (available_plugins_.empty()) {
        spdlog::warn("No valid plugins found during scan");
    }

    // Start bundle monitoring for hot-reloading
    if (bundle_monitor_) {
        // Monitor common LV2 directories
        std::vector<std::string> lv2_paths = {
            "/usr/lib/lv2",
            "/usr/local/lib/lv2",
            "~/.lv2"
        };
        bundle_monitor_->startMonitoring(lv2_paths);
        spdlog::info("Started monitoring {} LV2 directories for changes", lv2_paths.size());
    }
}

std::optional<std::string> PluginManager::send_to_modhost(const std::string& command) {
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) {
        spdlog::error("Failed to create socket for mod-host command");
        return std::nullopt;
    }

    // Set receive timeout
    struct timeval timeout;
    timeout.tv_sec = 1;
    timeout.tv_usec = 0;
    setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));

    struct sockaddr_in server_addr;
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(mod_host_port_);

    // Resolve hostname (supports 'localhost' and other names)
    struct addrinfo hints;
    struct addrinfo* res = nullptr;
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_INET;
    hints.ai_socktype = SOCK_STREAM;

    int gai = getaddrinfo(mod_host_host_.c_str(), nullptr, &hints, &res);
    if (gai == 0 && res) {
        struct sockaddr_in* addr_in = (struct sockaddr_in*)res->ai_addr;
        server_addr.sin_addr = addr_in->sin_addr;
        freeaddrinfo(res);
    } else {
        // Fallback: try inet_pton for literal IPs
        if (inet_pton(AF_INET, mod_host_host_.c_str(), &server_addr.sin_addr) <= 0) {
            spdlog::error("Invalid mod-host address: {}", mod_host_host_);
            close(sock);
            return std::nullopt;
        }
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
        return std::nullopt;
    } else {
        if (errno == EWOULDBLOCK || errno == EAGAIN) {
            spdlog::warn("Timeout waiting for mod-host response");
        } else {
            spdlog::error("Error reading from mod-host: {}", strerror(errno));
        }
        return std::nullopt;
    }
}

void PluginManager::publish_event(const std::string& event_type, const Json::Value& payload) {
    if (!pub_socket_) return;

    try {
        Json::Value event;
        event["type"] = event_type;
        event["timestamp"] = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::system_clock::now().time_since_epoch()).count();
        event["data"] = payload;

        Json::StreamWriterBuilder writer;
        std::string message = Json::writeString(writer, event);

        zmq::message_t zmq_msg(message.size());
        memcpy(zmq_msg.data(), message.c_str(), message.size());
        pub_socket_->send(zmq_msg, zmq::send_flags::none);
    } catch (const std::exception& e) {
        spdlog::error("Failed to publish event {}: {}", event_type, e.what());
    }
}

std::string PluginManager::generate_instance_id() {
    static std::random_device rd;
    static std::mt19937 gen(rd());
    static std::uniform_int_distribution<> dis(0, 15);
    static std::uniform_int_distribution<> dis2(0, 255);

    std::stringstream ss;
    ss << "plugin_" << instances_.size() << "_" << std::hex;

    for (int i = 0; i < 8; i++) {
        ss << dis(gen);
    }

    return ss.str();
}

int PluginManager::get_next_numeric_instance() {
    // Find the next available numeric instance slot for mod-host
    // mod-host expects an integer instance ID
    static int next_instance = 0;
    return next_instance++;
}

} // namespace modhost_bridge
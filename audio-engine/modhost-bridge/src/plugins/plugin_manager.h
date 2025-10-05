#pragma once

#include "../utils/types.h"
#include "plugin_scanner.h"
#include "plugin_bundle_monitor.h"
#include "plugin_validator.h"
#include "plugin_search_engine.h"
#include <zmq.hpp>
#include <memory>
#include <thread>
#include <atomic>
#include <unordered_map>
#include <mutex>

namespace modhost_bridge {

/**
 * Plugin Manager for managing LV2 plugin instances in mod-host.
 *
 * This class provides high-level plugin management functionality including:
 * - Loading/unloading plugin instances
 * - Setting/getting plugin parameters
 * - Managing plugin state and metadata
 * - Publishing events via ZeroMQ PUB socket
 */
class PluginManager {
public:
    /**
     * Constructor
     *
     * @param zmq_context ZeroMQ context
     * @param pub_endpoint ZeroMQ PUB socket endpoint for events
     * @param mod_host_host mod-host hostname/IP
     * @param mod_host_port mod-host command port
     * @param health_state Shared health state
     */
    PluginManager(zmq::context_t& zmq_context,
                  const std::string& pub_endpoint,
                  const std::string& mod_host_host,
                  uint16_t mod_host_port,
                  std::shared_ptr<HealthState> health_state);

    /**
     * Destructor - stops the manager and cleans up resources
     */
    ~PluginManager();

    /**
     * Initialize the plugin manager
     */
    void initialize();

    /**
     * Shutdown the plugin manager
     */
    void shutdown();

    /**
     * Process a plugin command
     */
    PluginResponse process_command(const PluginCommand& command);

    /**
     * Rescan plugins for changes
     */
    void rescan_plugins();

    /**
     * Get the PUB socket (for sharing with other components)
     */
    zmq::socket_t* get_pub_socket() { return pub_socket_.get(); }

private:
    /**
     * Load available plugins (hardcoded for MVP)
     */
    void load_available_plugins();

    /**
     * Send command to mod-host and get response
     */
    std::optional<std::string> send_to_modhost(const std::string& command);

    /**
     * Publish an event via ZeroMQ PUB socket
     */
    void publish_event(const std::string& event_type, const Json::Value& payload);

    /**
     * Generate a unique instance ID
     */
    std::string generate_instance_id();

    // Command processing methods
    PluginResponse process_load_plugin(const LoadPluginRequest& req);
    PluginResponse process_unload_plugin(const UnloadPluginRequest& req);
    PluginResponse process_set_parameter(const SetParameterRequest& req);
    PluginResponse process_get_parameter(const GetParameterRequest& req);
    PluginResponse process_get_plugin_info(const GetPluginInfoRequest& req);
    PluginResponse process_list_instances(const ListInstancesRequest& req);
    PluginResponse process_clear_all(const ClearAllRequest& req);
    PluginResponse process_get_available_plugins(const GetAvailablePluginsRequest& req);
    PluginResponse process_search_plugins(const SearchPluginsRequest& req);
    PluginResponse process_get_plugin_presets(const GetPluginPresetsRequest& req);
    PluginResponse process_load_preset(const LoadPresetRequest& req);
    PluginResponse process_save_preset(const SavePresetRequest& req);
    PluginResponse process_rescan_plugins(const RescanPluginsRequest& req);
    PluginResponse process_validate_preset(const ValidatePresetRequest& req);
    PluginResponse process_rescan_presets(const RescanPresetsRequest& req);
    PluginResponse process_get_plugin_gui(const GetPluginGUIRequest& req);
    PluginResponse process_get_plugin_gui_mini(const GetPluginGUIMiniRequest& req);
    PluginResponse process_get_plugin_essentials(const GetPluginEssentialsRequest& req);
    PluginResponse process_is_bundle_loaded(const IsBundleLoadedRequest& req);
    PluginResponse process_add_bundle(const AddBundleRequest& req);
    PluginResponse process_remove_bundle(const RemoveBundleRequest& req);
    PluginResponse process_list_bundle_plugins(const ListBundlePluginsRequest& req);

    zmq::context_t& zmq_context_;
    std::string pub_endpoint_;
    std::string mod_host_host_;
    uint16_t mod_host_port_;
    std::shared_ptr<HealthState> health_state_;

    std::unique_ptr<zmq::socket_t> pub_socket_;
    std::unique_ptr<PluginScanner> plugin_scanner_;
    std::unique_ptr<PluginBundleMonitor> bundle_monitor_;
    std::unique_ptr<PluginValidator> plugin_validator_;
    std::unique_ptr<PluginSearchEngine> search_engine_;
    std::unordered_map<std::string, PluginInfo> available_plugins_;
    std::unordered_map<std::string, PluginInstance> instances_;
    std::mutex mutex_;
    bool initialized_ = false;
};

} // namespace modhost_bridge
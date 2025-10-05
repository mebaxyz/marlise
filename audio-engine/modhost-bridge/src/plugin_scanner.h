#pragma once

#include "types.h"
#include <string>
#include <unordered_map>
#include <vector>
#include <memory>

extern "C" {
#include "utils.h"
}

namespace modhost_bridge {

/**
 * Plugin Scanner for discovering LV2 plugins using MOD utils library.
 *
 * This class provides dynamic plugin discovery functionality by wrapping
 * the MOD utils C API which uses Lilv for LV2 plugin scanning.
 */
class PluginScanner {
public:
    /**
     * Constructor
     */
    PluginScanner();

    /**
     * Destructor
     */
    ~PluginScanner();

    /**
     * Initialize the plugin scanner
     */
    void initialize();

    /**
     * Shutdown the plugin scanner
     */
    void shutdown();

    /**
     * Scan for available plugins
     *
     * @return Map of plugin URI to PluginInfo
     */
    std::unordered_map<std::string, PluginInfo> scan_plugins();

    /**
     * Get detailed information for a specific plugin
     *
     * @param uri Plugin URI
     * @return PluginInfo or nullptr if not found
     */
    std::unique_ptr<PluginInfo> get_plugin_info(const std::string& uri);

    /**
     * Get presets for a specific plugin
     *
     * @param plugin_uri Plugin URI
     * @return Vector of PluginPreset (currently returns empty vector)
     */
    std::vector<PluginPreset> get_plugin_presets(const std::string& plugin_uri);

    /**
     * Load a preset for a plugin
     *
     * @param plugin_uri Plugin URI
     * @param preset_uri Preset URI
     * @return PluginPreset or nullptr if not found (currently always returns nullptr)
     */
    std::unique_ptr<PluginPreset> load_preset(const std::string& plugin_uri,
                                            const std::string& preset_uri);

    /**
     * Save a preset for a plugin
     *
     * @param plugin_uri Plugin URI
     * @param preset Preset to save
     * @return true if successful (currently always returns false)
     */
    bool save_preset(const std::string& plugin_uri, const PluginPreset& preset);

    /**
     * Check if a plugin preset is valid
     *
     * @param plugin_uri Plugin URI
     * @param preset_uri Preset URI
     * @return true if preset exists and is valid
     */
    bool is_preset_valid(const std::string& plugin_uri, const std::string& preset_uri);

    /**
     * Trigger a preset rescan for a plugin
     *
     * @param plugin_uri Plugin URI
     */
    void rescan_presets(const std::string& plugin_uri);

    /**
     * Get plugin GUI information
     *
     * @param plugin_uri Plugin URI
     * @return PluginGUI or nullptr if not found
     */
    std::unique_ptr<PluginGUI> get_plugin_gui(const std::string& plugin_uri);

    /**
     * Get plugin GUI information (mini version)
     *
     * @param plugin_uri Plugin URI
     * @return PluginGUI_Mini or nullptr if not found
     */
    std::unique_ptr<PluginGUI_Mini> get_plugin_gui_mini(const std::string& plugin_uri);

    /**
     * Get plugin essentials information
     *
     * @param plugin_uri Plugin URI
     * @return PluginInfo_Essentials or nullptr if not found
     */
    std::unique_ptr<PluginInfo_Essentials> get_plugin_essentials(const std::string& plugin_uri);

    /**
     * Check if a bundle is loaded
     *
     * @param bundle_path Bundle path
     * @return true if bundle is loaded
     */
    bool is_bundle_loaded(const std::string& bundle_path);

    /**
     * Add a bundle to the Lilv world
     *
     * @param bundle_path Bundle path
     * @return List of added plugin URIs
     */
    std::vector<std::string> add_bundle(const std::string& bundle_path);

    /**
     * Remove a bundle from the Lilv world
     *
     * @param bundle_path Bundle path
     * @param resource_path Resource path
     * @return List of removed plugin URIs
     */
    std::vector<std::string> remove_bundle(const std::string& bundle_path, const std::string& resource_path);

    /**
     * List plugins in a bundle
     *
     * @param bundle_path Bundle path
     * @return List of plugin URIs in the bundle
     */
    std::vector<std::string> list_plugins_in_bundle(const std::string& bundle_path);

    // JACK utilities functions
    /**
     * Convert MOD utils PluginInfo_Mini to our PluginInfo
     */
    PluginInfo convert_plugin_info_mini(const PluginInfo_Mini* mini_info);

    /**
     * Convert MOD utils PluginInfo to our PluginInfo
     */
    PluginInfo convert_plugin_info(const ::PluginInfo* mod_info);

    /**
     * Convert MOD utils PluginPorts to our PluginPorts
     */
    PluginPorts convert_plugin_ports(const ::PluginPorts* mod_ports);

    /**
     * Convert MOD utils PluginPort to our PluginPort
     */
    PluginPort convert_plugin_port(const ::PluginPort* mod_port);

    bool initialized_;
};

} // namespace modhost_bridge
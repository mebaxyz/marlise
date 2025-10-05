#include "plugin_scanner.h"
#include <spdlog/spdlog.h>
#include <cstring>
#include <algorithm>

namespace modhost_bridge {

PluginScanner::PluginScanner() : initialized_(false) {
}

PluginScanner::~PluginScanner() {
    shutdown();
}

void PluginScanner::initialize() {
    if (initialized_) return;

    spdlog::info("Initializing plugin scanner");

    // Initialize MOD utils library
    init();

    initialized_ = true;
    spdlog::info("Plugin scanner initialized");
}

void PluginScanner::shutdown() {
    if (!initialized_) return;

    spdlog::info("Shutting down plugin scanner");

    // Cleanup MOD utils library
    cleanup();

    initialized_ = false;
    spdlog::info("Plugin scanner shutdown complete");
}

std::unordered_map<std::string, PluginInfo> PluginScanner::scan_plugins() {
    if (!initialized_) {
        throw std::runtime_error("Plugin scanner not initialized");
    }

    spdlog::info("Scanning for available plugins");

    std::unordered_map<std::string, PluginInfo> plugins;

    // Get all plugins from MOD utils
    const PluginInfo_Mini* const* mini_plugins = get_all_plugins();

    if (mini_plugins == nullptr) {
        spdlog::warn("No plugins found during scan");
        return plugins;
    }

    // Convert each plugin
    for (int i = 0; mini_plugins[i] != nullptr; ++i) {
        const PluginInfo_Mini* mini_info = mini_plugins[i];

        if (mini_info->uri == nullptr) continue;

        try {
            PluginInfo plugin_info = convert_plugin_info_mini(mini_info);
            plugins[mini_info->uri] = std::move(plugin_info);
        } catch (const std::exception& e) {
            spdlog::error("Error converting plugin {}: {}", mini_info->uri, e.what());
        }
    }

    spdlog::info("Found {} plugins", plugins.size());
    return plugins;
}

std::unique_ptr<PluginInfo> PluginScanner::get_plugin_info(const std::string& uri) {
    if (!initialized_) {
        throw std::runtime_error("Plugin scanner not initialized");
    }

    // Get detailed plugin info from MOD utils
    const ::PluginInfo* mod_info = ::get_plugin_info(uri.c_str());

    if (mod_info == nullptr) {
        return nullptr;
    }

    try {
        PluginInfo plugin_info = convert_plugin_info(mod_info);
        return std::make_unique<PluginInfo>(std::move(plugin_info));
    } catch (const std::exception& e) {
        spdlog::error("Error converting detailed plugin info for {}: {}", uri, e.what());
        return nullptr;
    }
}

PluginInfo PluginScanner::convert_plugin_info_mini(const PluginInfo_Mini* mini_info) {
    PluginInfo info;

    info.uri = mini_info->uri ? mini_info->uri : "";
    info.name = mini_info->name ? mini_info->name : "";
    info.brand = mini_info->brand ? mini_info->brand : "";
    info.label = mini_info->label ? mini_info->label : "";
    info.comment = mini_info->comment ? mini_info->comment : "";
    info.build_environment = mini_info->buildEnvironment ? mini_info->buildEnvironment : "";
    info.version = std::to_string(mini_info->minorVersion) + "." + std::to_string(mini_info->microVersion);

    // Convert category array to vector
    if (mini_info->category != nullptr) {
        for (int i = 0; mini_info->category[i] != nullptr; ++i) {
            info.category.push_back(mini_info->category[i]);
        }
    }

    // Set basic port info (will be filled in detailed scan)
    info.ports = {};

    return info;
}

PluginInfo PluginScanner::convert_plugin_info(const ::PluginInfo* mod_info) {
    PluginInfo info;

    info.uri = mod_info->uri ? mod_info->uri : "";
    info.name = mod_info->name ? mod_info->name : "";
    info.brand = mod_info->brand ? mod_info->brand : "";
    info.label = mod_info->label ? mod_info->label : "";
    info.comment = mod_info->comment ? mod_info->comment : "";
    info.build_environment = mod_info->buildEnvironment ? mod_info->buildEnvironment : "";
    info.version = mod_info->version ? mod_info->version : "";
    info.license = mod_info->license ? mod_info->license : "";

    // Convert category array to vector
    if (mod_info->category != nullptr) {
        for (int i = 0; mod_info->category[i] != nullptr; ++i) {
            info.category.push_back(mod_info->category[i]);
        }
    }

    // Convert ports
    info.ports = convert_plugin_ports(&mod_info->ports);

    // Convert author info
    if (mod_info->author.name) {
        info.author.name = mod_info->author.name;
    }
    if (mod_info->author.homepage) {
        info.author.homepage = mod_info->author.homepage;
    }
    if (mod_info->author.email) {
        info.author.email = mod_info->author.email;
    }

    return info;
}

PluginPorts PluginScanner::convert_plugin_ports(const ::PluginPorts* mod_ports) {
    PluginPorts ports;

    // Convert audio ports
    if (mod_ports->audio.input != nullptr) {
        for (int i = 0; mod_ports->audio.input[i].valid; ++i) {
            ports.audio_inputs.push_back(convert_plugin_port(&mod_ports->audio.input[i]));
        }
    }

    if (mod_ports->audio.output != nullptr) {
        for (int i = 0; mod_ports->audio.output[i].valid; ++i) {
            ports.audio_outputs.push_back(convert_plugin_port(&mod_ports->audio.output[i]));
        }
    }

    // Convert control ports
    if (mod_ports->control.input != nullptr) {
        for (int i = 0; mod_ports->control.input[i].valid; ++i) {
            ports.control_inputs.push_back(convert_plugin_port(&mod_ports->control.input[i]));
        }
    }

    if (mod_ports->control.output != nullptr) {
        for (int i = 0; mod_ports->control.output[i].valid; ++i) {
            ports.control_outputs.push_back(convert_plugin_port(&mod_ports->control.output[i]));
        }
    }

    // Convert CV ports
    if (mod_ports->cv.input != nullptr) {
        for (int i = 0; mod_ports->cv.input[i].valid; ++i) {
            ports.cv_inputs.push_back(convert_plugin_port(&mod_ports->cv.input[i]));
        }
    }

    if (mod_ports->cv.output != nullptr) {
        for (int i = 0; mod_ports->cv.output[i].valid; ++i) {
            ports.cv_outputs.push_back(convert_plugin_port(&mod_ports->cv.output[i]));
        }
    }

    // Convert MIDI ports
    if (mod_ports->midi.input != nullptr) {
        for (int i = 0; mod_ports->midi.input[i].valid; ++i) {
            ports.midi_inputs.push_back(convert_plugin_port(&mod_ports->midi.input[i]));
        }
    }

    if (mod_ports->midi.output != nullptr) {
        for (int i = 0; mod_ports->midi.output[i].valid; ++i) {
            ports.midi_outputs.push_back(convert_plugin_port(&mod_ports->midi.output[i]));
        }
    }

    return ports;
}

PluginPort PluginScanner::convert_plugin_port(const ::PluginPort* mod_port) {
    PluginPort port;

    port.index = mod_port->index;
    port.name = mod_port->name ? mod_port->name : "";
    port.symbol = mod_port->symbol ? mod_port->symbol : "";
    port.short_name = mod_port->shortName ? mod_port->shortName : "";
    port.comment = mod_port->comment ? mod_port->comment : "";
    port.designation = mod_port->designation ? mod_port->designation : "";

    // Convert ranges
    port.min_value = mod_port->ranges.min;
    port.max_value = mod_port->ranges.max;
    port.default_value = mod_port->ranges.def;

    // Convert units
    if (mod_port->units.label) {
        port.units.label = mod_port->units.label;
    }
    if (mod_port->units.symbol) {
        port.units.symbol = mod_port->units.symbol;
    }

    // Convert properties
    if (mod_port->properties != nullptr) {
        for (int i = 0; mod_port->properties[i] != nullptr; ++i) {
            port.properties.push_back(mod_port->properties[i]);
        }
    }

    // Convert scale points
    if (mod_port->scalePoints != nullptr) {
        for (int i = 0; mod_port->scalePoints[i].valid; ++i) {
            const ::PluginPortScalePoint* mod_sp = &mod_port->scalePoints[i];
            PluginScalePoint sp;
            sp.value = mod_sp->value;
            sp.label = mod_sp->label ? mod_sp->label : "";
            port.scale_points.push_back(sp);
        }
    }

    return port;
}

std::vector<PluginPreset> PluginScanner::get_plugin_presets(const std::string& plugin_uri) {
    if (!initialized_) {
        throw std::runtime_error("Plugin scanner not initialized");
    }

    // Get detailed plugin info to access presets
    auto plugin_info = get_plugin_info(plugin_uri);
    if (!plugin_info) {
        spdlog::warn("Plugin {} not found when getting presets", plugin_uri);
        return {};
    }

    // Return presets from the detailed plugin info
    return plugin_info->presets;
}

std::unique_ptr<PluginPreset> PluginScanner::load_preset(const std::string& plugin_uri,
                                                       const std::string& preset_uri) {
    if (!initialized_) {
        throw std::runtime_error("Plugin scanner not initialized");
    }

    // TODO: Implement preset loading using LV2 state extension
    // For now, return nullptr
    spdlog::warn("Preset loading not yet implemented for preset {} of plugin {}", preset_uri, plugin_uri);
    return nullptr;
}

bool PluginScanner::save_preset(const std::string& plugin_uri, const PluginPreset& preset) {
    if (!initialized_) {
        throw std::runtime_error("Plugin scanner not initialized");
    }

    // TODO: Implement preset saving using LV2 state extension
    // For now, return false
    spdlog::warn("Preset saving not yet implemented for preset {} of plugin {}", preset.uri, plugin_uri);
    return false;
}

bool PluginScanner::is_preset_valid(const std::string& plugin_uri, const std::string& preset_uri) {
    if (!initialized_) {
        throw std::runtime_error("Plugin scanner not initialized");
    }

    return ::is_plugin_preset_valid(plugin_uri.c_str(), preset_uri.c_str());
}

void PluginScanner::rescan_presets(const std::string& plugin_uri) {
    if (!initialized_) {
        throw std::runtime_error("Plugin scanner not initialized");
    }

    ::rescan_plugin_presets(plugin_uri.c_str());
    spdlog::debug("Triggered preset rescan for plugin {}", plugin_uri);
}

std::unique_ptr<PluginGUI> PluginScanner::get_plugin_gui(const std::string& plugin_uri) {
    if (!initialized_) {
        throw std::runtime_error("Plugin scanner not initialized");
    }

    const ::PluginGUI* mod_gui = ::get_plugin_gui(plugin_uri.c_str());
    if (!mod_gui) {
        return nullptr;
    }

    auto gui = std::make_unique<PluginGUI>();
    gui->resources_directory = mod_gui->resourcesDirectory ? mod_gui->resourcesDirectory : "";
    gui->icon_template = mod_gui->iconTemplate ? mod_gui->iconTemplate : "";
    gui->settings_template = mod_gui->settingsTemplate ? mod_gui->settingsTemplate : "";
    gui->javascript = mod_gui->javascript ? mod_gui->javascript : "";
    gui->stylesheet = mod_gui->stylesheet ? mod_gui->stylesheet : "";
    gui->screenshot = mod_gui->screenshot ? mod_gui->screenshot : "";
    gui->thumbnail = mod_gui->thumbnail ? mod_gui->thumbnail : "";
    gui->discussion_url = mod_gui->discussionURL ? mod_gui->discussionURL : "";
    gui->documentation = mod_gui->documentation ? mod_gui->documentation : "";
    gui->brand = mod_gui->brand ? mod_gui->brand : "";
    gui->label = mod_gui->label ? mod_gui->label : "";
    gui->model = mod_gui->model ? mod_gui->model : "";
    gui->panel = mod_gui->panel ? mod_gui->panel : "";
    gui->color = mod_gui->color ? mod_gui->color : "";
    gui->knob = mod_gui->knob ? mod_gui->knob : "";

    // Convert GUI ports
    if (mod_gui->ports) {
        for (int i = 0; mod_gui->ports[i].valid; ++i) {
            const ::PluginGUIPort* mod_port = &mod_gui->ports[i];
            PluginGUIPort port;
            port.valid = true;
            port.index = mod_port->index;
            port.name = mod_port->name ? mod_port->name : "";
            port.symbol = mod_port->symbol ? mod_port->symbol : "";
            gui->ports.push_back(port);
        }
    }

    // Convert monitored outputs
    if (mod_gui->monitoredOutputs) {
        for (int i = 0; mod_gui->monitoredOutputs[i] != nullptr; ++i) {
            gui->monitored_outputs.push_back(mod_gui->monitoredOutputs[i]);
        }
    }

    return gui;
}

std::unique_ptr<PluginGUI_Mini> PluginScanner::get_plugin_gui_mini(const std::string& plugin_uri) {
    if (!initialized_) {
        throw std::runtime_error("Plugin scanner not initialized");
    }

    const ::PluginGUI_Mini* mod_gui_mini = ::get_plugin_gui_mini(plugin_uri.c_str());
    if (!mod_gui_mini) {
        return nullptr;
    }

    auto gui_mini = std::make_unique<PluginGUI_Mini>();
    gui_mini->resources_directory = mod_gui_mini->resourcesDirectory ? mod_gui_mini->resourcesDirectory : "";
    gui_mini->screenshot = mod_gui_mini->screenshot ? mod_gui_mini->screenshot : "";
    gui_mini->thumbnail = mod_gui_mini->thumbnail ? mod_gui_mini->thumbnail : "";

    return gui_mini;
}

std::unique_ptr<PluginInfo_Essentials> PluginScanner::get_plugin_essentials(const std::string& plugin_uri) {
    if (!initialized_) {
        throw std::runtime_error("Plugin scanner not initialized");
    }

    const ::PluginInfo_Essentials* mod_essentials = ::get_plugin_info_essentials(plugin_uri.c_str());
    if (!mod_essentials) {
        return nullptr;
    }

    auto essentials = std::make_unique<PluginInfo_Essentials>();

    // Convert control inputs
    if (mod_essentials->controlInputs) {
        for (int i = 0; mod_essentials->controlInputs[i].valid; ++i) {
            essentials->control_inputs.push_back(convert_plugin_port(&mod_essentials->controlInputs[i]));
        }
    }

    // Convert monitored outputs
    if (mod_essentials->monitoredOutputs) {
        for (int i = 0; mod_essentials->monitoredOutputs[i] != nullptr; ++i) {
            essentials->monitored_outputs.push_back(mod_essentials->monitoredOutputs[i]);
        }
    }

    // Convert parameters
    if (mod_essentials->parameters) {
        for (int i = 0; mod_essentials->parameters[i].valid; ++i) {
            const ::PluginParameter* mod_param = &mod_essentials->parameters[i];
            PluginParameter param;
            param.valid = true;
            param.readable = mod_param->readable;
            param.writable = mod_param->writable;
            param.uri = mod_param->uri ? mod_param->uri : "";
            param.label = mod_param->label ? mod_param->label : "";
            param.type = mod_param->type ? mod_param->type : "";
            param.comment = mod_param->comment ? mod_param->comment : "";
            param.short_name = mod_param->shortName ? mod_param->shortName : "";

            // Convert ranges based on type
            if (strcmp(mod_param->type, "http://lv2plug.in/ns/lv2core#ControlPort") == 0) {
                param.ranges = mod_param->ranges.f.def;
            } else if (strcmp(mod_param->type, "http://lv2plug.in/ns/ext/atom#Int") == 0) {
                param.ranges = mod_param->ranges.l.def;
            } else {
                param.ranges = std::string(mod_param->ranges.s ? mod_param->ranges.s : "");
            }

            // Convert units
            if (mod_param->units.label) {
                param.units.label = mod_param->units.label;
            }
            if (mod_param->units.symbol) {
                param.units.symbol = mod_param->units.symbol;
            }

            // Convert file types and extensions
            if (mod_param->fileTypes) {
                for (int j = 0; mod_param->fileTypes[j] != nullptr; ++j) {
                    param.file_types.push_back(mod_param->fileTypes[j]);
                }
            }
            if (mod_param->supportedExtensions) {
                for (int j = 0; mod_param->supportedExtensions[j] != nullptr; ++j) {
                    param.supported_extensions.push_back(mod_param->supportedExtensions[j]);
                }
            }

            essentials->parameters.push_back(param);
        }
    }

    essentials->build_environment = mod_essentials->buildEnvironment ? mod_essentials->buildEnvironment : "";
    essentials->micro_version = mod_essentials->microVersion;
    essentials->minor_version = mod_essentials->minorVersion;
    essentials->release = mod_essentials->release;
    essentials->builder = mod_essentials->builder;

    return essentials;
}

bool PluginScanner::is_bundle_loaded(const std::string& bundle_path) {
    if (!initialized_) {
        throw std::runtime_error("Plugin scanner not initialized");
    }

    return ::is_bundle_loaded(bundle_path.c_str());
}

std::vector<std::string> PluginScanner::add_bundle(const std::string& bundle_path) {
    if (!initialized_) {
        throw std::runtime_error("Plugin scanner not initialized");
    }

    const char* const* added_plugins = ::add_bundle_to_lilv_world(bundle_path.c_str());
    std::vector<std::string> result;

    if (added_plugins) {
        for (int i = 0; added_plugins[i] != nullptr; ++i) {
            result.push_back(added_plugins[i]);
        }
    }

    spdlog::info("Added bundle {} with {} plugins", bundle_path, result.size());
    return result;
}

std::vector<std::string> PluginScanner::remove_bundle(const std::string& bundle_path, const std::string& resource_path) {
    if (!initialized_) {
        throw std::runtime_error("Plugin scanner not initialized");
    }

    const char* const* removed_plugins = ::remove_bundle_from_lilv_world(bundle_path.c_str(), resource_path.c_str());
    std::vector<std::string> result;

    if (removed_plugins) {
        for (int i = 0; removed_plugins[i] != nullptr; ++i) {
            result.push_back(removed_plugins[i]);
        }
    }

    spdlog::info("Removed bundle {} with {} plugins", bundle_path, result.size());
    return result;
}

std::vector<std::string> PluginScanner::list_plugins_in_bundle(const std::string& bundle_path) {
    if (!initialized_) {
        throw std::runtime_error("Plugin scanner not initialized");
    }

    const char* const* plugins = ::list_plugins_in_bundle(bundle_path.c_str());
    std::vector<std::string> result;

    if (plugins) {
        for (int i = 0; plugins[i] != nullptr; ++i) {
            result.push_back(plugins[i]);
        }
    }

    return result;
}

} // namespace modhost_bridge
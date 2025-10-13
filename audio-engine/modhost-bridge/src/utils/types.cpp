#include "types.h"
#include <chrono>
#include <spdlog/spdlog.h>

namespace modhost_bridge {

// HealthState implementation
HealthState::HealthState()
    : last_health_log(std::chrono::steady_clock::now()) {}

void HealthState::update_command_connection(bool connected) {
    command_connected = connected;
    update_overall_status();
}

void HealthState::update_feedback_connection(bool connected) {
    feedback_connected = connected;
    update_overall_status();
}

void HealthState::update_overall_status() {
    HealthStatus new_status;
    if (command_connected && feedback_connected) {
        new_status = HealthStatus::Healthy;
    } else if (command_connected) {
        new_status = HealthStatus::Degraded;
    } else {
        new_status = HealthStatus::Unhealthy;
    }

    if (new_status != status) {
        spdlog::info("Health status changed: {} -> {}",
                    static_cast<int>(status), static_cast<int>(new_status));
        status = new_status;
        last_health_log = std::chrono::steady_clock::now();
    } else {
        auto now = std::chrono::steady_clock::now();
        auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(now - last_health_log);
        if (elapsed.count() >= 30) {
            spdlog::info("Health status: {} (command: {}, feedback: {})",
                        static_cast<int>(status), command_connected, feedback_connected);
            last_health_log = now;
        }
    }
}

HealthResponse HealthState::get_health_response() const {
    std::string message;
    switch (status) {
        case HealthStatus::Starting:
            message = "Service is starting up, waiting for mod-host connections";
            break;
        case HealthStatus::Healthy:
            message = "Service is healthy, all connections established";
            break;
        case HealthStatus::Degraded:
            message = "Service is degraded, command connection available but feedback connection lost";
            break;
        case HealthStatus::Unhealthy:
            message = "Service is unhealthy, cannot connect to mod-host";
            break;
    }

    return HealthResponse{status, message, command_connected, feedback_connected};
}

// JSON serialization implementations
Json::Value to_json(const HealthStatus& status) {
    switch (status) {
        case HealthStatus::Starting:
            return "starting";
        case HealthStatus::Healthy:
            return "healthy";
        case HealthStatus::Degraded:
            return "degraded";
        case HealthStatus::Unhealthy:
            return "unhealthy";
    }
    return "unknown";
}

Json::Value to_json(const HealthResponse& response) {
    Json::Value root;
    root["status"] = to_json(response.status);
    root["message"] = response.message;
    root["command_connected"] = response.command_connected;
    root["feedback_connected"] = response.feedback_connected;
    return root;
}

Json::Value to_json(const CommandResponse& response) {
    Json::Value root;
    std::visit([&root](const auto& resp) {
        using T = std::decay_t<decltype(resp)>;
        if constexpr (std::is_same_v<T, CommandSuccess>) {
            root["status"] = resp.status;
            root["raw"] = resp.raw;
        } else if constexpr (std::is_same_v<T, CommandError>) {
            root["error"] = resp.error;
        }
    }, response);
    return root;
}

Json::Value to_json(const PluginInstance& instance) {
    Json::Value root;
    root["uri"] = instance.uri;
    root["instance_id"] = instance.instance_id;
    root["name"] = instance.name;
    root["brand"] = instance.brand;
    root["version"] = instance.version;
    root["x"] = instance.x;
    root["y"] = instance.y;
    root["enabled"] = instance.enabled;
    root["preset"] = instance.preset;

    // Convert parameters
    Json::Value params(Json::objectValue);
    for (const auto& [key, value] : instance.parameters) {
        params[key] = value;
    }
    root["parameters"] = params;

    // Convert ports (simplified for now)
    Json::Value ports(Json::objectValue);
    ports["audio_inputs"] = static_cast<int>(instance.ports.audio_inputs.size());
    ports["audio_outputs"] = static_cast<int>(instance.ports.audio_outputs.size());
    ports["control_inputs"] = static_cast<int>(instance.ports.control_inputs.size());
    ports["control_outputs"] = static_cast<int>(instance.ports.control_outputs.size());
    root["ports"] = ports;

    if (instance.host_instance.has_value()) {
        root["host_instance"] = instance.host_instance.value();
    } else {
        root["host_instance"] = Json::nullValue;
    }

    // Convert timestamp
    auto time_t = std::chrono::system_clock::to_time_t(instance.created_at);
    std::tm tm = *std::gmtime(&time_t);
    char buffer[32];
    std::strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%SZ", &tm);
    root["created_at"] = buffer;

    return root;
}

Json::Value to_json(const PluginInfo& info) {
    Json::Value root;
    root["uri"] = info.uri;
    root["name"] = info.name;
    root["brand"] = info.brand;
    root["label"] = info.label;
    root["comment"] = info.comment;
    root["build_environment"] = info.build_environment;
    root["version"] = info.version;
    root["license"] = info.license;

    // Convert category array
    Json::Value category(Json::arrayValue);
    for (const auto& cat : info.category) {
        category.append(cat);
    }
    root["category"] = category;

    // Convert author
    Json::Value author;
    author["name"] = info.author.name;
    author["homepage"] = info.author.homepage;
    author["email"] = info.author.email;
    root["author"] = author;

    // Convert ports (simplified for now)
    Json::Value ports(Json::objectValue);
    ports["audio_inputs"] = static_cast<int>(info.ports.audio_inputs.size());
    ports["audio_outputs"] = static_cast<int>(info.ports.audio_outputs.size());
    ports["control_inputs"] = static_cast<int>(info.ports.control_inputs.size());
    ports["control_outputs"] = static_cast<int>(info.ports.control_outputs.size());
    ports["cv_inputs"] = static_cast<int>(info.ports.cv_inputs.size());
    ports["cv_outputs"] = static_cast<int>(info.ports.cv_outputs.size());
    ports["midi_inputs"] = static_cast<int>(info.ports.midi_inputs.size());
    ports["midi_outputs"] = static_cast<int>(info.ports.midi_outputs.size());
    root["ports"] = ports;

    return root;
}

Json::Value to_json(const PluginGUIPort& port) {
    Json::Value root;
    root["valid"] = port.valid;
    root["index"] = port.index;
    root["name"] = port.name;
    root["symbol"] = port.symbol;
    return root;
}

Json::Value to_json(const PluginParameter& param) {
    Json::Value root;
    root["valid"] = param.valid;
    root["readable"] = param.readable;
    root["writable"] = param.writable;
    root["uri"] = param.uri;
    root["label"] = param.label;
    root["type"] = param.type;
    // Handle ranges variant
    std::visit([&root](const auto& val) {
        if constexpr (std::is_same_v<std::decay_t<decltype(val)>, double>) {
            root["ranges"] = val;
        } else if constexpr (std::is_same_v<std::decay_t<decltype(val)>, int64_t>) {
            root["ranges"] = static_cast<Json::Int64>(val);
        } else if constexpr (std::is_same_v<std::decay_t<decltype(val)>, std::string>) {
            root["ranges"] = val;
        }
    }, param.ranges);
    root["units"]["label"] = param.units.label;
    root["units"]["symbol"] = param.units.symbol;
    root["comment"] = param.comment;
    root["short_name"] = param.short_name;
    
    Json::Value file_types(Json::arrayValue);
    for (const auto& ft : param.file_types) {
        file_types.append(ft);
    }
    root["file_types"] = file_types;
    
    Json::Value extensions(Json::arrayValue);
    for (const auto& ext : param.supported_extensions) {
        extensions.append(ext);
    }
    root["supported_extensions"] = extensions;
    
    return root;
}

Json::Value to_json(const PluginGUI& gui) {
    Json::Value root;
    root["resources_directory"] = gui.resources_directory;
    root["icon_template"] = gui.icon_template;
    root["settings_template"] = gui.settings_template;
    root["javascript"] = gui.javascript;
    root["stylesheet"] = gui.stylesheet;
    root["screenshot"] = gui.screenshot;
    root["thumbnail"] = gui.thumbnail;
    root["discussion_url"] = gui.discussion_url;
    root["documentation"] = gui.documentation;
    root["brand"] = gui.brand;
    root["label"] = gui.label;
    root["model"] = gui.model;
    root["panel"] = gui.panel;
    root["color"] = gui.color;
    root["knob"] = gui.knob;
    
    Json::Value ports(Json::arrayValue);
    for (const auto& port : gui.ports) {
        ports.append(to_json(port));
    }
    root["ports"] = ports;
    
    Json::Value monitored(Json::arrayValue);
    for (const auto& output : gui.monitored_outputs) {
        monitored.append(output);
    }
    root["monitored_outputs"] = monitored;
    
    return root;
}

Json::Value to_json(const PluginGUI_Mini& gui) {
    Json::Value root;
    root["resources_directory"] = gui.resources_directory;
    root["screenshot"] = gui.screenshot;
    root["thumbnail"] = gui.thumbnail;
    return root;
}

Json::Value to_json(const PluginInfo_Essentials& essentials) {
    Json::Value root;
    
    Json::Value control_inputs(Json::arrayValue);
    for (const auto& port : essentials.control_inputs) {
        Json::Value port_json;
        port_json["index"] = port.index;
        port_json["name"] = port.name;
        port_json["symbol"] = port.symbol;
        port_json["short_name"] = port.short_name;
        port_json["comment"] = port.comment;
        port_json["designation"] = port.designation;
        port_json["min_value"] = port.min_value;
        port_json["max_value"] = port.max_value;
        port_json["default_value"] = port.default_value;
        port_json["units"]["label"] = port.units.label;
        port_json["units"]["symbol"] = port.units.symbol;
        
        Json::Value properties(Json::arrayValue);
        for (const auto& prop : port.properties) {
            properties.append(prop);
        }
        port_json["properties"] = properties;
        
        Json::Value scale_points(Json::arrayValue);
        for (const auto& sp : port.scale_points) {
            Json::Value sp_json;
            sp_json["value"] = sp.value;
            sp_json["label"] = sp.label;
            scale_points.append(sp_json);
        }
        port_json["scale_points"] = scale_points;
        
        control_inputs.append(port_json);
    }
    root["control_inputs"] = control_inputs;
    
    Json::Value monitored(Json::arrayValue);
    for (const auto& output : essentials.monitored_outputs) {
        monitored.append(output);
    }
    root["monitored_outputs"] = monitored;
    
    Json::Value parameters(Json::arrayValue);
    for (const auto& param : essentials.parameters) {
        parameters.append(to_json(param));
    }
    root["parameters"] = parameters;
    
    root["build_environment"] = essentials.build_environment;
    root["micro_version"] = essentials.micro_version;
    root["minor_version"] = essentials.minor_version;
    root["release"] = essentials.release;
    root["builder"] = essentials.builder;
    
    return root;
}

Json::Value to_json(const PluginResponse& response) {
    Json::Value root;
    std::visit([&root](const auto& resp) {
        using T = std::decay_t<decltype(resp)>;
        if constexpr (std::is_same_v<T, LoadPluginResponse>) {
            root["instance_id"] = resp.instance_id;
            root["plugin"] = to_json(resp.plugin);
        } else if constexpr (std::is_same_v<T, UnloadPluginResponse>) {
            root["status"] = resp.status;
            root["instance_id"] = resp.instance_id;
        } else if constexpr (std::is_same_v<T, SetParameterResponse>) {
            root["status"] = resp.status;
            root["value"] = resp.value;
        } else if constexpr (std::is_same_v<T, GetParameterResponse>) {
            root["parameter"] = resp.parameter;
            root["value"] = resp.value;
        } else if constexpr (std::is_same_v<T, GetPluginInfoResponse>) {
            root["plugin"] = to_json(resp.plugin);
        } else if constexpr (std::is_same_v<T, ListInstancesResponse>) {
            Json::Value instances(Json::objectValue);
            for (const auto& [id, instance] : resp.instances) {
                instances[id] = to_json(instance);
            }
            root["instances"] = instances;
        } else if constexpr (std::is_same_v<T, ClearAllResponse>) {
            root["status"] = resp.status;
        } else if constexpr (std::is_same_v<T, GetAvailablePluginsResponse>) {
            Json::Value plugins(Json::objectValue);
            for (const auto& [uri, info] : resp.plugins) {
                plugins[uri] = to_json(info);
            }
            root["plugins"] = plugins;
        } else if constexpr (std::is_same_v<T, SearchPluginsResponse>) {
            Json::Value plugins(Json::arrayValue);
            for (const auto& plugin : resp.plugins) {
                plugins.append(to_json(plugin));
            }
            root["plugins"] = plugins;
        } else if constexpr (std::is_same_v<T, GetPluginPresetsResponse>) {
            root["plugin_uri"] = resp.plugin_uri;
            Json::Value presets(Json::arrayValue);
            for (const auto& preset : resp.presets) {
                Json::Value preset_json;
                preset_json["uri"] = preset.uri;
                preset_json["label"] = preset.label;
                preset_json["path"] = preset.path;
                presets.append(preset_json);
            }
            root["presets"] = presets;
        } else if constexpr (std::is_same_v<T, LoadPresetResponse>) {
            root["status"] = resp.status;
            root["preset_uri"] = resp.preset_uri;
        } else if constexpr (std::is_same_v<T, SavePresetResponse>) {
            root["status"] = resp.status;
            root["preset_uri"] = resp.preset_uri;
        } else if constexpr (std::is_same_v<T, RescanPluginsResponse>) {
            root["status"] = resp.status;
            root["plugins_added"] = resp.plugins_added;
            root["plugins_removed"] = resp.plugins_removed;
        } else if constexpr (std::is_same_v<T, ValidatePresetResponse>) {
            root["is_valid"] = resp.is_valid;
        } else if constexpr (std::is_same_v<T, RescanPresetsResponse>) {
            root["status"] = resp.status;
        } else if constexpr (std::is_same_v<T, GetPluginGUIResponse>) {
            root["plugin_uri"] = resp.plugin_uri;
            if (resp.gui) {
                root["gui"] = to_json(*resp.gui);
            } else {
                root["gui"] = Json::nullValue;
            }
        } else if constexpr (std::is_same_v<T, GetPluginGUIMiniResponse>) {
            root["plugin_uri"] = resp.plugin_uri;
            if (resp.gui_mini) {
                root["gui_mini"] = to_json(*resp.gui_mini);
            } else {
                root["gui_mini"] = Json::nullValue;
            }
        } else if constexpr (std::is_same_v<T, GetPluginEssentialsResponse>) {
            root["plugin_uri"] = resp.plugin_uri;
            if (resp.essentials) {
                root["essentials"] = to_json(*resp.essentials);
            } else {
                root["essentials"] = Json::nullValue;
            }
        } else if constexpr (std::is_same_v<T, IsBundleLoadedResponse>) {
            root["is_loaded"] = resp.is_loaded;
        } else if constexpr (std::is_same_v<T, AddBundleResponse>) {
            Json::Value plugins(Json::arrayValue);
            for (const auto& plugin : resp.added_plugins) {
                plugins.append(plugin);
            }
            root["added_plugins"] = plugins;
        } else if constexpr (std::is_same_v<T, RemoveBundleResponse>) {
            Json::Value plugins(Json::arrayValue);
            for (const auto& plugin : resp.removed_plugins) {
                plugins.append(plugin);
            }
            root["removed_plugins"] = plugins;
        } else if constexpr (std::is_same_v<T, ListBundlePluginsResponse>) {
            Json::Value plugins(Json::arrayValue);
            for (const auto& plugin : resp.plugins) {
                plugins.append(plugin);
            }
            root["plugins"] = plugins;
        }
    }, response);
    return root;
}

Json::Value to_json(const FeedbackMessage& message) {
    Json::Value root;
    std::visit([&root](const auto& msg) {
        root["type"] = msg.type;
        using T = std::decay_t<decltype(msg)>;
        if constexpr (std::is_same_v<T, ParamSet>) {
            root["effect_id"] = msg.effect_id;
            root["symbol"] = msg.symbol;
            root["value"] = msg.value;
        } else if constexpr (std::is_same_v<T, AudioMonitor>) {
            root["index"] = msg.index;
            root["value"] = msg.value;
        } else if constexpr (std::is_same_v<T, OutputSet>) {
            root["effect_id"] = msg.effect_id;
            root["symbol"] = msg.symbol;
            root["value"] = msg.value;
        } else if constexpr (std::is_same_v<T, MidiMapped>) {
            root["effect_id"] = msg.effect_id;
            root["symbol"] = msg.symbol;
            root["channel"] = msg.channel;
            root["controller"] = msg.controller;
        } else if constexpr (std::is_same_v<T, MidiControlChange>) {
            root["channel"] = msg.channel;
            root["control"] = msg.control;
            root["value"] = msg.value;
        } else if constexpr (std::is_same_v<T, MidiProgramChange>) {
            root["program"] = msg.program;
            root["channel"] = msg.channel;
        } else if constexpr (std::is_same_v<T, Transport>) {
            root["rolling"] = msg.rolling;
            root["bpb"] = msg.bpb;
            root["bpm"] = msg.bpm;
        } else if constexpr (std::is_same_v<T, PatchSet>) {
            root["instance"] = msg.instance;
            root["symbol"] = msg.symbol;
            root["value"] = msg.value;
        } else if constexpr (std::is_same_v<T, Log>) {
            root["level"] = msg.level;
            root["message"] = msg.message;
        } else if constexpr (std::is_same_v<T, CpuLoad>) {
            root["load"] = msg.load;
            root["max_load"] = msg.max_load;
            root["xruns"] = msg.xruns;
        } else if constexpr (std::is_same_v<T, DataFinish>) {
            // No additional fields
        } else if constexpr (std::is_same_v<T, CcMap>) {
            root["raw"] = msg.raw;
        } else if constexpr (std::is_same_v<T, UnknownFeedback>) {
            root["raw"] = msg.raw;
        }
    }, message);
    return root;
}

// Audio response JSON serialization
Json::Value to_json(const GetJackDataResponse& response) {
    Json::Value root;
    if (response.data) {
        root["cpu_load"] = response.data->cpu_load;
        root["xruns"] = response.data->xruns;
        root["rolling"] = response.data->rolling;
        root["bpb"] = response.data->bpb;
        root["bpm"] = response.data->bpm;
    }
    return root;
}

Json::Value to_json(const GetJackBufferSizeResponse& response) {
    Json::Value root;
    root["buffer_size"] = response.buffer_size;
    return root;
}

Json::Value to_json(const GetJackSampleRateResponse& response) {
    Json::Value root;
    root["sample_rate"] = response.sample_rate;
    return root;
}

Json::Value to_json(const HasMidiBeatClockSenderPortResponse& response) {
    Json::Value root;
    root["has_port"] = response.has_port;
    return root;
}

Json::Value to_json(const HasSerialMidiInputPortResponse& response) {
    Json::Value root;
    root["has_port"] = response.has_port;
    return root;
}

Json::Value to_json(const HasSerialMidiOutputPortResponse& response) {
    Json::Value root;
    root["has_port"] = response.has_port;
    return root;
}

Json::Value to_json(const HasMidiMergerOutputPortResponse& response) {
    Json::Value root;
    root["has_port"] = response.has_port;
    return root;
}

Json::Value to_json(const HasMidiBroadcasterInputPortResponse& response) {
    Json::Value root;
    root["has_port"] = response.has_port;
    return root;
}

Json::Value to_json(const HasDuoxSplitSpdifResponse& response) {
    Json::Value root;
    root["has_feature"] = response.has_feature;
    return root;
}

Json::Value to_json(const InitJackResponse& response) {
    Json::Value root;
    root["success"] = response.success;
    return root;
}

Json::Value to_json(const CloseJackResponse& response) {
    Json::Value root;
    root["success"] = response.success;
    return root;
}

Json::Value to_json(const SetJackBufferSizeResponse& response) {
    Json::Value root;
    root["buffer_size"] = response.buffer_size;
    return root;
}

Json::Value to_json(const GetJackPortAliasResponse& response) {
    Json::Value root;
    root["alias"] = response.alias;
    return root;
}

Json::Value to_json(const GetJackHardwarePortsResponse& response) {
    Json::Value root;
    Json::Value ports(Json::arrayValue);
    for (const auto& port : response.ports) {
        ports.append(port);
    }
    root["ports"] = ports;
    return root;
}

Json::Value to_json(const ConnectJackPortsResponse& response) {
    Json::Value root;
    root["success"] = response.success;
    return root;
}

Json::Value to_json(const ConnectJackMidiOutputPortsResponse& response) {
    Json::Value root;
    root["success"] = response.success;
    return root;
}

Json::Value to_json(const DisconnectJackPortsResponse& response) {
    Json::Value root;
    root["success"] = response.success;
    return root;
}

Json::Value to_json(const DisconnectAllJackPortsResponse& response) {
    Json::Value root;
    root["success"] = response.success;
    return root;
}

Json::Value to_json(const ResetXrunsResponse& response) {
    Json::Value root;
    root["success"] = response.success;
    return root;
}

Json::Value to_json(const AudioResponse& response) {
    Json::Value root;
    std::visit([&root](const auto& resp) {
        using T = std::decay_t<decltype(resp)>;
        if constexpr (std::is_same_v<T, GetJackDataResponse>) {
            if (resp.data) {
                root["cpu_load"] = resp.data->cpu_load;
                root["xruns"] = resp.data->xruns;
                root["rolling"] = resp.data->rolling;
                root["bpb"] = resp.data->bpb;
                root["bpm"] = resp.data->bpm;
            }
        } else if constexpr (std::is_same_v<T, GetJackBufferSizeResponse>) {
            root["buffer_size"] = resp.buffer_size;
        } else if constexpr (std::is_same_v<T, GetJackSampleRateResponse>) {
            root["sample_rate"] = resp.sample_rate;
        } else if constexpr (std::is_same_v<T, HasMidiBeatClockSenderPortResponse>) {
            root["has_port"] = resp.has_port;
        } else if constexpr (std::is_same_v<T, HasSerialMidiInputPortResponse>) {
            root["has_port"] = resp.has_port;
        } else if constexpr (std::is_same_v<T, HasSerialMidiOutputPortResponse>) {
            root["has_port"] = resp.has_port;
        } else if constexpr (std::is_same_v<T, HasMidiMergerOutputPortResponse>) {
            root["has_port"] = resp.has_port;
        } else if constexpr (std::is_same_v<T, HasMidiBroadcasterInputPortResponse>) {
            root["has_port"] = resp.has_port;
        } else if constexpr (std::is_same_v<T, HasDuoxSplitSpdifResponse>) {
            root["has_feature"] = resp.has_feature;
        } else if constexpr (std::is_same_v<T, InitJackResponse>) {
            root["success"] = resp.success;
        } else if constexpr (std::is_same_v<T, CloseJackResponse>) {
            root["success"] = resp.success;
        } else if constexpr (std::is_same_v<T, SetJackBufferSizeResponse>) {
            root["buffer_size"] = resp.buffer_size;
        } else if constexpr (std::is_same_v<T, GetJackPortAliasResponse>) {
            root["alias"] = resp.alias;
        } else if constexpr (std::is_same_v<T, GetJackHardwarePortsResponse>) {
            Json::Value ports(Json::arrayValue);
            for (const auto& port : resp.ports) {
                ports.append(port);
            }
            root["ports"] = ports;
        } else if constexpr (std::is_same_v<T, ConnectJackPortsResponse>) {
            root["success"] = resp.success;
        } else if constexpr (std::is_same_v<T, ConnectJackMidiOutputPortsResponse>) {
            root["success"] = resp.success;
        } else if constexpr (std::is_same_v<T, DisconnectJackPortsResponse>) {
            root["success"] = resp.success;
        } else if constexpr (std::is_same_v<T, DisconnectAllJackPortsResponse>) {
            root["success"] = resp.success;
        } else if constexpr (std::is_same_v<T, ResetXrunsResponse>) {
            root["success"] = resp.success;
        }
    }, response);
    return root;
}

} // namespace modhost_bridge
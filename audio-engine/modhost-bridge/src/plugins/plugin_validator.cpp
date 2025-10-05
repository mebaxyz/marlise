#include "plugin_validator.h"

#include <spdlog/spdlog.h>

#include <algorithm>

namespace modhost_bridge {

PluginValidator::PluginValidator() {
    spdlog::debug("PluginValidator initialized");
}

PluginValidator::~PluginValidator() = default;

ValidationResult PluginValidator::validatePlugin(const PluginInfo& plugin) const {
    validation_errors_.clear();

    ValidationResult result;
    result.is_valid = true;

    // Check for known incompatible plugins
    if (isKnownIncompatible(plugin.uri)) {
        result.is_valid = false;
        result.error_message = "Plugin is known to be incompatible with mod-host";
        validation_errors_.push_back(result.error_message);
        return result;
    }

    // Check LV2 features
    if (!checkLv2Features(plugin)) {
        result.is_valid = false;
        result.error_message = "Plugin has incompatible LV2 features";
    }

    // Check audio ports
    if (!checkAudioPorts(plugin)) {
        result.is_valid = false;
        result.error_message = "Plugin has invalid audio port configuration";
    }

    // Check control ports
    if (!checkControlPorts(plugin)) {
        result.is_valid = false;
        result.error_message = "Plugin has invalid control port configuration";
    }

    // Check real-time support
    if (!supportsRealTime(plugin)) {
        spdlog::warn("Plugin {} does not support real-time processing", plugin.uri);
        // This is a warning, not an error for validation
    }

    if (!result.is_valid) {
        result.error_message = "Multiple validation errors: " +
                              std::to_string(validation_errors_.size()) + " issues found";
        // Log the specific validation errors
        for (const auto& error : validation_errors_) {
            spdlog::warn("Validation error for plugin {}: {}", plugin.uri, error);
        }
    }

    return result;
}

bool PluginValidator::supportsRealTime(const PluginInfo& plugin) const {
    // Note: PluginInfo doesn't have a features field, so we can't check for hardRTCapable
    // For now, assume all plugins support real-time processing
    // This could be enhanced by checking plugin properties or extending PluginInfo
    spdlog::debug("Real-time capability check not implemented - assuming plugin {} supports RT", plugin.uri);
    return true;
}

bool PluginValidator::hasRequiredFeatures(const PluginInfo& plugin) const {
    // Basic LV2 plugin requirements
    return !plugin.uri.empty() &&
           !plugin.name.empty() &&
           !plugin.ports.audio_inputs.empty() &&
           !plugin.ports.audio_outputs.empty();
}

std::vector<std::string> PluginValidator::getValidationErrors() const {
    return validation_errors_;
}

bool PluginValidator::checkLv2Features(const PluginInfo& plugin) const {
    // Note: PluginInfo doesn't have a features field, so feature validation is not implemented
    // This could be enhanced by extending PluginInfo to include LV2 features
    spdlog::debug("LV2 feature validation not implemented for plugin {}", plugin.uri);
    return true;
}

bool PluginValidator::checkAudioPorts(const PluginInfo& plugin) const {
    bool valid = true;

    // mod-host supports up to 8 audio inputs and outputs
    const int max_audio_ports = 8;
    int audio_inputs = static_cast<int>(plugin.ports.audio_inputs.size());
    int audio_outputs = static_cast<int>(plugin.ports.audio_outputs.size());

    if (audio_inputs > max_audio_ports) {
        validation_errors_.push_back("Too many audio inputs: " +
                                   std::to_string(audio_inputs) +
                                   " (max: " + std::to_string(max_audio_ports) + ")");
        valid = false;
    }

    if (audio_outputs > max_audio_ports) {
        validation_errors_.push_back("Too many audio outputs: " +
                                   std::to_string(audio_outputs) +
                                   " (max: " + std::to_string(max_audio_ports) + ")");
        valid = false;
    }

    // Must have at least one audio input or output for processing
    if (audio_inputs == 0 && audio_outputs == 0) {
        validation_errors_.push_back("Plugin has no audio ports");
        valid = false;
    }

    return valid;
}

bool PluginValidator::checkControlPorts(const PluginInfo& plugin) const {
    bool valid = true;

    // Check control input port ranges
    for (const auto& param : plugin.ports.control_inputs) {
        if (param.min_value > param.max_value) {
            validation_errors_.push_back("Invalid parameter range for '" + param.name +
                                       "': min > max");
            valid = false;
        }

        // Check for reasonable ranges (mod-host uses float values)
        if (param.min_value < -1000000.0f || param.max_value > 1000000.0f) {
            spdlog::warn("Parameter '{}' has extreme range [{}, {}]",
                        param.name, param.min_value, param.max_value);
        }
    }

    // Check control output port ranges
    for (const auto& param : plugin.ports.control_outputs) {
        if (param.min_value > param.max_value) {
            validation_errors_.push_back("Invalid parameter range for '" + param.name +
                                       "': min > max");
            valid = false;
        }

        // Check for reasonable ranges (mod-host uses float values)
        if (param.min_value < -1000000.0f || param.max_value > 1000000.0f) {
            spdlog::warn("Parameter '{}' has extreme range [{}, {}]",
                        param.name, param.min_value, param.max_value);
        }
    }

    return valid;
}

bool PluginValidator::isKnownIncompatible(const std::string& uri) const {
    // List of known incompatible plugins
    static const std::vector<std::string> incompatible_plugins = {
        // Add URIs of known problematic plugins here
    };

    return std::find(incompatible_plugins.begin(), incompatible_plugins.end(), uri) !=
           incompatible_plugins.end();
}

}  // namespace modhost_bridge
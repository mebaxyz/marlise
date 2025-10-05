#pragma once

#include <memory>
#include <string>
#include <vector>

#include "../utils/types.h"

namespace modhost_bridge {

class PluginValidator {
public:
    PluginValidator();
    ~PluginValidator();

    // Validate a plugin for compatibility with mod-host
    ValidationResult validatePlugin(const PluginInfo& plugin) const;

    // Check if a plugin supports real-time processing
    bool supportsRealTime(const PluginInfo& plugin) const;

    // Check if a plugin has required features
    bool hasRequiredFeatures(const PluginInfo& plugin) const;

    // Get validation error messages
    std::vector<std::string> getValidationErrors() const;

private:
    // Check LV2 feature compatibility
    bool checkLv2Features(const PluginInfo& plugin) const;

    // Check audio port configuration
    bool checkAudioPorts(const PluginInfo& plugin) const;

    // Check control port ranges
    bool checkControlPorts(const PluginInfo& plugin) const;

    // Check for known incompatible plugins
    bool isKnownIncompatible(const std::string& uri) const;

    mutable std::vector<std::string> validation_errors_;
};

}  // namespace modhost_bridge
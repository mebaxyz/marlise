#pragma once

#include <filesystem>
#include <functional>
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

#include "../utils/types.h"

namespace modhost_bridge {

class PluginBundleMonitor {
public:
    explicit PluginBundleMonitor(std::function<void()> on_change_callback);
    ~PluginBundleMonitor();

    // Start monitoring the specified directories
    void startMonitoring(const std::vector<std::string>& directories);

    // Stop monitoring
    void stopMonitoring();

    // Check for changes (non-blocking)
    void checkForChanges();

    // Get the list of currently monitored directories
    std::vector<std::string> getMonitoredDirectories() const;

private:
    struct BundleState {
        std::filesystem::file_time_type last_modified;
        std::vector<std::string> plugins;  // URIs of plugins in this bundle
    };

    void scanDirectory(const std::string& directory);
    void processBundle(const std::filesystem::path& bundle_path);
    bool hasBundleChanged(const std::filesystem::path& bundle_path,
                         const BundleState& state) const;

    std::function<void()> on_change_callback_;
    std::unordered_map<std::string, BundleState> bundle_states_;
    std::vector<std::string> monitored_directories_;
    bool is_monitoring_;
};

}  // namespace modhost_bridge
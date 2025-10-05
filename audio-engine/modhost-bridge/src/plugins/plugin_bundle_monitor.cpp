#include "plugin_bundle_monitor.h"

#include <spdlog/spdlog.h>

#include <algorithm>
#include <chrono>
#include <thread>

namespace modhost_bridge {

PluginBundleMonitor::PluginBundleMonitor(std::function<void()> on_change_callback)
    : on_change_callback_(std::move(on_change_callback))
    , is_monitoring_(false) {
    spdlog::debug("PluginBundleMonitor initialized");
}

PluginBundleMonitor::~PluginBundleMonitor() {
    stopMonitoring();
}

void PluginBundleMonitor::startMonitoring(const std::vector<std::string>& directories) {
    if (is_monitoring_) {
        spdlog::warn("PluginBundleMonitor is already monitoring");
        return;
    }

    monitored_directories_ = directories;
    is_monitoring_ = true;

    spdlog::info("Starting plugin bundle monitoring for {} directories",
                 directories.size());

    // Initial scan to establish baseline
    for (const auto& dir : directories) {
        scanDirectory(dir);
    }
}

void PluginBundleMonitor::stopMonitoring() {
    if (!is_monitoring_) {
        return;
    }

    is_monitoring_ = false;
    bundle_states_.clear();
    spdlog::info("Stopped plugin bundle monitoring");
}

void PluginBundleMonitor::checkForChanges() {
    if (!is_monitoring_) {
        return;
    }

    bool has_changes = false;

    for (const auto& dir : monitored_directories_) {
        std::filesystem::path dir_path(dir);

        if (!std::filesystem::exists(dir_path)) {
            continue;
        }

        // Check for new or removed bundles
        std::vector<std::string> current_bundles;
        for (const auto& entry : std::filesystem::directory_iterator(dir_path)) {
            if (entry.is_directory()) {
                std::string bundle_path = entry.path().string();
                current_bundles.push_back(bundle_path);

                // Check if this is a new bundle or if it has changed
                auto it = bundle_states_.find(bundle_path);
                if (it == bundle_states_.end()) {
                    // New bundle
                    spdlog::info("New plugin bundle detected: {}", bundle_path);
                    processBundle(entry.path());
                    has_changes = true;
                } else if (hasBundleChanged(entry.path(), it->second)) {
                    // Bundle changed
                    spdlog::info("Plugin bundle changed: {}", bundle_path);
                    processBundle(entry.path());
                    has_changes = true;
                }
            }
        }

        // Check for removed bundles
        for (auto it = bundle_states_.begin(); it != bundle_states_.end(); ) {
            const std::string& bundle_path = it->first;
            if (bundle_path.find(dir) == 0 &&  // Bundle is in this directory
                std::find(current_bundles.begin(), current_bundles.end(), bundle_path) ==
                current_bundles.end()) {
                // Bundle was removed
                spdlog::info("Plugin bundle removed: {}", bundle_path);
                it = bundle_states_.erase(it);
                has_changes = true;
            } else {
                ++it;
            }
        }
    }

    if (has_changes && on_change_callback_) {
        on_change_callback_();
    }
}

std::vector<std::string> PluginBundleMonitor::getMonitoredDirectories() const {
    return monitored_directories_;
}

void PluginBundleMonitor::scanDirectory(const std::string& directory) {
    std::filesystem::path dir_path(directory);

    if (!std::filesystem::exists(dir_path)) {
        spdlog::warn("Plugin bundle directory does not exist: {}", directory);
        return;
    }

    spdlog::debug("Scanning plugin bundle directory: {}", directory);

    for (const auto& entry : std::filesystem::directory_iterator(dir_path)) {
        if (entry.is_directory()) {
            processBundle(entry.path());
        }
    }
}

void PluginBundleMonitor::processBundle(const std::filesystem::path& bundle_path) {
    try {
        std::string bundle_str = bundle_path.string();

        // Check if it's an LV2 bundle (has manifest.ttl)
        std::filesystem::path manifest_path = bundle_path / "manifest.ttl";
        if (!std::filesystem::exists(manifest_path)) {
            return;  // Not an LV2 bundle
        }

        auto last_modified = std::filesystem::last_write_time(manifest_path);

        BundleState state;
        state.last_modified = last_modified;
        // Note: We don't populate plugins here as that would require LV2 parsing
        // The actual plugin list will be determined during rescanning

        bundle_states_[bundle_str] = state;

        spdlog::debug("Processed plugin bundle: {}", bundle_str);
    } catch (const std::filesystem::filesystem_error& e) {
        spdlog::error("Error processing plugin bundle {}: {}", bundle_path.string(), e.what());
    }
}

bool PluginBundleMonitor::hasBundleChanged(const std::filesystem::path& bundle_path,
                                          const BundleState& state) const {
    try {
        std::filesystem::path manifest_path = bundle_path / "manifest.ttl";
        if (!std::filesystem::exists(manifest_path)) {
            return true;  // Bundle is no longer valid
        }

        auto current_modified = std::filesystem::last_write_time(manifest_path);
        return current_modified != state.last_modified;
    } catch (const std::filesystem::filesystem_error& e) {
        spdlog::error("Error checking bundle change for {}: {}", bundle_path.string(), e.what());
        return true;  // Assume changed on error
    }
}

}  // namespace modhost_bridge
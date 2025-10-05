#pragma once

#include <memory>
#include <string>
#include <vector>

#include "../utils/types.h"

namespace modhost_bridge {

class PluginSearchEngine {
public:
    PluginSearchEngine();
    ~PluginSearchEngine();

    // Search plugins by text query
    std::vector<PluginInfo> searchByText(const std::string& query,
                                       const std::unordered_map<std::string, PluginInfo>& plugins) const;

    // Filter plugins by criteria
    std::vector<PluginInfo> filterPlugins(const PluginSearchCriteria& criteria,
                                        const std::unordered_map<std::string, PluginInfo>& plugins) const;

    // Get plugins by category
    std::vector<PluginInfo> getPluginsByCategory(const std::string& category,
                                               const std::unordered_map<std::string, PluginInfo>& plugins) const;

    // Get plugins by author
    std::vector<PluginInfo> getPluginsByAuthor(const std::string& author,
                                             const std::unordered_map<std::string, PluginInfo>& plugins) const;

    // Get plugins with specific features
    std::vector<PluginInfo> getPluginsWithFeatures(const std::vector<std::string>& features,
                                                 const std::unordered_map<std::string, PluginInfo>& plugins) const;

private:
    // Helper functions for text search
    bool matchesQuery(const PluginInfo& plugin, const std::string& query) const;
    std::string toLower(const std::string& str) const;

    // Helper functions for filtering
    bool matchesCriteria(const PluginInfo& plugin, const PluginSearchCriteria& criteria) const;
    bool hasAudioPorts(const PluginInfo& plugin, int min_inputs, int min_outputs) const;
    bool hasParameter(const PluginInfo& plugin, const std::string& param_name) const;
};

}  // namespace modhost_bridge
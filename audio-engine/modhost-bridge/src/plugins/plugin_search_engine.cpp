#include "plugin_search_engine.h"

#include <spdlog/spdlog.h>

#include <algorithm>
#include <regex>

namespace modhost_bridge {

PluginSearchEngine::PluginSearchEngine() {
    spdlog::debug("PluginSearchEngine initialized");
}

PluginSearchEngine::~PluginSearchEngine() = default;

std::vector<PluginInfo> PluginSearchEngine::searchByText(
    const std::string& query,
    const std::unordered_map<std::string, PluginInfo>& plugins) const {

    std::vector<PluginInfo> results;

    if (query.empty()) {
        // Return all plugins if query is empty
        results.reserve(plugins.size());
        for (const auto& pair : plugins) {
            results.push_back(pair.second);
        }
        return results;
    }

    std::string lower_query = toLower(query);

    for (const auto& pair : plugins) {
        const PluginInfo& plugin = pair.second;
        if (matchesQuery(plugin, lower_query)) {
            results.push_back(plugin);
        }
    }

    spdlog::debug("Text search for '{}' found {} results", query, results.size());
    return results;
}

std::vector<PluginInfo> PluginSearchEngine::filterPlugins(
    const PluginSearchCriteria& criteria,
    const std::unordered_map<std::string, PluginInfo>& plugins) const {

    std::vector<PluginInfo> results;

    for (const auto& pair : plugins) {
        const PluginInfo& plugin = pair.second;
        if (matchesCriteria(plugin, criteria)) {
            results.push_back(plugin);
        }
    }

    spdlog::debug("Filter search found {} results", results.size());
    return results;
}

std::vector<PluginInfo> PluginSearchEngine::getPluginsByCategory(
    const std::string& category,
    const std::unordered_map<std::string, PluginInfo>& plugins) const {

    PluginSearchCriteria criteria;
    criteria.category = category;
    return filterPlugins(criteria, plugins);
}

std::vector<PluginInfo> PluginSearchEngine::getPluginsByAuthor(
    const std::string& author,
    const std::unordered_map<std::string, PluginInfo>& plugins) const {

    PluginSearchCriteria criteria;
    criteria.author = author;
    return filterPlugins(criteria, plugins);
}

std::vector<PluginInfo> PluginSearchEngine::getPluginsWithFeatures(
    const std::vector<std::string>& features,
    const std::unordered_map<std::string, PluginInfo>& plugins) const {

    // Note: PluginInfo doesn't have a features field, so this function returns empty results
    // Features would need to be added to PluginInfo structure if needed
    spdlog::warn("getPluginsWithFeatures called but PluginInfo doesn't have features field");
    return {};
}

bool PluginSearchEngine::matchesQuery(const PluginInfo& plugin, const std::string& query) const {
    // Search in name, author, comment, and URI
    std::string searchable_text = toLower(plugin.name + " " + plugin.author.name + " " +
                                        plugin.comment + " " + plugin.uri);

    // Simple substring search
    return searchable_text.find(query) != std::string::npos;
}

std::string PluginSearchEngine::toLower(const std::string& str) const {
    std::string result = str;
    std::transform(result.begin(), result.end(), result.begin(), ::tolower);
    return result;
}

bool PluginSearchEngine::matchesCriteria(const PluginInfo& plugin,
                                       const PluginSearchCriteria& criteria) const {
    // Check category
    if (!criteria.category.empty()) {
        bool category_match = false;
        for (const auto& cat : plugin.category) {
            if (toLower(cat).find(toLower(criteria.category)) != std::string::npos) {
                category_match = true;
                break;
            }
        }
        if (!category_match) {
            return false;
        }
    }

    // Check author
    if (!criteria.author.empty() && 
        toLower(plugin.author.name).find(toLower(criteria.author)) == std::string::npos) {
        return false;
    }

    // Check minimum audio inputs
    if (criteria.min_audio_inputs > 0 && 
        static_cast<int>(plugin.ports.audio_inputs.size()) < criteria.min_audio_inputs) {
        return false;
    }

    // Check minimum audio outputs
    if (criteria.min_audio_outputs > 0 && 
        static_cast<int>(plugin.ports.audio_outputs.size()) < criteria.min_audio_outputs) {
        return false;
    }

    // Check maximum audio inputs
    if (criteria.max_audio_inputs >= 0 && 
        static_cast<int>(plugin.ports.audio_inputs.size()) > criteria.max_audio_inputs) {
        return false;
    }

    // Check maximum audio outputs
    if (criteria.max_audio_outputs >= 0 && 
        static_cast<int>(plugin.ports.audio_outputs.size()) > criteria.max_audio_outputs) {
        return false;
    }

    // Note: Real-time capability and feature checks removed as PluginInfo doesn't have features field
    // Note: Parameter checks removed as PluginInfo doesn't have parameters field directly

    return true;
}

bool PluginSearchEngine::hasAudioPorts(const PluginInfo& plugin,
                                     int min_inputs, int min_outputs) const {
    return static_cast<int>(plugin.ports.audio_inputs.size()) >= min_inputs && 
           static_cast<int>(plugin.ports.audio_outputs.size()) >= min_outputs;
}

bool PluginSearchEngine::hasParameter(const PluginInfo& plugin,
                                    const std::string& param_name) const {
    std::string lower_param = toLower(param_name);
    
    // Check control inputs for parameter
    for (const auto& param : plugin.ports.control_inputs) {
        if (toLower(param.name).find(lower_param) != std::string::npos ||
            toLower(param.symbol).find(lower_param) != std::string::npos) {
            return true;
        }
    }
    
    // Check control outputs for parameter
    for (const auto& param : plugin.ports.control_outputs) {
        if (toLower(param.name).find(lower_param) != std::string::npos ||
            toLower(param.symbol).find(lower_param) != std::string::npos) {
            return true;
        }
    }
    
    return false;
}

}  // namespace modhost_bridge
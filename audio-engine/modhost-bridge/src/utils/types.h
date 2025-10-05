#pragma once

#include <string>
#include <vector>
#include <variant>
#include <chrono>
#include <json/json.h>
#include <unordered_map>
#include <memory>
#include <mutex>
#include <optional>

// Forward declarations
namespace modhost_bridge {

// Command request types
struct RawCommand {
    std::string command;
};

struct StructuredCommand {
    std::string name;
    std::vector<std::string> args;
};

using CommandRequest = std::variant<RawCommand, StructuredCommand>;

// Command response types
struct CommandSuccess {
    std::string status;
    std::string raw;
};

struct CommandError {
    std::string error;
};

using CommandResponse = std::variant<CommandSuccess, CommandError>;

// Health status enum
enum class HealthStatus {
    Starting,
    Healthy,
    Degraded,
    Unhealthy
};

// Health request/response
struct HealthRequest {
    std::string action; // Always "health"
};

struct HealthResponse {
    HealthStatus status;
    std::string message;
    bool command_connected;
    bool feedback_connected;
};

// Plugin manager types
struct PluginAuthor {
    std::string name;
    std::string homepage;
    std::string email;
};

struct PluginScalePoint {
    double value;
    std::string label;
};

struct PluginUnits {
    std::string label;
    std::string symbol;
};

struct PluginPort {
    uint32_t index;
    std::string name;
    std::string symbol;
    std::string short_name;
    std::string comment;
    std::string designation;
    double min_value;
    double max_value;
    double default_value;
    PluginUnits units;
    std::vector<std::string> properties;
    std::vector<PluginScalePoint> scale_points;
};

struct PluginPorts {
    std::vector<PluginPort> audio_inputs;
    std::vector<PluginPort> audio_outputs;
    std::vector<PluginPort> control_inputs;
    std::vector<PluginPort> control_outputs;
    std::vector<PluginPort> cv_inputs;
    std::vector<PluginPort> cv_outputs;
    std::vector<PluginPort> midi_inputs;
    std::vector<PluginPort> midi_outputs;
};

struct PluginPreset {
    std::string uri;
    std::string label;
    std::string path;
};

struct PluginPresetValue {
    std::string symbol;
    double value;
};

struct ValidationResult {
    bool is_valid;
    std::string error_message;
};

struct PluginSearchCriteria {
    std::string category;
    std::string author;
    int min_audio_inputs = -1;
    int min_audio_outputs = -1;
    int max_audio_inputs = -1;
    int max_audio_outputs = -1;
    bool requires_realtime = false;
    std::string has_parameter;
    std::vector<std::string> required_features;
};

struct PluginInfo {
    std::string uri;
    std::string name;
    std::string brand;
    std::string label;
    std::string comment;
    std::string build_environment;
    std::string version;
    std::string license;
    std::vector<std::string> category;
    PluginAuthor author;
    PluginPorts ports;
    std::vector<PluginPreset> presets;
};

struct PluginGUIPort {
    bool valid;
    unsigned int index;
    std::string name;
    std::string symbol;
};

struct PluginGUI {
    std::string resources_directory;
    std::string icon_template;
    std::string settings_template;
    std::string javascript;
    std::string stylesheet;
    std::string screenshot;
    std::string thumbnail;
    std::string discussion_url;
    std::string documentation;
    std::string brand;
    std::string label;
    std::string model;
    std::string panel;
    std::string color;
    std::string knob;
    std::vector<PluginGUIPort> ports;
    std::vector<std::string> monitored_outputs;
};

struct PluginGUI_Mini {
    std::string resources_directory;
    std::string screenshot;
    std::string thumbnail;
};

struct PluginParameter {
    bool valid;
    bool readable;
    bool writable;
    std::string uri;
    std::string label;
    std::string type;
    // For regular controls
    std::variant<double, int64_t, std::string> ranges;
    PluginUnits units;
    std::string comment;
    std::string short_name;
    // For path stuff
    std::vector<std::string> file_types;
    std::vector<std::string> supported_extensions;
};

struct PluginInfo_Essentials {
    std::vector<PluginPort> control_inputs;
    std::vector<std::string> monitored_outputs;
    std::vector<PluginParameter> parameters;
    std::string build_environment;
    int micro_version;
    int minor_version;
    int release;
    int builder;
};

struct PluginInstance {
    std::string uri;
    std::string instance_id;
    std::string name;
    std::string brand;
    std::string version;
    std::unordered_map<std::string, double> parameters;
    PluginPorts ports;
    double x = 0.0;
    double y = 0.0;
    bool enabled = true;
    std::string preset;
    std::chrono::system_clock::time_point created_at;

    PluginInstance() : created_at(std::chrono::system_clock::now()) {}
};

// Plugin manager command types
struct LoadPluginRequest {
    std::string uri;
    double x = 0.0;
    double y = 0.0;
    std::unordered_map<std::string, double> parameters;
};

struct UnloadPluginRequest {
    std::string instance_id;
};

struct SetParameterRequest {
    std::string instance_id;
    std::string parameter;
    double value;
};

struct GetParameterRequest {
    std::string instance_id;
    std::string parameter;
};

struct GetPluginInfoRequest {
    std::string instance_id;
};

struct ListInstancesRequest {
    // No additional fields needed
};

struct ClearAllRequest {
    // No additional fields needed
};

struct GetAvailablePluginsRequest {
    // No additional fields needed
};

struct SearchPluginsRequest {
    std::string query;
    std::optional<PluginSearchCriteria> criteria;
};

struct GetPluginPresetsRequest {
    std::string plugin_uri;
};

struct LoadPresetRequest {
    std::string plugin_uri;
    std::string preset_uri;
};

struct SavePresetRequest {
    std::string plugin_uri;
    PluginPreset preset;
};

struct RescanPluginsRequest {
    // No additional fields needed
};

struct ValidatePresetRequest {
    std::string plugin_uri;
    std::string preset_uri;
};

struct RescanPresetsRequest {
    std::string plugin_uri;
};

struct GetPluginGUIRequest {
    std::string plugin_uri;
};

struct GetPluginGUIMiniRequest {
    std::string plugin_uri;
};

struct GetPluginEssentialsRequest {
    std::string plugin_uri;
};

struct IsBundleLoadedRequest {
    std::string bundle_path;
};

struct AddBundleRequest {
    std::string bundle_path;
};

struct RemoveBundleRequest {
    std::string bundle_path;
    std::string resource_path;
};

struct ListBundlePluginsRequest {
    std::string bundle_path;
};

using PluginCommand = std::variant<
    LoadPluginRequest,
    UnloadPluginRequest,
    SetParameterRequest,
    GetParameterRequest,
    GetPluginInfoRequest,
    ListInstancesRequest,
    ClearAllRequest,
    GetAvailablePluginsRequest,
    SearchPluginsRequest,
    GetPluginPresetsRequest,
    LoadPresetRequest,
    SavePresetRequest,
    RescanPluginsRequest,
    ValidatePresetRequest,
    RescanPresetsRequest,
    GetPluginGUIRequest,
    GetPluginGUIMiniRequest,
    GetPluginEssentialsRequest,
    IsBundleLoadedRequest,
    AddBundleRequest,
    RemoveBundleRequest,
    ListBundlePluginsRequest
>;

// Plugin manager response types
struct LoadPluginResponse {
    std::string instance_id;
    PluginInstance plugin;
};

struct UnloadPluginResponse {
    std::string status;
    std::string instance_id;
};

struct SetParameterResponse {
    std::string status;
    double value;
};

struct GetParameterResponse {
    std::string parameter;
    double value;
};

struct GetPluginInfoResponse {
    PluginInstance plugin;
};

struct ListInstancesResponse {
    std::unordered_map<std::string, PluginInstance> instances;
};

struct ClearAllResponse {
    std::string status;
};

struct GetAvailablePluginsResponse {
    std::unordered_map<std::string, PluginInfo> plugins;
};

struct SearchPluginsResponse {
    std::vector<PluginInfo> plugins;
};

struct GetPluginPresetsResponse {
    std::string plugin_uri;
    std::vector<PluginPreset> presets;
};

struct LoadPresetResponse {
    std::string status;
    std::string preset_uri;
};

struct SavePresetResponse {
    std::string status;
    std::string preset_uri;
};

struct RescanPluginsResponse {
    std::string status;
    int plugins_added;
    int plugins_removed;
};

struct ValidatePresetResponse {
    bool is_valid;
};

struct RescanPresetsResponse {
    std::string status;
};

struct GetPluginGUIResponse {
    std::string plugin_uri;
    std::unique_ptr<PluginGUI> gui;
};

struct GetPluginGUIMiniResponse {
    std::string plugin_uri;
    std::unique_ptr<PluginGUI_Mini> gui_mini;
};

struct GetPluginEssentialsResponse {
    std::string plugin_uri;
    std::unique_ptr<PluginInfo_Essentials> essentials;
};

struct IsBundleLoadedResponse {
    bool is_loaded;
};

struct AddBundleResponse {
    std::vector<std::string> added_plugins;
};

struct RemoveBundleResponse {
    std::vector<std::string> removed_plugins;
};

struct ListBundlePluginsResponse {
    std::vector<std::string> plugins;
};

using PluginResponse = std::variant<
    LoadPluginResponse,
    UnloadPluginResponse,
    SetParameterResponse,
    GetParameterResponse,
    GetPluginInfoResponse,
    ListInstancesResponse,
    ClearAllResponse,
    GetAvailablePluginsResponse,
    SearchPluginsResponse,
    GetPluginPresetsResponse,
    LoadPresetResponse,
    SavePresetResponse,
    RescanPluginsResponse,
    ValidatePresetResponse,
    RescanPresetsResponse,
    GetPluginGUIResponse,
    GetPluginGUIMiniResponse,
    GetPluginEssentialsResponse,
    IsBundleLoadedResponse,
    AddBundleResponse,
    RemoveBundleResponse,
    ListBundlePluginsResponse
>;

// Feedback message types
struct ParamSet {
    std::string type = "param_set";
    uint32_t effect_id;
    std::string symbol;
    double value;
};

struct AudioMonitor {
    std::string type = "audio_monitor";
    uint32_t index;
    double value;
};

struct OutputSet {
    std::string type = "output_set";
    uint32_t effect_id;
    std::string symbol;
    double value;
};

struct MidiMapped {
    std::string type = "midi_mapped";
    uint32_t effect_id;
    std::string symbol;
    uint32_t channel;
    uint32_t controller;
};

struct MidiControlChange {
    std::string type = "midi_control_change";
    uint32_t channel;
    uint32_t control;
    uint32_t value;
};

struct MidiProgramChange {
    std::string type = "midi_program_change";
    uint32_t program;
    uint32_t channel;
};

struct Transport {
    std::string type = "transport";
    bool rolling;
    double bpb;
    double bpm;
};

struct PatchSet {
    std::string type = "patch_set";
    uint32_t instance;
    std::string symbol;
    Json::Value value;
};

struct Log {
    std::string type = "log";
    uint32_t level;
    std::string message;
};

struct CpuLoad {
    std::string type = "cpu_load";
    double load;
    double max_load;
    uint32_t xruns;
};

struct DataFinish {
    std::string type = "data_finish";
};

struct CcMap {
    std::string type = "cc_map";
    std::string raw;
};

struct UnknownFeedback {
    std::string type = "unknown";
    std::string raw;
};

using FeedbackMessage = std::variant<
    ParamSet, AudioMonitor, OutputSet, MidiMapped, MidiControlChange,
    MidiProgramChange, Transport, PatchSet, Log, CpuLoad, DataFinish,
    CcMap, UnknownFeedback
>;

// Health state structure
struct HealthState {
    HealthStatus status = HealthStatus::Starting;
    bool command_connected = false;
    bool feedback_connected = false;
    std::chrono::steady_clock::time_point last_health_log;

    HealthState();
    void update_command_connection(bool connected);
    void update_feedback_connection(bool connected);
    void update_overall_status();
    HealthResponse get_health_response() const;
};

// Audio system types
struct JackData {
    double cpu_load;
    uint32_t xruns;
    bool rolling;
    double bpb;
    double bpm;
};

// Audio system command types
struct InitJackRequest {
    // No additional fields needed
};

struct CloseJackRequest {
    // No additional fields needed
};

struct GetJackDataRequest {
    std::optional<bool> with_transport;
};

struct GetJackBufferSizeRequest {
    // No additional fields needed
};

struct SetJackBufferSizeRequest {
    unsigned size;
};

struct GetJackSampleRateRequest {
    // No additional fields needed
};

struct GetJackPortAliasRequest {
    std::string port_name;
};

struct GetJackHardwarePortsRequest {
    bool is_audio;
    bool is_output;
};

struct HasMidiBeatClockSenderPortRequest {
    // No additional fields needed
};

struct HasSerialMidiInputPortRequest {
    // No additional fields needed
};

struct HasSerialMidiOutputPortRequest {
    // No additional fields needed
};

struct HasMidiMergerOutputPortRequest {
    // No additional fields needed
};

struct HasMidiBroadcasterInputPortRequest {
    // No additional fields needed
};

struct HasDuoxSplitSpdifRequest {
    // No additional fields needed
};

struct ConnectJackPortsRequest {
    std::string port1;
    std::string port2;
};

struct ConnectJackMidiOutputPortsRequest {
    std::string port;
};

struct DisconnectJackPortsRequest {
    std::string port1;
    std::string port2;
};

struct DisconnectAllJackPortsRequest {
    std::string port;
};

struct ResetXrunsRequest {
    // No additional fields needed
};

using AudioCommand = std::variant<
    InitJackRequest,
    CloseJackRequest,
    GetJackDataRequest,
    GetJackBufferSizeRequest,
    SetJackBufferSizeRequest,
    GetJackSampleRateRequest,
    GetJackPortAliasRequest,
    GetJackHardwarePortsRequest,
    HasMidiBeatClockSenderPortRequest,
    HasSerialMidiInputPortRequest,
    HasSerialMidiOutputPortRequest,
    HasMidiMergerOutputPortRequest,
    HasMidiBroadcasterInputPortRequest,
    HasDuoxSplitSpdifRequest,
    ConnectJackPortsRequest,
    ConnectJackMidiOutputPortsRequest,
    DisconnectJackPortsRequest,
    DisconnectAllJackPortsRequest,
    ResetXrunsRequest
>;

// Audio system response types
struct InitJackResponse {
    bool success;
};

struct CloseJackResponse {
    bool success;
};

struct GetJackDataResponse {
    std::unique_ptr<JackData> data;
};

struct GetJackBufferSizeResponse {
    unsigned buffer_size;
};

struct SetJackBufferSizeResponse {
    unsigned buffer_size;
};

struct GetJackSampleRateResponse {
    float sample_rate;
};

struct GetJackPortAliasResponse {
    std::string alias;
};

struct GetJackHardwarePortsResponse {
    std::vector<std::string> ports;
};

struct HasMidiBeatClockSenderPortResponse {
    bool has_port;
};

struct HasSerialMidiInputPortResponse {
    bool has_port;
};

struct HasSerialMidiOutputPortResponse {
    bool has_port;
};

struct HasMidiMergerOutputPortResponse {
    bool has_port;
};

struct HasMidiBroadcasterInputPortResponse {
    bool has_port;
};

struct HasDuoxSplitSpdifResponse {
    bool has_feature;
};

struct ConnectJackPortsResponse {
    bool success;
};

struct ConnectJackMidiOutputPortsResponse {
    bool success;
};

struct DisconnectJackPortsResponse {
    bool success;
};

struct DisconnectAllJackPortsResponse {
    bool success;
};

struct ResetXrunsResponse {
    bool success;
};

using AudioResponse = std::variant<
    InitJackResponse,
    CloseJackResponse,
    GetJackDataResponse,
    GetJackBufferSizeResponse,
    SetJackBufferSizeResponse,
    GetJackSampleRateResponse,
    GetJackPortAliasResponse,
    GetJackHardwarePortsResponse,
    HasMidiBeatClockSenderPortResponse,
    HasSerialMidiInputPortResponse,
    HasSerialMidiOutputPortResponse,
    HasMidiMergerOutputPortResponse,
    HasMidiBroadcasterInputPortResponse,
    HasDuoxSplitSpdifResponse,
    ConnectJackPortsResponse,
    ConnectJackMidiOutputPortsResponse,
    DisconnectJackPortsResponse,
    DisconnectAllJackPortsResponse,
    ResetXrunsResponse
>;

// JSON serialization helpers
Json::Value to_json(const HealthStatus& status);
Json::Value to_json(const HealthResponse& response);
Json::Value to_json(const CommandResponse& response);
Json::Value to_json(const FeedbackMessage& message);
Json::Value to_json(const PluginInstance& instance);
Json::Value to_json(const PluginInfo& info);
Json::Value to_json(const PluginResponse& response);
Json::Value to_json(const AudioResponse& response);

} // namespace modhost_bridge
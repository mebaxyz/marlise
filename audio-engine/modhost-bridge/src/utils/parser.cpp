#include "parser.h"
#include <spdlog/spdlog.h>
#include <sstream>
#include <algorithm>

namespace modhost_bridge {

std::optional<FeedbackMessage> parse_feedback_line(const std::string& line) {
    std::istringstream iss(line);
    std::string type;
    iss >> type;

    try {
        if (type == "param_set") {
            uint32_t effect_id;
            std::string symbol;
            double value;
            iss >> effect_id >> symbol >> value;
            return ParamSet{"param_set", effect_id, symbol, value};

        } else if (type == "audio_monitor") {
            uint32_t index;
            double value;
            iss >> index >> value;
            return AudioMonitor{"audio_monitor", index, value};

        } else if (type == "output_set") {
            uint32_t effect_id;
            std::string symbol;
            double value;
            iss >> effect_id >> symbol >> value;
            return OutputSet{"output_set", effect_id, symbol, value};

        } else if (type == "midi_mapped") {
            uint32_t effect_id, channel, controller;
            std::string symbol;
            iss >> effect_id >> symbol >> channel >> controller;
            return MidiMapped{"midi_mapped", effect_id, symbol, channel, controller};

        } else if (type == "midi_control_change") {
            uint32_t channel, control, value;
            iss >> channel >> control >> value;
            return MidiControlChange{"midi_control_change", channel, control, value};

        } else if (type == "midi_program_change") {
            uint32_t program, channel;
            iss >> program >> channel;
            return MidiProgramChange{"midi_program_change", program, channel};

        } else if (type == "transport") {
            bool rolling;
            double bpb, bpm;
            iss >> rolling >> bpb >> bpm;
            return Transport{"transport", rolling, bpb, bpm};

        } else if (type == "patch_set") {
            uint32_t instance;
            std::string symbol;
            iss >> instance >> symbol;
            // Read remaining as JSON value
            std::string remaining;
            std::getline(iss, remaining);
            if (!remaining.empty() && remaining[0] == ' ') {
                remaining = remaining.substr(1);
            }
            Json::Value value;
            Json::Reader reader;
            reader.parse(remaining, value);
            return PatchSet{"patch_set", instance, symbol, value};

        } else if (type == "log") {
            uint32_t level;
            std::string message;
            iss >> level;
            std::getline(iss, message);
            if (!message.empty() && message[0] == ' ') {
                message = message.substr(1);
            }
            return Log{"log", level, message};

        } else if (type == "cpu_load") {
            double load, max_load;
            uint32_t xruns;
            iss >> load >> max_load >> xruns;
            return CpuLoad{"cpu_load", load, max_load, xruns};

        } else if (type == "data_finish") {
            return DataFinish{"data_finish"};

        } else if (type == "cc_map") {
            std::string raw;
            std::getline(iss, raw);
            if (!raw.empty() && raw[0] == ' ') {
                raw = raw.substr(1);
            }
            return CcMap{"cc_map", raw};

        } else {
            return UnknownFeedback{"unknown", line};
        }
    } catch (const std::exception& e) {
        spdlog::warn("Failed to parse feedback line '{}': {}", line, e.what());
        return UnknownFeedback{"unknown", line};
    }
}

} // namespace modhost_bridge
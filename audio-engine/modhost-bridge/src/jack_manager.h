#include "audio_system_manager.h"
#include "types.h"
#include <spdlog/spdlog.h>
#include <cstring>

// Include MOD utils headers
extern "C" {
#include <mod-host.h>
}

namespace modhost_bridge {

/**
 * JACK audio system manager implementation
 */
class JackManager : public AudioSystemManager {
public:
    JackManager() : initialized_(false) {}
    ~JackManager() override {
        if (initialized_) {
            close();
        }
    }

    bool init() override {
        if (initialized_) return true;

        spdlog::info("Initializing JACK audio system");
        bool success = ::init_jack();

        if (success) {
            initialized_ = true;
            spdlog::info("JACK audio system initialized successfully");
        } else {
            spdlog::error("Failed to initialize JACK audio system");
        }

        return success;
    }

    void close() override {
        if (!initialized_) return;

        spdlog::info("Closing JACK audio system");
        ::close_jack();
        initialized_ = false;
        spdlog::info("JACK audio system closed");
    }

    std::unique_ptr<JackData> get_data(bool with_transport) override {
        if (!initialized_) {
            spdlog::error("JACK system not initialized");
            return nullptr;
        }

        const ::JackData* mod_jack_data = ::get_jack_data(with_transport);
        if (!mod_jack_data) {
            return nullptr;
        }

        return std::make_unique<JackData>(JackData{
            mod_jack_data->cpuLoad,
            mod_jack_data->xruns,
            mod_jack_data->rolling,
            mod_jack_data->bpb,
            mod_jack_data->bpm
        });
    }

    unsigned get_buffer_size() override {
        if (!initialized_) {
            spdlog::error("JACK system not initialized");
            return 0;
        }

        return ::get_jack_buffer_size();
    }

    unsigned set_buffer_size(unsigned size) override {
        if (!initialized_) {
            spdlog::error("JACK system not initialized");
            return 0;
        }

        return ::set_jack_buffer_size(size);
    }

    float get_sample_rate() override {
        if (!initialized_) {
            spdlog::error("JACK system not initialized");
            return 0.0f;
        }

        return ::get_jack_sample_rate();
    }

    std::string get_port_alias(const std::string& port_name) override {
        if (!initialized_) {
            spdlog::error("JACK system not initialized");
            return "";
        }

        const char* alias = ::get_jack_port_alias(port_name.c_str());
        return alias ? alias : "";
    }

    std::vector<std::string> get_hardware_ports(bool is_audio, bool is_output) override {
        if (!initialized_) {
            spdlog::error("JACK system not initialized");
            return {};
        }

        const char* const* ports = ::get_jack_hardware_ports(is_audio, is_output);
        std::vector<std::string> result;
        if (ports) {
            for (int i = 0; ports[i] != nullptr; ++i) {
                result.push_back(ports[i]);
            }
        }

        return result;
    }

    bool has_midi_beat_clock_sender_port() override {
        if (!initialized_) {
            spdlog::error("JACK system not initialized");
            return false;
        }

        return ::has_midi_beat_clock_sender_port();
    }

    bool has_serial_midi_input_port() override {
        if (!initialized_) {
            spdlog::error("JACK system not initialized");
            return false;
        }

        return ::has_serial_midi_input_port();
    }

    bool has_serial_midi_output_port() override {
        if (!initialized_) {
            spdlog::error("JACK system not initialized");
            return false;
        }

        return ::has_serial_midi_output_port();
    }

    bool has_midi_merger_output_port() override {
        if (!initialized_) {
            spdlog::error("JACK system not initialized");
            return false;
        }

        return ::has_midi_merger_output_port();
    }

    bool has_midi_broadcaster_input_port() override {
        if (!initialized_) {
            spdlog::error("JACK system not initialized");
            return false;
        }

        return ::has_midi_broadcaster_input_port();
    }

    bool has_duox_split_spdif() override {
        if (!initialized_) {
            spdlog::error("JACK system not initialized");
            return false;
        }

        return ::has_duox_split_spdif();
    }

    bool connect_ports(const std::string& port1, const std::string& port2) override {
        if (!initialized_) {
            spdlog::error("JACK system not initialized");
            return false;
        }

        return ::connect_jack_ports(port1.c_str(), port2.c_str());
    }

    bool connect_midi_output_ports(const std::string& port) override {
        if (!initialized_) {
            spdlog::error("JACK system not initialized");
            return false;
        }

        return ::connect_jack_midi_output_ports(port.c_str());
    }

    bool disconnect_ports(const std::string& port1, const std::string& port2) override {
        if (!initialized_) {
            spdlog::error("JACK system not initialized");
            return false;
        }

        return ::disconnect_jack_ports(port1.c_str(), port2.c_str());
    }

    bool disconnect_all_ports(const std::string& port) override {
        if (!initialized_) {
            spdlog::error("JACK system not initialized");
            return false;
        }

        return ::disconnect_all_jack_ports(port.c_str());
    }

    void reset_xruns() override {
        if (!initialized_) {
            spdlog::error("JACK system not initialized");
            return;
        }

        ::reset_xruns();
    }

    std::string get_system_name() const override {
        return "JACK";
    }

private:
    bool initialized_;
};

} // namespace modhost_bridge
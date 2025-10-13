#include "audio_system_manager.h"
#include "../utils/types.h"
#include <spdlog/spdlog.h>
#include <cstring>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>

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
    JackManager() : initialized_(false), mod_host_host_("127.0.0.1"), mod_host_port_(5555) {}
    
    JackManager(const std::string& mod_host_host, uint16_t mod_host_port) 
        : initialized_(false), mod_host_host_(mod_host_host), mod_host_port_(mod_host_port) {}
    
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

        // Send connect command to mod-host
        std::string command = "connect " + port1 + " " + port2;
        spdlog::info("Sending to mod-host: {}", command);
        auto response = send_to_modhost(command);
        spdlog::info("Received from mod-host: '{}'", response ? *response : "no response");
        
        if (!response) {
            spdlog::error("Failed to connect ports {} -> {}: no response from mod-host", port1, port2);
            return false;
        }
        
        // Check for success (resp 0) or any response starting with "resp"
        // The response may have trailing newlines or whitespace
        std::string resp_str = *response;
        // Trim whitespace
        resp_str.erase(resp_str.find_last_not_of(" \n\r\t") + 1);
        
        if (resp_str.find("resp 0") == std::string::npos) {
            spdlog::error("Failed to connect ports {} -> {}: {}", port1, port2, resp_str);
            return false;
        }
        
        spdlog::info("Successfully connected ports {} -> {}", port1, port2);
        return true;
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

        // Send disconnect command to mod-host
        std::string command = "disconnect " + port1 + " " + port2;
        auto response = send_to_modhost(command);
        if (!response || response->find("resp 0") == std::string::npos) {
            spdlog::error("Failed to disconnect ports {} -> {}: {}", port1, port2,
                         response ? *response : "no response");
            return false;
        }
        return true;
    }

    bool disconnect_all_ports(const std::string& port) override {
        if (!initialized_) {
            spdlog::error("JACK system not initialized");
            return false;
        }

        // Send disconnect_all command to mod-host
        std::string command = "disconnect_all " + port;
        auto response = send_to_modhost(command);
        if (!response || response->find("resp 0") == std::string::npos) {
            spdlog::error("Failed to disconnect all ports for {}: {}", port,
                         response ? *response : "no response");
            return false;
        }
        return true;
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
    /**
     * Send command to mod-host and get response
     */
    std::optional<std::string> send_to_modhost(const std::string& command) {
        int sock = socket(AF_INET, SOCK_STREAM, 0);
        if (sock < 0) {
            spdlog::error("Failed to create socket for mod-host command");
            return std::nullopt;
        }

        struct sockaddr_in serv_addr;
        serv_addr.sin_family = AF_INET;
        serv_addr.sin_port = htons(mod_host_port_);
        if (inet_pton(AF_INET, mod_host_host_.c_str(), &serv_addr.sin_addr) <= 0) {
            ::close(sock);
            spdlog::error("Invalid mod-host address: {}", mod_host_host_);
            return std::nullopt;
        }

        if (connect(sock, (struct sockaddr*)&serv_addr, sizeof(serv_addr)) < 0) {
            ::close(sock);
            spdlog::error("Failed to connect to mod-host at {}:{}", mod_host_host_, mod_host_port_);
            return std::nullopt;
        }

        // Send command
        std::string cmd_with_newline = command + "\n";
        ssize_t sent = send(sock, cmd_with_newline.c_str(), cmd_with_newline.length(), 0);
        if (sent < 0) {
            ::close(sock);
            spdlog::error("Failed to send command to mod-host");
            return std::nullopt;
        }

        // Read response
        char buffer[1024] = {0};
        ssize_t received = recv(sock, buffer, sizeof(buffer) - 1, 0);
        ::close(sock);

        if (received < 0) {
            spdlog::error("Failed to receive response from mod-host");
            return std::nullopt;
        }

        return std::string(buffer, received);
    }

    bool initialized_;
    std::string mod_host_host_;
    uint16_t mod_host_port_;
};

} // namespace modhost_bridge
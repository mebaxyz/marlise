#pragma once

#include "../utils/types.h"
#include "../plugins/plugin_manager.h"
#include "../audio/audio_system_manager.h"
#include <zmq.hpp>
#include <memory>
#include <thread>
#include <atomic>

namespace modhost_bridge {

/**
 * Command service that handles ZeroMQ REP requests and forwards them to mod-host.
 *
 * This class runs a ZeroMQ REP socket to receive JSON command requests from clients,
 * forwards them to mod-host via TCP, and returns the responses.
 */
class CommandService {
public:
    /**
     * Constructor
     *
     * @param zmq_context ZeroMQ context
     * @param rep_endpoint ZeroMQ REP socket endpoint
     * @param mod_host_host mod-host hostname/IP
     * @param mod_host_port mod-host command port
     * @param plugin_manager Shared plugin manager instance
     * @param audio_system_manager Shared audio system manager instance
     * @param health_state Shared health state
     */
    CommandService(zmq::context_t& zmq_context,
                   const std::string& rep_endpoint,
                   const std::string& mod_host_host,
                   uint16_t mod_host_port,
                   std::shared_ptr<PluginManager> plugin_manager,
                   std::shared_ptr<AudioSystemManager> audio_system_manager,
                   std::shared_ptr<HealthState> health_state);

    /**
     * Destructor - stops the service thread
     */
    ~CommandService();

    /**
     * Start the command service (non-blocking)
     */
    void start();

    /**
     * Stop the command service
     */
    void stop();

private:
    /**
     * Main service loop
     */
    void service_loop();

    /**
     * Process a single command request
     */
    Json::Value process_command(const CommandRequest& request);

    /**
     * Process a plugin command
     */
    Json::Value process_plugin_command(const Json::Value& request);

    /**
     * Process an audio command
     */
    Json::Value process_audio_command(const Json::Value& request);

    /**
     * Send command to mod-host and get response
     */
    std::optional<std::string> send_to_modhost(const std::string& command);

    zmq::context_t& zmq_context_;
    std::string rep_endpoint_;
    std::string mod_host_host_;
    uint16_t mod_host_port_;
    std::shared_ptr<PluginManager> plugin_manager_;
    std::shared_ptr<AudioSystemManager> audio_system_manager_;
    std::shared_ptr<HealthState> health_state_;

    std::unique_ptr<zmq::socket_t> rep_socket_;
    std::thread service_thread_;
    std::atomic<bool> running_;
};

} // namespace modhost_bridge
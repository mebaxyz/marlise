#pragma once

#include "../utils/types.h"
#include <zmq.hpp>
#include <memory>
#include <thread>
#include <atomic>

namespace modhost_bridge {

/**
 * Feedback reader that connects to mod-host's feedback port and publishes events via ZeroMQ.
 *
 * This class establishes a TCP connection to mod-host's feedback port and continuously
 * reads NUL-terminated lines. Each line is parsed into a structured message and published
 * as JSON on the ZeroMQ PUB socket.
 */
class FeedbackReader {
public:
    /**
     * Constructor
     *
     * @param zmq_context ZeroMQ context
     * @param pub_socket Shared ZeroMQ PUB socket for events
     * @param mod_host_host mod-host hostname/IP
     * @param mod_host_feedback_port mod-host feedback port
     * @param health_state Shared health state
     */
    FeedbackReader(zmq::context_t& zmq_context,
                   zmq::socket_t& pub_socket,
                   const std::string& mod_host_host,
                   uint16_t mod_host_feedback_port,
                   std::shared_ptr<HealthState> health_state);

    /**
     * Destructor - stops the reader thread
     */
    ~FeedbackReader();

    /**
     * Start the feedback reader (non-blocking)
     */
    void start();

    /**
     * Stop the feedback reader
     */
    void stop();

private:
    /**
     * Main reader loop
     */
    void reader_loop();

    /**
     * Attempt to connect to mod-host feedback port
     */
    bool connect_to_modhost();

    zmq::context_t& zmq_context_;
    zmq::socket_t& pub_socket_;
    std::string mod_host_host_;
    uint16_t mod_host_feedback_port_;
    std::shared_ptr<HealthState> health_state_;

    int tcp_socket_ = -1;
    std::thread reader_thread_;
    std::atomic<bool> running_;
};

} // namespace modhost_bridge
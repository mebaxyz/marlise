#pragma once

#include "../utils/types.h"
#include <zmq.hpp>
#include <memory>
#include <thread>
#include <atomic>

namespace modhost_bridge {

/**
 * Health check service that responds to health status requests via ZeroMQ.
 *
 * This class runs a ZeroMQ REP socket to provide health status information
 * to external monitoring systems.
 */
class HealthMonitor {
public:
    /**
     * Constructor
     *
     * @param zmq_context ZeroMQ context
     * @param health_endpoint ZeroMQ REP socket endpoint for health checks
     * @param health_state Shared health state
     */
    HealthMonitor(zmq::context_t& zmq_context,
                  const std::string& health_endpoint,
                  std::shared_ptr<HealthState> health_state);

    /**
     * Destructor - stops the monitor thread
     */
    ~HealthMonitor();

    /**
     * Start the health monitor (non-blocking)
     */
    void start();

    /**
     * Stop the health monitor
     */
    void stop();

private:
    /**
     * Main monitor loop
     */
    void monitor_loop();

    zmq::context_t& zmq_context_;
    std::string health_endpoint_;
    std::shared_ptr<HealthState> health_state_;

    std::unique_ptr<zmq::socket_t> health_socket_;
    std::thread monitor_thread_;
    std::atomic<bool> running_;
};

} // namespace modhost_bridge
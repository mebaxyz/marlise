#include "utils/types.h"
#include "core/feedback_reader.h"
#include "core/command_service.h"
#include "core/health_monitor.h"
#include "plugins/plugin_manager.h"
#include "audio/audio_system_manager.h"
#include "audio/jack_manager.h"
#include <spdlog/spdlog.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <fcntl.h>
#include <cstdlib>
#include <csignal>
#include <atomic>
#include <chrono>
#include <thread>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/stat.h>
#include <errno.h>
#include <sstream>
#include <vector>
#include <cstring>

namespace {

// Default configuration constants
const std::string DEFAULT_MOD_HOST_HOST = "127.0.0.1";
const uint16_t DEFAULT_MOD_HOST_PORT = 5555;
const uint16_t DEFAULT_MOD_HOST_FEEDBACK_PORT = 5556;
const std::string DEFAULT_ZMQ_REP_ADDR = "tcp://127.0.0.1:6000";
const std::string DEFAULT_ZMQ_PUB_ADDR = "tcp://127.0.0.1:6001";
const std::string DEFAULT_ZMQ_HEALTH_ADDR = "tcp://127.0.0.1:6002";

// Connection retry constants
const std::chrono::milliseconds CONNECTION_RETRY_DELAY(1000);
const std::chrono::seconds CONNECTION_TIMEOUT(5);

// Global shutdown flag
std::atomic<bool> shutdown_requested(false);

void signal_handler(int signal) {
    spdlog::info("Received signal {}, initiating shutdown...", signal);
    shutdown_requested = true;
}

} // anonymous namespace

namespace modhost_bridge {

/**
 * Test TCP connection to mod-host with timeout
 */
bool test_connection(const std::string& host, uint16_t port) {
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) {
        return false;
    }

    // Set non-blocking
    int flags = fcntl(sock, F_GETFL, 0);
    fcntl(sock, F_SETFL, flags | O_NONBLOCK);

    struct sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(port);
    inet_pton(AF_INET, host.c_str(), &server_addr.sin_addr);

    // Attempt connection
    int result = connect(sock, (struct sockaddr*)&server_addr, sizeof(server_addr));
    if (result < 0) {
        if (errno == EINPROGRESS) {
            // Connection in progress, wait with timeout
            fd_set write_fds;
            FD_ZERO(&write_fds);
            FD_SET(sock, &write_fds);

            struct timeval timeout;
            timeout.tv_sec = CONNECTION_TIMEOUT.count();
            timeout.tv_usec = 0;

            result = select(sock + 1, nullptr, &write_fds, nullptr, &timeout);
            if (result > 0) {
                // Check if connection was successful
                int error;
                socklen_t len = sizeof(error);
                getsockopt(sock, SOL_SOCKET, SO_ERROR, &error, &len);
                close(sock);
                return error == 0;
            }
        }
        close(sock);
        return false;
    }

    close(sock);
    return true;
}

/**
 * Wait for mod-host to become available
 */
bool wait_for_modhost(const std::string& host, uint16_t command_port, uint16_t feedback_port,
                      std::shared_ptr<HealthState> health_state) {
    spdlog::info("Waiting for mod-host to become available at {}:{} (command) and {}:{} (feedback)",
                host, command_port, host, feedback_port);

    while (!shutdown_requested) {
        // Try command port first
        if (test_connection(host, command_port)) {
            spdlog::info("Successfully connected to mod-host command port {}:{}", host, command_port);
            health_state->update_command_connection(true);

            // Now try feedback port
            if (test_connection(host, feedback_port)) {
                spdlog::info("Successfully connected to mod-host feedback port {}:{}", host, feedback_port);
                health_state->update_feedback_connection(true);
                return true;
            } else {
                spdlog::warn("Cannot connect to mod-host feedback port {}:{}", host, feedback_port);
                health_state->update_feedback_connection(false);
            }
        } else {
            spdlog::warn("Cannot connect to mod-host command port {}:{}", host, command_port);
            health_state->update_command_connection(false);
            health_state->update_feedback_connection(false);
        }

        // Wait before retrying
        std::this_thread::sleep_for(CONNECTION_RETRY_DELAY);
    }

    return false;
}

} // namespace modhost_bridge

// Helper utilities to optionally build and start mod-host
namespace {
// No auto-build / auto-start helpers: runtime building or spawning of mod-host
// has been removed. The bridge now expects mod-host to be started externally
// (or managed by orchestration scripts). The bridge will still wait for mod- host
// to be reachable (via wait_for_modhost) but will not build or spawn the process.

} // anonymous

int main(int argc, char* argv[]) {
    // Initialize logging
    spdlog::set_level(spdlog::level::info);
    spdlog::set_pattern("[%Y-%m-%d %H:%M:%S] [%l] %v");

    // Set up signal handlers
    std::signal(SIGINT, signal_handler);
    std::signal(SIGTERM, signal_handler);

    try {
        // Read configuration from environment variables
        std::string mod_host_host = std::getenv("MOD_HOST_HOST") ?
            std::getenv("MOD_HOST_HOST") : DEFAULT_MOD_HOST_HOST;
        uint16_t mod_host_port = std::getenv("MOD_HOST_PORT") ?
            static_cast<uint16_t>(std::stoi(std::getenv("MOD_HOST_PORT"))) : DEFAULT_MOD_HOST_PORT;
        uint16_t mod_host_feedback_port = std::getenv("MOD_HOST_FEEDBACK_PORT") ?
            static_cast<uint16_t>(std::stoi(std::getenv("MOD_HOST_FEEDBACK_PORT"))) : DEFAULT_MOD_HOST_FEEDBACK_PORT;

        std::string zmq_rep_addr = std::getenv("MODHOST_BRIDGE_REP") ?
            std::getenv("MODHOST_BRIDGE_REP") : DEFAULT_ZMQ_REP_ADDR;
        std::string zmq_pub_addr = std::getenv("MODHOST_BRIDGE_PUB") ?
            std::getenv("MODHOST_BRIDGE_PUB") : DEFAULT_ZMQ_PUB_ADDR;
        std::string zmq_health_addr = std::getenv("MODHOST_BRIDGE_HEALTH") ?
            std::getenv("MODHOST_BRIDGE_HEALTH") : DEFAULT_ZMQ_HEALTH_ADDR;

        spdlog::info("Starting mod-host-bridge");
        spdlog::info("mod-host: {}:{} (command), {}:{} (feedback)",
                    mod_host_host, mod_host_port, mod_host_host, mod_host_feedback_port);
        spdlog::info("ZeroMQ: {} (REP), {} (PUB), {} (Health)",
                    zmq_rep_addr, zmq_pub_addr, zmq_health_addr);

        // Initialize health state
        auto health_state = std::make_shared<modhost_bridge::HealthState>();

        // Create ZeroMQ context
        zmq::context_t zmq_context(1);

        // Create and start health monitor BEFORE waiting for mod-host
        modhost_bridge::HealthMonitor health_monitor(zmq_context, zmq_health_addr, health_state);
        health_monitor.start();

        // Auto-build and auto-start behavior has been removed. The bridge expects
        // mod-host to be started (and JACK available) by orchestration or manually.
        spdlog::info("Auto-build/auto-start of mod-host is disabled. Ensure mod-host is started separately.");

        // Optionally wait for mod-host to become available (bridge will proceed only when reachable).
        if (!modhost_bridge::wait_for_modhost(mod_host_host, mod_host_port, mod_host_feedback_port, health_state)) {
            spdlog::error("Shutdown requested while waiting for mod-host");
            return 1;
        }

        // Create and start services
        auto plugin_manager = std::make_shared<modhost_bridge::PluginManager>(
            zmq_context, zmq_pub_addr, mod_host_host, mod_host_port, health_state);
        auto audio_system_manager = std::make_shared<modhost_bridge::JackManager>();
        modhost_bridge::FeedbackReader feedback_reader(zmq_context, *plugin_manager->get_pub_socket(),
                                                      mod_host_host, mod_host_feedback_port, health_state);
        auto command_service = std::make_shared<modhost_bridge::CommandService>(
            zmq_context, zmq_rep_addr, mod_host_host, mod_host_port,
            plugin_manager, audio_system_manager, health_state);

        // Initialize plugin manager
        plugin_manager->initialize();

        // Initialize JACK audio system
        if (!audio_system_manager->init()) {
            spdlog::warn("Failed to initialize JACK audio system - audio operations may not work");
        }

        feedback_reader.start();
        command_service->start();

        spdlog::info("All services started successfully");

        // Wait for shutdown signal
        while (!shutdown_requested) {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }

        spdlog::info("Shutting down services...");

        // Stop services
        feedback_reader.stop();
        command_service->stop();
        health_monitor.stop();
        plugin_manager->shutdown();

        // We do not manage the mod-host process lifecycle here.

        spdlog::info("Shutdown complete");
        return 0;

    } catch (const std::exception& e) {
        spdlog::error("Fatal error: {}", e.what());
        return 1;
    }
}
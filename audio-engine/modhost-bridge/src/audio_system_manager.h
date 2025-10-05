#pragma once

#include <string>
#include <vector>
#include <memory>
#include <optional>
#include "types.h"

namespace modhost_bridge {

/**
 * Abstract base class for audio system management.
 * Provides a common interface for different audio systems (JACK, PipeWire, etc.)
 */
class AudioSystemManager {
public:
    virtual ~AudioSystemManager() = default;

    /**
     * Initialize the audio system connection
     * @return true if successful
     */
    virtual bool init() = 0;

    /**
     * Close the audio system connection
     */
    virtual void close() = 0;

    /**
     * Get audio system data
     * @param with_transport Include transport information
     * @return Audio system data or nullptr
     */
    virtual std::unique_ptr<JackData> get_data(bool with_transport = false) = 0;

    /**
     * Get buffer size
     * @return Current buffer size
     */
    virtual unsigned get_buffer_size() = 0;

    /**
     * Set buffer size
     * @param size New buffer size
     * @return Actual buffer size set
     */
    virtual unsigned set_buffer_size(unsigned size) = 0;

    /**
     * Get sample rate
     * @return Current sample rate
     */
    virtual float get_sample_rate() = 0;

    /**
     * Get port alias
     * @param port_name Port name
     * @return Port alias or empty string
     */
    virtual std::string get_port_alias(const std::string& port_name) = 0;

    /**
     * Get hardware ports
     * @param is_audio true for audio ports, false for MIDI ports
     * @param is_output true for output ports, false for input ports
     * @return List of port names
     */
    virtual std::vector<std::string> get_hardware_ports(bool is_audio, bool is_output) = 0;

    /**
     * Check if system has MIDI beat clock sender port
     * @return true if available
     */
    virtual bool has_midi_beat_clock_sender_port() = 0;

    /**
     * Check if system has serial MIDI input port
     * @return true if available
     */
    virtual bool has_serial_midi_input_port() = 0;

    /**
     * Check if system has serial MIDI output port
     * @return true if available
     */
    virtual bool has_serial_midi_output_port() = 0;

    /**
     * Check if system has MIDI merger output port
     * @return true if available
     */
    virtual bool has_midi_merger_output_port() = 0;

    /**
     * Check if system has MIDI broadcaster input port
     * @return true if available
     */
    virtual bool has_midi_broadcaster_input_port() = 0;

    /**
     * Check if system has DuoX split SPDIF
     * @return true if available
     */
    virtual bool has_duox_split_spdif() = 0;

    /**
     * Connect two ports
     * @param port1 First port name
     * @param port2 Second port name
     * @return true if successful
     */
    virtual bool connect_ports(const std::string& port1, const std::string& port2) = 0;

    /**
     * Connect MIDI output ports
     * @param port Port name
     * @return true if successful
     */
    virtual bool connect_midi_output_ports(const std::string& port) = 0;

    /**
     * Disconnect two ports
     * @param port1 First port name
     * @param port2 Second port name
     * @return true if successful
     */
    virtual bool disconnect_ports(const std::string& port1, const std::string& port2) = 0;

    /**
     * Disconnect all connections for a port
     * @param port Port name
     * @return true if successful
     */
    virtual bool disconnect_all_ports(const std::string& port) = 0;

    /**
     * Reset XRUN counter
     */
    virtual void reset_xruns() = 0;

    /**
     * Get the name of the audio system (e.g., "JACK", "PipeWire")
     * @return System name
     */
    virtual std::string get_system_name() const = 0;
};

} // namespace modhost_bridge
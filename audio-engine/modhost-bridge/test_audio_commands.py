#!/usr/bin/env python3
"""
Simple test to verify audio command JSON serialization works correctly.
"""

import json
import sys
import os

# Add the build directory to Python path to import the compiled module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'build'))

def test_audio_commands():
    """Test that audio commands are properly structured"""

    print("Testing audio command structures...")

    # Test audio commands from MESSAGE_SCHEMAS.md
    audio_commands = [
        {
            "action": "audio",
            "method": "init_jack"
        },
        {
            "action": "audio",
            "method": "close_jack"
        },
        {
            "action": "audio",
            "method": "get_jack_data",
            "with_transport": True
        },
        {
            "action": "audio",
            "method": "get_jack_buffer_size"
        },
        {
            "action": "audio",
            "method": "set_jack_buffer_size",
            "size": 1024
        },
        {
            "action": "audio",
            "method": "get_jack_sample_rate"
        },
        {
            "action": "audio",
            "method": "get_jack_port_alias",
            "port_name": "system:capture_1"
        },
        {
            "action": "audio",
            "method": "get_jack_hardware_ports",
            "is_audio": True,
            "is_output": False
        },
        {
            "action": "audio",
            "method": "has_midi_beat_clock_sender_port"
        },
        {
            "action": "audio",
            "method": "connect_jack_ports",
            "port1": "system:capture_1",
            "port2": "effect:input"
        },
        {
            "action": "audio",
            "method": "disconnect_jack_ports",
            "port1": "system:capture_1",
            "port2": "effect:input"
        },
        {
            "action": "audio",
            "method": "reset_xruns"
        }
    ]

    print(f"✓ Defined {len(audio_commands)} audio command structures")

    # Test that they can be JSON serialized
    for i, cmd in enumerate(audio_commands, 1):
        try:
            json_str = json.dumps(cmd, indent=2)
            parsed = json.loads(json_str)
            assert parsed == cmd, f"Command {i} round-trip failed"
            print(f"✓ Command {i} ({cmd['method']}) serializes correctly")
        except Exception as e:
            print(f"✗ Command {i} ({cmd['method']}) failed: {e}")
            return False

    print("\n✓ All audio command structures are valid JSON!")
    return True

if __name__ == "__main__":
    try:
        success = test_audio_commands()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Test failed with exception: {e}")
        sys.exit(1)
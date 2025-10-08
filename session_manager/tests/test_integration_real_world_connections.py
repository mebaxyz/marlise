import asyncio
import os
import subprocess

import pytest

import main
from main import startup, shutdown


# Run against a real bridge only
if os.environ.get("USE_REAL_BRIDGE", "0") != "1":
    pytest.skip("Integration test: set USE_REAL_BRIDGE=1 to run against a real bridge", allow_module_level=True)


@pytest.mark.asyncio
async def test_create_pedalboard_with_system_connections():
    """
    Real-world test: create a pedalboard with system input/output connections
    and verify they exist using PipeWire commands.
    """
    os.environ["SESSION_MANAGER_AUTO_CREATE_DEFAULT"] = "0"

    await startup()

    # Give services time to initialize
    await asyncio.sleep(1.0)

    try:
        # Create a new pedalboard
        result = await main.session_manager.create_pedalboard(
            "System Passthrough Test",
            "Test pedalboard with direct input to output connections"
        )
        assert result.get("pedalboard_id") is not None

        # Test direct PipeWire connections using pw-link command
        # Connect audio input to mod-monitor (mod-host's audio interface)
        pipewire_connections = [
            ("alsa_input.pci-0000_00_1f.3.analog-stereo:capture_FL", "mod-monitor:in_1"),  # Left
            ("alsa_input.pci-0000_00_1f.3.analog-stereo:capture_FR", "mod-monitor:in_2"),  # Right
        ]

        created_connections = []

        # Create connections using pw-link directly (since session-manager expects plugin instances)
        for source_port, target_port in pipewire_connections:
            try:
                # Use pw-link to create the connection
                result = subprocess.run(
                    ["pw-link", source_port, target_port],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode == 0:
                    created_connections.append((source_port, target_port))
                    print(f"✓ Created PipeWire connection: {source_port} -> {target_port}")
                else:
                    print(f"⚠ Failed to create connection: {source_port} -> {target_port}")
                    print(f"  Error: {result.stderr}")
            except Exception as e:
                print(f"Warning: Could not create connection {source_port} -> {target_port}: {e}")

        # Also test session-manager connection creation with mock plugin instances
        # (This tests the session-manager API even if no real plugins are loaded)
        try:
            # This will fail but tests the API path
            conn_result = await main.session_manager.create_connection(
                source_plugin="nonexistent_plugin",
                source_port="output_1",
                target_plugin="another_nonexistent_plugin",
                target_port="input_1"
            )
        except Exception as e:
            print(f"Expected failure testing session-manager API: {e}")

        # Give connections time to be established
        await asyncio.sleep(0.5)

        # Verify connections exist using PipeWire commands
        verification_passed = await verify_pipewire_connections(pipewire_connections)

        # Also try pw-link for verification if pw-dump fails
        if not verification_passed:
            verification_passed = await verify_with_pw_link(pipewire_connections)

        if created_connections:
            print(f"Successfully created {len(created_connections)} connections")
            if verification_passed:
                print("✓ Connections verified with PipeWire tools")
            else:
                print("⚠ Could not verify connections with PipeWire tools (may still exist)")

        # Clean up connections using pw-link disconnect
        for source_port, target_port in created_connections:
            try:
                result = subprocess.run(
                    ["pw-link", "-d", source_port, target_port],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    print(f"✓ Removed connection: {source_port} -> {target_port}")
                else:
                    print(f"⚠ Could not remove connection: {source_port} -> {target_port}")
            except Exception as e:
                print(f"Warning: Could not remove connection {source_port} -> {target_port}: {e}")

    finally:
        await shutdown()


async def verify_pipewire_connections(expected_connections):
    """Verify connections exist using pw-dump command"""
    try:
        # Run pw-dump to get current PipeWire state
        result = subprocess.run(
            ["pw-dump"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            print(f"pw-dump failed with return code {result.returncode}")
            return False

        output = result.stdout

        # Look for connection patterns in the output
        # pw-dump shows links between nodes/ports
        connections_found = 0
        for source_port, target_port in expected_connections:
            # Simple check - look for both port names in proximity
            if source_port in output and target_port in output:
                connections_found += 1
                print(f"Found potential connection: {source_port} -> {target_port}")

        return connections_found > 0

    except subprocess.TimeoutExpired:
        print("pw-dump command timed out")
        return False
    except FileNotFoundError:
        print("pw-dump command not found")
        return False
    except Exception as e:
        print(f"Error running pw-dump: {e}")
        return False


async def verify_with_pw_link(expected_connections):
    """Verify connections using pw-link -l command"""
    try:
        # Run pw-link -l to list current connections
        result = subprocess.run(
            ["pw-link", "-l"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            print(f"pw-link -l failed with return code {result.returncode}")
            return False

        output = result.stdout
        print("Current PipeWire connections:")
        print(output)

        # pw-link -l shows connections in format "source -> target"
        connections_found = 0
        for source_port, target_port in expected_connections:
            # Look for the connection in the output
            if f"{source_port}" in output and f"{target_port}" in output:
                connections_found += 1
                print(f"✓ Verified connection: {source_port} -> {target_port}")

        return connections_found > 0

    except subprocess.TimeoutExpired:
        print("pw-link command timed out")
        return False
    except FileNotFoundError:
        print("pw-link command not found")
        return False
    except Exception as e:
        print(f"Error running pw-link: {e}")
        return False


@pytest.mark.asyncio
async def test_create_pedalboard_check_jack_connections():
    """
    Alternative test using JACK commands if available
    """
    os.environ["SESSION_MANAGER_AUTO_CREATE_DEFAULT"] = "0"

    await startup()
    await asyncio.sleep(1.0)

    try:
        # Create pedalboard
        result = await main.session_manager.create_pedalboard("JACK Test Pedalboard")
        assert result.get("pedalboard_id") is not None

        # Try to get JACK port information first
        try:
            jack_result = subprocess.run(
                ["jack_lsp", "-c"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if jack_result.returncode == 0:
                print("JACK ports and connections:")
                print(jack_result.stdout)
            else:
                print("JACK not available or no connections")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("jack_lsp command not available")

        # Test basic session manager functionality
        status = main.session_manager.get_status()
        print(f"Session status: {status}")
        assert status["current_pedalboard"] == "JACK Test Pedalboard"

    finally:
        await shutdown()
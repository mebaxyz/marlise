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
async def test_complete_pedalboard_workflow():
    """
    Complete real-world test: Create pedalboard, set up audio routing, verify with PipeWire
    """
    os.environ["SESSION_MANAGER_AUTO_CREATE_DEFAULT"] = "0"

    print("\n=== Starting Complete Pedalboard Workflow Test ===")
    
    await startup()
    await asyncio.sleep(1.5)  # Give more time for plugin scanning

    try:
        # 1. Check initial system state
        print("\n1. Checking initial system state...")
        print("Available plugins:")
        plugins = await main.plugin_manager.get_available_plugins()
        print(f"   Found {len(plugins)} plugins")
        
        if plugins:
            for i, (uri, info) in enumerate(list(plugins.items())[:3]):
                print(f"   - {uri}")
                if i >= 2:  # Show max 3
                    break
            if len(plugins) > 3:
                print(f"   ... and {len(plugins) - 3} more")
        
        # 2. Create a new pedalboard
        print("\n2. Creating pedalboard...")
        result = await main.session_manager.create_pedalboard(
            "Real World Test Pedalboard", 
            "Integration test with real audio routing"
        )
        pedalboard_id = result.get("pedalboard_id")
        print(f"   Created pedalboard: {pedalboard_id}")
        assert pedalboard_id is not None

        # 3. Show current session state
        print("\n3. Session state after pedalboard creation:")
        status = main.session_manager.get_status()
        print(f"   Current pedalboard: {status['current_pedalboard']}")
        print(f"   Loaded plugins: {status['loaded_plugins']}")
        print(f"   Active connections: {status['active_connections']}")

        # 4. Test audio routing with PipeWire (real hardware connections)
        print("\n4. Testing audio routing...")
        
        # Show current PipeWire state
        print("   Current PipeWire connections:")
        try:
            result = subprocess.run(["pw-link", "-l"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines[:10]:  # Show first 10 lines
                    print(f"     {line}")
                if len(lines) > 10:
                    print(f"     ... and {len(lines) - 10} more lines")
            else:
                print("     Could not get PipeWire connections")
        except Exception as e:
            print(f"     Error getting PipeWire state: {e}")

        # Create a test connection: audio input -> mod-monitor
        print("   Creating test audio connection...")
        test_connections = []
        
        try:
            # Connect system audio input to mod-host input
            source = "alsa_input.pci-0000_00_1f.3.analog-stereo:capture_FL"
            target = "mod-monitor:in_1" 
            
            result = subprocess.run(
                ["pw-link", source, target],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0:
                test_connections.append((source, target))
                print(f"   ✓ Connected: {source} -> {target}")
                
                # Verify connection exists
                await asyncio.sleep(0.2)
                verify_result = subprocess.run(["pw-link", "-l"], capture_output=True, text=True)
                if verify_result.returncode == 0 and source in verify_result.stdout and target in verify_result.stdout:
                    print("   ✓ Connection verified in PipeWire")
                else:
                    print("   ⚠ Connection not found in PipeWire output")
            else:
                print(f"   ⚠ Failed to create connection: {result.stderr}")
                
        except Exception as e:
            print(f"   Error creating test connection: {e}")

        # 5. Test session-manager connection API (even with no plugins loaded)
        print("\n5. Testing session-manager connection API...")
        try:
            # This should fail gracefully since we don't have loaded plugin instances
            conn_result = await main.session_manager.create_connection(
                source_plugin="fake_plugin_1",
                source_port="output_1",
                target_plugin="fake_plugin_2", 
                target_port="input_1"
            )
            print("   Unexpected: connection creation succeeded")
        except Exception as e:
            print(f"   Expected API failure: {e}")

        # 6. Final state check
        print("\n6. Final state verification...")
        final_status = main.session_manager.get_status()
        print(f"   Final pedalboard: {final_status['current_pedalboard']}")
        print(f"   Final loaded plugins: {final_status['loaded_plugins']}")
        print(f"   Final connections: {final_status['active_connections']}")

        # Cleanup test connections
        print("\n7. Cleaning up test connections...")
        for source, target in test_connections:
            try:
                subprocess.run(["pw-link", "-d", source, target], 
                             capture_output=True, timeout=5)
                print(f"   ✓ Removed: {source} -> {target}")
            except Exception as e:
                print(f"   Warning cleaning up {source} -> {target}: {e}")

        print("\n=== Test completed successfully ===")

    finally:
        await shutdown()


if __name__ == "__main__":
    # Allow running this test directly
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "direct":
        os.environ["USE_REAL_BRIDGE"] = "1"
        asyncio.run(test_complete_pedalboard_workflow())
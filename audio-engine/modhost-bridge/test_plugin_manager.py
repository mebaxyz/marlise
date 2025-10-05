#!/usr/bin/env python3
"""
Simple test script for the mod-host-bridge plugin manager API.
This script tests the plugin management functionality using ZeroMQ.
"""

import zmq
import json
import time
import sys

def test_plugin_manager():
    """Test the plugin manager API"""

    # Create ZeroMQ context
    context = zmq.Context()

    # Create REQ socket for commands
    req_socket = context.socket(zmq.REQ)
    req_socket.connect("tcp://127.0.0.1:6000")

    # Create SUB socket for events
    sub_socket = context.socket(zmq.SUB)
    sub_socket.connect("tcp://127.0.0.1:6001")
    sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")

    print("Testing mod-host-bridge plugin manager API...")

    # Test 1: Get available plugins
    print("\n1. Testing get_available_plugins...")
    request = {
        "action": "plugin",
        "method": "get_available_plugins"
    }

    req_socket.send_json(request)
    response = req_socket.recv_json()
    print(f"Response: {json.dumps(response, indent=2)}")

    if "plugins" in response:
        print(f"✓ Found {len(response['plugins'])} available plugins")
    else:
        print("✗ No plugins found in response")
        return False

    # Test 2: Load a plugin
    print("\n2. Testing load_plugin...")
    plugin_uri = list(response["plugins"].keys())[0]  # Use first available plugin
    request = {
        "action": "plugin",
        "method": "load_plugin",
        "uri": plugin_uri,
        "x": 100.0,
        "y": 200.0
    }

    req_socket.send_json(request)
    response = req_socket.recv_json()
    print(f"Response: {json.dumps(response, indent=2)}")

    if "instance_id" in response:
        instance_id = response["instance_id"]
        print(f"✓ Plugin loaded with instance_id: {instance_id}")
    else:
        print("✗ Failed to load plugin")
        return False

    # Check for plugin_loaded event
    print("Checking for plugin_loaded event...")
    try:
        sub_socket.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second timeout
        event = sub_socket.recv_json()
        print(f"Event received: {json.dumps(event, indent=2)}")
        if event.get("type") == "plugin_loaded":
            print("✓ plugin_loaded event received")
        else:
            print("✗ Expected plugin_loaded event")
    except zmq.Again:
        print("⚠ No event received (mod-host may not be running)")

    # Test 3: List instances
    print("\n3. Testing list_instances...")
    request = {
        "action": "plugin",
        "method": "list_instances"
    }

    req_socket.send_json(request)
    response = req_socket.recv_json()
    print(f"Response: {json.dumps(response, indent=2)}")

    if "instances" in response and instance_id in response["instances"]:
        print(f"✓ Instance {instance_id} found in list")
    else:
        print("✗ Instance not found in list")
        return False

    # Test 4: Get plugin info
    print("\n4. Testing get_plugin_info...")
    request = {
        "action": "plugin",
        "method": "get_plugin_info",
        "instance_id": instance_id
    }

    req_socket.send_json(request)
    response = req_socket.recv_json()
    print(f"Response: {json.dumps(response, indent=2)}")

    if "plugin" in response:
        print("✓ Plugin info retrieved")
    else:
        print("✗ Failed to get plugin info")

    # Test 5: Set parameter
    print("\n5. Testing set_parameter...")
    # Get first parameter from plugin info
    plugin_info = response.get("plugin", {})
    parameters = plugin_info.get("parameters", {})
    if parameters:
        param_name = list(parameters.keys())[0]
        request = {
            "action": "plugin",
            "method": "set_parameter",
            "instance_id": instance_id,
            "parameter": param_name,
            "value": 0.8
        }

        req_socket.send_json(request)
        response = req_socket.recv_json()
        print(f"Response: {json.dumps(response, indent=2)}")

        if response.get("status") == "ok":
            print(f"✓ Parameter {param_name} set successfully")
        else:
            print("✗ Failed to set parameter")
    else:
        print("⚠ No parameters to test")

    # Test 6: Get parameter
    print("\n6. Testing get_parameter...")
    if 'param_name' in locals():
        request = {
            "action": "plugin",
            "method": "get_parameter",
            "instance_id": instance_id,
            "parameter": param_name
        }

        req_socket.send_json(request)
        response = req_socket.recv_json()
        print(f"Response: {json.dumps(response, indent=2)}")

        if "value" in response:
            print(f"✓ Parameter {param_name} value: {response['value']}")
        else:
            print("✗ Failed to get parameter")

    # Test 7: Unload plugin
    print("\n7. Testing unload_plugin...")
    request = {
        "action": "plugin",
        "method": "unload_plugin",
        "instance_id": instance_id
    }

    req_socket.send_json(request)
    response = req_socket.recv_json()
    print(f"Response: {json.dumps(response, indent=2)}")

    if response.get("status") == "ok":
        print("✓ Plugin unloaded successfully")
    else:
        print("✗ Failed to unload plugin")

    # Check for plugin_unloaded event
    print("Checking for plugin_unloaded event...")
    try:
        sub_socket.setsockopt(zmq.RCVTIMEO, 1000)  # 1 second timeout
        event = sub_socket.recv_json()
        print(f"Event received: {json.dumps(event, indent=2)}")
        if event.get("type") == "plugin_unloaded":
            print("✓ plugin_unloaded event received")
        else:
            print("✗ Expected plugin_unloaded event")
    except zmq.Again:
        print("⚠ No event received (mod-host may not be running)")

    # Test 8: Clear all
    print("\n8. Testing clear_all...")
    request = {
        "action": "plugin",
        "method": "clear_all"
    }

    req_socket.send_json(request)
    response = req_socket.recv_json()
    print(f"Response: {json.dumps(response, indent=2)}")

    if response.get("status") == "ok":
        print("✓ All plugins cleared")
    else:
        print("✗ Failed to clear all plugins")

    # Cleanup
    req_socket.close()
    sub_socket.close()
    context.term()

    print("\n✓ All plugin manager tests completed!")
    return True

if __name__ == "__main__":
    try:
        success = test_plugin_manager()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Test failed with exception: {e}")
        sys.exit(1)
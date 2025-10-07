#!/bin/bash

# Session Manager Startup Script
# This script starts the session manager with proper environment configuration

set -e

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration
export SERVICE_NAME="${SERVICE_NAME:-session_manager}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"

# Modhost-bridge connection
export MODHOST_BRIDGE_ENDPOINT="${MODHOST_BRIDGE_ENDPOINT:-tcp://127.0.0.1:6000}"
export MODHOST_BRIDGE_TIMEOUT="${MODHOST_BRIDGE_TIMEOUT:-5.0}"

# ServiceBus configuration (ZeroMQ implementation)
export SERVICEBUS_IMPL="${SERVICEBUS_IMPL:-zeromq}"

echo "Starting $SERVICE_NAME..."
echo "Configuration:"
echo "  Service Name: $SERVICE_NAME"
echo "  Log Level: $LOG_LEVEL"
echo "  Bridge Endpoint: $MODHOST_BRIDGE_ENDPOINT"
echo "  Bridge Timeout: $MODHOST_BRIDGE_TIMEOUT"
echo "  ServiceBus Implementation: $SERVICEBUS_IMPL"

# Set Python path to include libraries
export PYTHONPATH="$PROJECT_ROOT/mod-ui/libraries:$SCRIPT_DIR:$PYTHONPATH"

# Change to session manager directory
cd "$SCRIPT_DIR"

# Start the session manager
exec python3 main.py "$@"
#!/usr/bin/env bash
# Quick health check for all Marlise services

set -e

echo "🏥 Marlise Health Check"
echo "======================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_service() {
    local name=$1
    local url=$2
    local expected=$3
    
    printf "%-30s" "$name"
    
    if response=$(curl -s -f "$url" 2>&1); then
        if echo "$response" | grep -q "$expected"; then
            echo -e "${GREEN}✓ OK${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠ Running (unexpected response)${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ Failed${NC}"
        return 1
    fi
}

check_port() {
    local name=$1
    local port=$2
    
    printf "%-30s" "$name"
    
    if nc -z localhost "$port" 2>/dev/null; then
        echo -e "${GREEN}✓ Listening on :$port${NC}"
        return 0
    else
        echo -e "${RED}✗ Not listening on :$port${NC}"
        return 1
    fi
}

echo "HTTP Services:"
echo "--------------"
check_service "FastAPI (Client Interface)" "http://localhost:8080/health" "client_interface" || true
check_service "Tornado (Web Client)" "http://localhost:8888/css/dashboard.css" "body" || true

echo ""
echo "ZeroMQ Ports:"
echo "-------------"
check_port "Session Manager RPC" 5718 || true
check_port "Session Manager PUB" 6718 || true
check_port "Session Manager SUB" 7718 || true
check_port "Modhost Bridge" 6000 || true

echo ""
echo "Audio Services:"
echo "---------------"
check_port "mod-host Command" 5555 || true
check_port "mod-host Feedback" 5556 || true

echo ""
echo "Docker Services:"
echo "----------------"
if command -v docker &> /dev/null; then
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "marlise\|tornado\|fastapi"; then
        docker ps --filter "name=marlise" --filter "name=tornado" --filter "name=fastapi" --format "table {{.Names}}\t{{.Status}}"
    else
        echo "No Docker containers running"
    fi
else
    echo "Docker not available"
fi

echo ""
echo "Process Check:"
echo "--------------"
ps aux | grep -E "mod-host|modhost-bridge|session_manager|uvicorn|tornado" | grep -v grep || echo "No processes found"

echo ""
echo "Recent Errors (last 10 lines):"
echo "-------------------------------"
if [ -d "logs" ]; then
    for log in logs/*.log; do
        if [ -f "$log" ]; then
            errors=$(tail -100 "$log" | grep -i "error\|exception\|failed" | tail -5 || true)
            if [ -n "$errors" ]; then
                echo "📄 $(basename "$log"):"
                echo "$errors"
                echo ""
            fi
        fi
    done
else
    echo "No logs directory found"
fi

echo ""
echo "✅ Health check complete"

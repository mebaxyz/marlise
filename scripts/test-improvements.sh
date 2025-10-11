#!/usr/bin/env bash
# Quick test script to verify implemented improvements

set -e

echo "🧪 Testing Marlise Improvements"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if services are running
echo "1️⃣  Checking if services are running..."
if pgrep -f "mod-host" > /dev/null; then
    echo -e "${GREEN}✓ mod-host is running${NC}"
else
    echo -e "${YELLOW}⚠ mod-host not running (start with ./scripts/start-service.sh)${NC}"
fi

if pgrep -f "modhost-bridge" > /dev/null; then
    echo -e "${GREEN}✓ modhost-bridge is running${NC}"
else
    echo -e "${YELLOW}⚠ modhost-bridge not running${NC}"
fi

if pgrep -f "session_manager" > /dev/null; then
    echo -e "${GREEN}✓ session-manager is running${NC}"
else
    echo -e "${YELLOW}⚠ session-manager not running${NC}"
fi

if pgrep -f "uvicorn.*main:app" > /dev/null; then
    echo -e "${GREEN}✓ client-interface (FastAPI) is running${NC}"
else
    echo -e "${YELLOW}⚠ client-interface not running${NC}"
fi

echo ""
echo "2️⃣  Testing new dependencies..."

# Test uvloop
if python3 -c "import uvloop" 2>/dev/null; then
    echo -e "${GREEN}✓ uvloop installed${NC}"
else
    echo -e "${RED}✗ uvloop not installed - run: pip install uvloop${NC}"
fi

# Test psutil
if python3 -c "import psutil" 2>/dev/null; then
    echo -e "${GREEN}✓ psutil installed${NC}"
else
    echo -e "${RED}✗ psutil not installed - run: pip install psutil${NC}"
fi

echo ""
echo "3️⃣  Testing new endpoints (if services are running)..."

# Test basic health
if curl -f -s http://localhost:8080/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Basic health check works${NC}"
else
    echo -e "${YELLOW}⚠ Basic health check failed (is client-interface running?)${NC}"
fi

# Test deep health
if curl -f -s http://localhost:8080/health/deep > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Deep health check endpoint works${NC}"
    # Show actual status
    response=$(curl -s http://localhost:8080/health/deep)
    echo "   Response: $response"
else
    echo -e "${YELLOW}⚠ Deep health check not accessible${NC}"
fi

# Test metrics
if curl -f -s http://localhost:8080/api/metrics > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Metrics endpoint works${NC}"
else
    echo -e "${YELLOW}⚠ Metrics endpoint not accessible${NC}"
fi

echo ""
echo "4️⃣  Checking systemd deployment files..."

if [ -f "deployment/systemd/marlise-mod-host@.service" ]; then
    echo -e "${GREEN}✓ Systemd service files created${NC}"
    echo "   Found $(ls deployment/systemd/*.service 2>/dev/null | wc -l) service files"
else
    echo -e "${RED}✗ Systemd files not found${NC}"
fi

if [ -x "deployment/install-systemd.sh" ]; then
    echo -e "${GREEN}✓ Systemd installer is executable${NC}"
else
    echo -e "${YELLOW}⚠ Systemd installer not executable${NC}"
fi

echo ""
echo "5️⃣  Checking helper scripts..."

for script in health-check.sh logs-tail.sh add-timeouts.py; do
    if [ -f "scripts/$script" ]; then
        echo -e "${GREEN}✓ scripts/$script exists${NC}"
    else
        echo -e "${RED}✗ scripts/$script missing${NC}"
    fi
done

echo ""
echo "6️⃣  Checking documentation..."

for doc in IMPLEMENTATION_SUMMARY.md QUICK_IMPROVEMENTS.md ANALYSIS_SUMMARY.md deployment/README.md; do
    if [ -f "$doc" ]; then
        echo -e "${GREEN}✓ $doc created${NC}"
    else
        echo -e "${RED}✗ $doc missing${NC}"
    fi
done

echo ""
echo "7️⃣  Verifying timeout additions..."

# Count timeouts in router files
timeout_count=$(grep -r "timeout=5.0" client-interface/web_api/api/routers/*.py 2>/dev/null | wc -l)
if [ "$timeout_count" -gt 0 ]; then
    echo -e "${GREEN}✓ Found $timeout_count timeout parameters in routers${NC}"
else
    echo -e "${YELLOW}⚠ No timeout parameters found (run scripts/add-timeouts.py)${NC}"
fi

echo ""
echo "8️⃣  Checking bridge auto-reconnect implementation..."

if grep -q "_auto_reconnect_loop" session_manager/infrastructure/bridge_client.py; then
    echo -e "${GREEN}✓ Bridge auto-reconnect implemented${NC}"
else
    echo -e "${RED}✗ Bridge auto-reconnect not found${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Test Summary Complete"
echo ""
echo "📋 Next Steps:"
echo "   1. Install dependencies: pip install -r */requirements.txt"
echo "   2. Restart services: ./scripts/start-service.sh"
echo "   3. Run full health check: ./scripts/health-check.sh"
echo "   4. Test endpoints manually:"
echo "      - curl http://localhost:8080/health/deep"
echo "      - curl http://localhost:8080/api/metrics"
echo "   5. Consider installing systemd services: cd deployment && sudo ./install-systemd.sh"
echo ""

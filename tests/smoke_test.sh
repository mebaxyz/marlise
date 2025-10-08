#!/bin/bash
# Simple smoke test for Python components

set -e

echo "🔍 Marlise Python Components Smoke Test"
echo "======================================"

cd "$(dirname "$0")/.."

echo "Testing Python imports..."

# Test session_manager import
if python3 -c "import sys; sys.path.append('session_manager'); import session_manager.main" 2>/dev/null; then
    echo "✅ session_manager imports successfully"
else
    echo "❌ session_manager import failed"
fi

# Test client interface import
if python3 -c "import sys; sys.path.append('client-interface/web_api/api'); import main" 2>/dev/null; then
    echo "✅ client-interface imports successfully"
else
    echo "❌ client-interface import failed"
fi

echo -e "\nTesting handler imports..."

# Test handlers
if python3 -c "import sys; sys.path.append('session_manager'); from session_manager.handlers.system_handlers import SystemHandlers" 2>/dev/null; then
    echo "✅ SystemHandlers imports successfully"
else
    echo "❌ SystemHandlers import failed"
fi

if python3 -c "import sys; sys.path.append('session_manager'); from session_manager.handlers.jack_handlers import JackHandlers" 2>/dev/null; then
    echo "✅ JackHandlers imports successfully"
else
    echo "❌ JackHandlers import failed"
fi

echo -e "\nTesting integration test framework..."

if python3 -c "import sys; sys.path.append('tests'); import integration.test_framework" 2>/dev/null; then
    echo "✅ Test framework imports successfully"
else
    echo "❌ Test framework import failed"
fi

echo -e "\n🎉 Python components smoke test completed!"
echo "Note: This test only verifies imports, not full functionality"
echo "For full testing, use the Docker-based integration tests when ready."
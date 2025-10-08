#!/bin/bash
# Verify test platform setup

echo "🔧 Marlise Test Platform Setup Verification"
echo "==========================================="

cd "$(dirname "$0")"

ERRORS=0

check_file() {
    if [ -f "$1" ]; then
        echo "✅ $1"
    else
        echo "❌ $1 (missing)"
        ((ERRORS++))
    fi
}

check_executable() {
    if [ -x "$1" ]; then
        echo "✅ $1 (executable)"
    else
        echo "❌ $1 (not executable)"
        ((ERRORS++))
    fi
}

echo "Checking test files..."
check_file "README.md"
check_file "pytest.ini"
check_file "Makefile"
check_executable "run_integration_tests.sh"
check_executable "health_check.sh"

echo -e "\nChecking Docker configuration..."
check_file "docker/Dockerfile.test-environment"
check_file "docker/docker-compose.test.yml"
check_file "docker/requirements-test.txt"
check_file "docker/supervisord-test.conf"
check_file "docker/test-plugins.txt"

echo -e "\nChecking integration tests..."
check_file "integration/test_framework.py"
check_file "integration/test_01_modhost_bridge.py"
check_file "integration/test_02_session_manager_direct.py"
check_file "integration/test_03_session_manager_zmq.py"
check_file "integration/test_04_client_api_http.py"

echo -e "\nChecking external dependencies..."
if command -v docker >/dev/null 2>&1; then
    echo "✅ docker"
else
    echo "❌ docker (not found in PATH)"
    ((ERRORS++))
fi

if command -v docker-compose >/dev/null 2>&1; then
    echo "✅ docker-compose"
elif docker compose version >/dev/null 2>&1; then
    echo "✅ docker compose (v2 plugin)"
else
    echo "❌ docker-compose or docker compose (not found)"
    ((ERRORS++))
fi

echo -e "\nCreating required directories..."
mkdir -p test-results logs docker/logs
echo "✅ Created test-results/, logs/, docker/logs/"

echo -e "\n📊 Setup Summary"
echo "==============="
if [ $ERRORS -eq 0 ]; then
    echo "🎉 Test platform setup is complete and ready!"
    echo ""
    echo "Next steps:"
    echo "1. Run health check: ./health_check.sh"
    echo "2. Run tests: ./run_integration_tests.sh"
    echo "3. Or use Make: make test"
    echo ""
    echo "See README.md for detailed usage instructions."
else
    echo "⚠️  Found $ERRORS issues that need to be resolved."
    exit 1
fi
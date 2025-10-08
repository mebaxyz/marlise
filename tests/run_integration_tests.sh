#!/bin/bash
# Marlise Integration Test Runner
# Runs the complete test suite at all levels

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🧪 Marlise Integration Test Suite"
echo "================================="
echo

# Configuration
COMPOSE_FILE="docker/docker-compose.test.yml"
TEST_RESULTS_DIR="./test-results"
LOGS_DIR="./logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Cleanup function
cleanup() {
    print_status "Cleaning up test environment..."
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" down -v 2>/dev/null || true
    docker system prune -f 2>/dev/null || true
}

# Trap cleanup on exit
trap cleanup EXIT

# Create directories
mkdir -p "$TEST_RESULTS_DIR" "$LOGS_DIR"

# Parse command line arguments
RUN_LEVEL=""
BUILD_IMAGES=true
SHOW_LOGS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --level1|--modhost-bridge)
            RUN_LEVEL="level1"
            shift
            ;;
        --level2|--session-direct)
            RUN_LEVEL="level2"
            shift
            ;;
        --level3|--session-zmq)
            RUN_LEVEL="level3"
            shift
            ;;
        --level4|--client-api)
            RUN_LEVEL="level4"
            shift
            ;;
        --no-build)
            BUILD_IMAGES=false
            shift
            ;;
        --show-logs)
            SHOW_LOGS=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo
            echo "OPTIONS:"
            echo "  --level1, --modhost-bridge    Run only Level 1 tests (mod-host bridge)"
            echo "  --level2, --session-direct    Run only Level 2 tests (session manager direct)"
            echo "  --level3, --session-zmq       Run only Level 3 tests (session manager ZMQ)"
            echo "  --level4, --client-api        Run only Level 4 tests (client API HTTP)"
            echo "  --no-build                    Skip Docker image building"
            echo "  --show-logs                   Show service logs on failure"
            echo "  --help                        Show this help"
            echo
            echo "If no level is specified, all levels will be run."
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check prerequisites
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "docker-compose or docker compose is not installed or not in PATH"
    exit 1
fi

# Determine which docker compose command to use
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

# Build images if requested
if [ "$BUILD_IMAGES" = true ]; then
    print_status "Building test environment Docker image..."
    if ! $DOCKER_COMPOSE -f "$COMPOSE_FILE" build; then
        print_error "Failed to build Docker images"
        exit 1
    fi
    print_success "Docker images built successfully"
fi

# Start test environment
print_status "Starting Marlise test environment..."
if ! $DOCKER_COMPOSE -f "$COMPOSE_FILE" up -d marlise-test-env; then
    print_error "Failed to start test environment"
    exit 1
fi

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 30

# Check if environment is healthy
print_status "Checking service health..."
if ! $DOCKER_COMPOSE -f "$COMPOSE_FILE" ps marlise-test-env | grep -q "healthy"; then
    print_warning "Service health check failed, checking logs..."
    
    if [ "$SHOW_LOGS" = true ]; then
        print_status "Service logs:"
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" logs marlise-test-env
    fi
    
    # Continue with tests anyway, services might still be functional
    print_warning "Proceeding with tests despite health check failure"
fi

print_success "Test environment is ready"

# Run tests based on level
run_tests() {
    local level=$1
    local test_file=$2
    local description=$3
    
    print_status "Running $description..."
    
    local test_cmd="python3 -m pytest integration/$test_file -v --tb=short"
    if [ -n "$level" ]; then
        test_cmd="$test_cmd -m $level"
    fi
    
    if $DOCKER_COMPOSE -f "$COMPOSE_FILE" run --rm marlise-test-runner bash -c "$test_cmd"; then
        print_success "$description completed successfully"
        return 0
    else
        print_error "$description failed"
        if [ "$SHOW_LOGS" = true ]; then
            print_status "Service logs for debugging:"
            $DOCKER_COMPOSE -f "$COMPOSE_FILE" logs marlise-test-env
        fi
        return 1
    fi
}

# Execute test levels
TEST_FAILURES=0

if [ -z "$RUN_LEVEL" ]; then
    # Run all levels
    print_status "Running complete test suite (all levels)..."
    echo
    
    run_tests "level1" "test_01_modhost_bridge.py" "Level 1: Mod-Host Bridge Direct Tests" || ((TEST_FAILURES++))
    echo
    
    run_tests "level2" "test_02_session_manager_direct.py" "Level 2: Session Manager Direct Tests" || ((TEST_FAILURES++))
    echo
    
    run_tests "level3" "test_03_session_manager_zmq.py" "Level 3: Session Manager ZMQ Tests" || ((TEST_FAILURES++))
    echo
    
    run_tests "level4" "test_04_client_api_http.py" "Level 4: Client API HTTP Tests" || ((TEST_FAILURES++))
    echo
    
else
    # Run specific level
    case $RUN_LEVEL in
        level1)
            run_tests "level1" "test_01_modhost_bridge.py" "Level 1: Mod-Host Bridge Direct Tests" || ((TEST_FAILURES++))
            ;;
        level2)
            run_tests "level2" "test_02_session_manager_direct.py" "Level 2: Session Manager Direct Tests" || ((TEST_FAILURES++))
            ;;
        level3)
            run_tests "level3" "test_03_session_manager_zmq.py" "Level 3: Session Manager ZMQ Tests" || ((TEST_FAILURES++))
            ;;
        level4)
            run_tests "level4" "test_04_client_api_http.py" "Level 4: Client API HTTP Tests" || ((TEST_FAILURES++))
            ;;
    esac
fi

# Copy test results
print_status "Copying test results..."
docker cp marlise-test-runner:/tmp/test-results/. "$TEST_RESULTS_DIR/" 2>/dev/null || true

# Final summary
echo
echo "🏁 Test Summary"
echo "============="
if [ $TEST_FAILURES -eq 0 ]; then
    print_success "All tests passed! 🎉"
    echo
    print_status "Test results are available in: $TEST_RESULTS_DIR"
    print_status "Service logs are available in: $LOGS_DIR"
    exit 0
else
    print_error "$TEST_FAILURES test level(s) failed"
    echo
    print_status "Check test results in: $TEST_RESULTS_DIR"
    print_status "Check service logs in: $LOGS_DIR"
    exit 1
fi
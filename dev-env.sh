#!/bin/bash
# Development environment management script for Marlise web interfaces

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose.dev.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
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

# Functions
build_services() {
    print_status "Building Docker images..."
    docker compose -f "$COMPOSE_FILE" build
    print_success "Images built successfully"
}

start_services() {
    print_status "Starting Marlise development services..."
    docker compose -f "$COMPOSE_FILE" up -d
    
    print_status "Waiting for services to be ready..."
    sleep 5
    
    # Check if services are healthy
    if docker compose -f "$COMPOSE_FILE" ps | grep -q "Up (healthy)"; then
        print_success "Services started successfully!"
        print_status "🌐 Tornado Web Client: http://localhost:8888"
        print_status "🔧 FastAPI Interface: http://localhost:8080"
        print_status "📊 FastAPI Docs: http://localhost:8080/docs"
    else
        print_warning "Services started but may not be fully ready yet"
        print_status "Check logs with: $0 logs"
    fi
}

stop_services() {
    print_status "Stopping Marlise development services..."
    docker compose -f "$COMPOSE_FILE" down
    print_success "Services stopped"
}

restart_services() {
    print_status "Restarting Marlise development services..."
    docker compose -f "$COMPOSE_FILE" restart
    print_success "Services restarted"
}

show_logs() {
    local service="$1"
    if [ -n "$service" ]; then
        print_status "Showing logs for $service..."
        docker compose -f "$COMPOSE_FILE" logs -f "$service"
    else
        print_status "Showing logs for all services..."
        docker compose -f "$COMPOSE_FILE" logs -f
    fi
}

show_status() {
    print_status "Service status:"
    docker compose -f "$COMPOSE_FILE" ps
    
    echo ""
    print_status "Service health checks:"
    
    # Test Tornado Web Client
    if curl -s -f "http://localhost:8888/css/dashboard.css" > /dev/null 2>&1; then
        print_success "✅ Tornado Web Client (port 8888) - OK"
    else
        print_error "❌ Tornado Web Client (port 8888) - Failed"
    fi
    
    # Test FastAPI Client Interface
    if curl -s -f "http://localhost:8080/health" > /dev/null 2>&1; then
        print_success "✅ FastAPI Client Interface (port 8080) - OK"
    else
        print_error "❌ FastAPI Client Interface (port 8080) - Failed"
    fi
    
    # Test API Proxy
    response_code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8888/api/health" 2>/dev/null || echo "000")
    if [ "$response_code" = "200" ]; then
        print_success "✅ API Proxy (8888 → 8080) - OK"
    elif [ "$response_code" = "502" ]; then
        print_warning "⚠️  API Proxy working but FastAPI not ready (502)"
    else
        print_error "❌ API Proxy - Failed (HTTP $response_code)"
    fi
}

cleanup() {
    print_status "Cleaning up Docker resources..."
    docker compose -f "$COMPOSE_FILE" down --rmi local --volumes --remove-orphans
    print_success "Cleanup completed"
}

show_help() {
    echo "Marlise Development Environment Manager"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  build      Build Docker images"
    echo "  start      Start all services (build if needed)"
    echo "  stop       Stop all services"
    echo "  restart    Restart all services"
    echo "  status     Show service status and health"
    echo "  logs       Show logs for all services"
    echo "  logs SERVICE Show logs for specific service"
    echo "  cleanup    Stop services and remove images/volumes"
    echo "  help       Show this help message"
    echo ""
    echo "Services:"
    echo "  - tornado-web-client     (port 8888)"
    echo "  - fastapi-client-interface (port 8080)"
    echo ""
    echo "Development URLs:"
    echo "  - Web UI:      http://localhost:8888"
    echo "  - API Direct:  http://localhost:8080"
    echo "  - API Docs:    http://localhost:8080/docs"
}

# Main command handling
case "${1:-help}" in
    "build")
        build_services
        ;;
    "start")
        build_services
        start_services
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        restart_services
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs "$2"
        ;;
    "cleanup")
        cleanup
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
#!/bin/bash

# ContextProvider Deployment Script
# This script deploys the ContextProvider application using Docker Compose

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command_exists docker-compose; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Setup environment
setup_environment() {
    print_status "Setting up environment..."
    
    # Copy environment file if it doesn't exist
    if [ ! -f .env ]; then
        if [ -f .env.production ]; then
            cp .env.production .env
            print_warning "Copied .env.production to .env. Please update the values before proceeding."
            print_warning "Edit .env file with your actual values:"
            print_warning "  - POSTGRES_PASSWORD"
            print_warning "  - JWT_SECRET_KEY"
            print_warning "  - OPENAI_API_KEY"
            print_warning "  - Domain names in ALLOWED_HOSTS and CORS_ORIGINS"
            read -p "Press Enter after updating .env file..."
        else
            print_error ".env file not found. Please create it from .env.production template."
            exit 1
        fi
    fi
    
    # Create necessary directories
    mkdir -p backend/uploads
    mkdir -p backend/logs
    mkdir -p database
    mkdir -p nginx/ssl
    
    print_success "Environment setup completed"
}

# Build and start services
deploy_services() {
    print_status "Building and starting services..."
    
    # Pull latest images
    print_status "Pulling latest base images..."
    docker-compose pull postgres chromadb
    
    # Build custom images
    print_status "Building application images..."
    docker-compose build --no-cache
    
    # Start services
    print_status "Starting services..."
    docker-compose up -d
    
    print_success "Services started successfully"
}

# Wait for services to be ready
wait_for_services() {
    print_status "Waiting for services to be ready..."
    
    # Wait for PostgreSQL
    print_status "Waiting for PostgreSQL..."
    until docker-compose exec -T postgres pg_isready -U contextuser -d contextprovider; do
        sleep 2
    done
    
    # Wait for ChromaDB
    print_status "Waiting for ChromaDB..."
    until curl -f http://localhost:8001/api/v1/heartbeat >/dev/null 2>&1; do
        sleep 2
    done
    
    # Wait for backend
    print_status "Waiting for backend..."
    until curl -f http://localhost:8000/health >/dev/null 2>&1; do
        sleep 2
    done
    
    # Wait for frontend
    print_status "Waiting for frontend..."
    until curl -f http://localhost/health >/dev/null 2>&1; do
        sleep 2
    done
    
    print_success "All services are ready"
}

# Run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    # Run Alembic migrations
    docker-compose exec backend alembic upgrade head
    
    print_success "Database migrations completed"
}

# Display deployment information
show_deployment_info() {
    print_success "🚀 ContextProvider deployed successfully!"
    echo ""
    echo "📋 Service URLs:"
    echo "  Frontend:    http://localhost"
    echo "  Backend API: http://localhost:8000"
    echo "  PostgreSQL:  localhost:5432"
    echo "  ChromaDB:    http://localhost:8001"
    echo ""
    echo "🔧 Management Commands:"
    echo "  View logs:     docker-compose logs -f"
    echo "  Stop services: docker-compose down"
    echo "  Restart:       docker-compose restart"
    echo "  Shell access:  docker-compose exec backend bash"
    echo ""
    echo "📊 Health Checks:"
    echo "  Frontend:  curl http://localhost/health"
    echo "  Backend:   curl http://localhost:8000/health"
    echo "  ChromaDB:  curl http://localhost:8001/api/v1/heartbeat"
    echo ""
}

# Main deployment function
main() {
    print_status "Starting ContextProvider deployment..."
    
    check_prerequisites
    setup_environment
    deploy_services
    wait_for_services
    run_migrations
    show_deployment_info
    
    print_success "Deployment completed successfully! 🎉"
}

# Handle script arguments
case "${1:-}" in
    "stop")
        print_status "Stopping ContextProvider services..."
        docker-compose down
        print_success "Services stopped"
        ;;
    "restart")
        print_status "Restarting ContextProvider services..."
        docker-compose restart
        print_success "Services restarted"
        ;;
    "logs")
        docker-compose logs -f
        ;;
    "clean")
        print_warning "This will remove all containers and volumes. Are you sure? (y/N)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            docker-compose down -v --remove-orphans
            docker system prune -f
            print_success "Cleanup completed"
        fi
        ;;
    *)
        main
        ;;
esac 
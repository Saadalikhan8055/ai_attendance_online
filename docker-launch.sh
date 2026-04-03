#!/bin/bash

# ==========================================
# AI ATTENDANCE SYSTEM - DOCKER LAUNCHER
# ==========================================
# Usage: ./docker-launch.sh [command]
# Commands:
#   up           Start all containers
#   down         Stop all containers
#   restart      Restart all containers
#   logs         View application logs
#   ps           Show running containers
#   exec         Execute command in app container
#   clean        Remove containers and volumes
#   build        Build Docker images
#   migrate      Run database migrations
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="attendance"
DOCKER_COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"

# Functions
print_header() {
    echo -e "${BLUE}======================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}======================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    print_success "Docker and Docker Compose are installed"
}

check_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        print_warning "Environment file not found: $ENV_FILE"
        print_warning "Creating $ENV_FILE from .env.docker..."
        cp .env.docker "$ENV_FILE"
        print_warning "Please update $ENV_FILE with your configuration"
        print_warning "Then run this script again"
        exit 0
    fi
}

setup() {
    print_header "Setting up Docker environment"
    check_docker
    check_env_file
    
    # Create necessary directories
    mkdir -p logs
    mkdir -p docker/certs
    mkdir -p static/uploads
    
    print_success "Setup completed"
}

build() {
    print_header "Building Docker images"
    docker-compose -f "$DOCKER_COMPOSE_FILE" build
    print_success "Images built successfully"
}

start() {
    print_header "Starting containers"
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    
    # Wait for services to be healthy
    print_warning "Waiting for services to be healthy..."
    sleep 10
    
    # Run migrations
    print_warning "Running database migrations..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T app python db_init.py
    
    print_success "All containers started successfully"
    
    # Display information
    echo ""
    echo -e "${GREEN}Service URLs:${NC}"
    echo "  - Application: http://localhost (or http://your-domain.com)"
    echo "  - PostgreSQL: localhost:5432"
    echo "  - Redis: localhost:6379"
    echo ""
    echo -e "${GREEN}View logs:${NC}"
    echo "  - docker logs attendance_app"
    echo "  - docker logs attendance_nginx"
    echo "  - ./docker-launch.sh logs"
    echo ""
}

stop() {
    print_header "Stopping containers"
    docker-compose -f "$DOCKER_COMPOSE_FILE" down
    print_success "All containers stopped"
}

restart() {
    print_header "Restarting containers"
    docker-compose -f "$DOCKER_COMPOSE_FILE" restart
    print_success "All containers restarted"
}

view_logs() {
    print_header "Application logs (Ctrl+C to exit)"
    docker-compose -f "$DOCKER_COMPOSE_FILE" logs -f app
}

ps_containers() {
    print_header "Running containers"
    docker-compose -f "$DOCKER_COMPOSE_FILE" ps
}

clean() {
    print_header "Cleaning up"
    echo -e "${RED}This will remove all containers, networks, and volumes.${NC}"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" down -v
        print_success "Cleanup completed"
    else
        print_warning "Cleanup cancelled"
    fi
}

health_check() {
    print_header "Health check"
    
    echo "Checking PostgreSQL..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres pg_isready -U attendance_user && \
        print_success "PostgreSQL is running" || print_error "PostgreSQL is not responding"
    
    echo "Checking Redis..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T redis redis-cli -a redis_password ping && \
        print_success "Redis is running" || print_error "Redis is not responding"
    
    echo "Checking Application..."
    curl -s http://localhost:5000/health > /dev/null && \
        print_success "Application is running" || print_error "Application is not responding"
    
    echo "Checking Nginx..."
    curl -s https://localhost/health > /dev/null 2>&1 && \
        print_success "Nginx is running" || print_error "Nginx is not responding"
}

backup() {
    print_header "Backing up database"
    BACKUP_DIR="backups"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql.gz"
    
    mkdir -p "$BACKUP_DIR"
    
    docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres \
        pg_dump -U attendance_user attendance_db | gzip > "$BACKUP_FILE"
    
    print_success "Database backed up to $BACKUP_FILE"
}

restore() {
    if [ -z "$1" ]; then
        print_error "Usage: $0 restore <backup_file>"
        exit 1
    fi
    
    if [ ! -f "$1" ]; then
        print_error "Backup file not found: $1"
        exit 1
    fi
    
    print_header "Restoring database from $1"
    print_warning "This will overwrite the current database. Continue? (y/N)"
    read -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Restore cancelled"
        exit 0
    fi
    
    zcat "$1" | docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres \
        psql -U attendance_user -d attendance_db
    
    print_success "Database restored successfully"
}

shell() {
    print_header "Opening shell in app container"
    docker-compose -f "$DOCKER_COMPOSE_FILE" exec app /bin/bash
}

migrate() {
    print_header "Running database migrations"
    docker-compose -f "$DOCKER_COMPOSE_FILE" exec app python db_init.py
    print_success "Migrations completed"
}

create_admin() {
    print_header "Creating admin user"
    read -p "Enter admin username: " username
    read -p "Enter admin email: " email
    read -sp "Enter admin password: " password
    echo
    
    docker-compose -f "$DOCKER_COMPOSE_FILE" exec app python -c "
from app import app, db
from models import User

with app.app_context():
    admin = User(username='$username', email='$email', is_admin=True)
    admin.set_password('$password')
    db.session.add(admin)
    db.session.commit()
    print('Admin user created successfully')
"
    
    print_success "Admin user created"
}

# Main script
main() {
    case "${1:-help}" in
        up)
            setup
            build
            start
            ;;
        down)
            stop
            ;;
        restart)
            restart
            ;;
        logs)
            view_logs
            ;;
        ps)
            ps_containers
            ;;
        clean)
            clean
            ;;
        health)
            health_check
            ;;
        backup)
            backup
            ;;
        restore)
            restore "$2"
            ;;
        shell)
            shell
            ;;
        migrate)
            migrate
            ;;
        admin)
            create_admin
            ;;
        build)
            setup
            build
            ;;
        help)
            echo "AI Attendance System - Docker Launcher"
            echo ""
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  up              Start all containers (includes setup & build)"
            echo "  down            Stop all containers"
            echo "  restart         Restart all containers"
            echo "  logs            View application logs"
            echo "  ps              Show running containers"
            echo "  clean           Remove containers and volumes"
            echo "  build           Build Docker images"
            echo "  health          Perform health checks"
            echo "  backup          Backup database"
            echo "  restore <file>  Restore database from backup"
            echo "  shell           Open shell in app container"
            echo "  migrate         Run database migrations"
            echo "  admin           Create admin user"
            echo "  help            Show this help message"
            echo ""
            ;;
        *)
            print_error "Unknown command: $1"
            echo "Run '$0 help' for usage information"
            exit 1
            ;;
    esac
}

main "$@"

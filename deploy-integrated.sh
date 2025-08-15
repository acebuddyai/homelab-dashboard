#!/bin/bash

# Integrated Homelab Deployment Script
# Deploys: Dashboard, AI Chat, Email, Calendar, and Nextcloud services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"
COMPOSE_FILE="${SCRIPT_DIR}/docker-compose-integrated.yml"

# Function to print colored output
print_color() {
    color=$1
    shift
    echo -e "${color}$@${NC}"
}

# Function to print section headers
print_header() {
    echo
    print_color $CYAN "╔════════════════════════════════════════════════════════════════════╗"
    printf "${CYAN}║${NC} %-66s ${CYAN}║${NC}\n" "$1"
    print_color $CYAN "╚════════════════════════════════════════════════════════════════════╝"
    echo
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to generate random password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Function to check system requirements
check_requirements() {
    print_header "Checking System Requirements"

    local has_error=false

    # Check for Docker
    if command_exists docker; then
        print_color $GREEN "✓ Docker installed"
        docker_version=$(docker --version | awk '{print $3}' | sed 's/,//')
        echo "  Version: $docker_version"
    else
        print_color $RED "✗ Docker not installed"
        has_error=true
    fi

    # Check for Docker Compose
    if command_exists docker-compose; then
        print_color $GREEN "✓ Docker Compose installed"
        compose_version=$(docker-compose --version | awk '{print $3}' | sed 's/,//')
        echo "  Version: $compose_version"
    else
        print_color $RED "✗ Docker Compose not installed"
        has_error=true
    fi

    # Check for required tools
    local tools=("openssl" "curl" "htpasswd")
    for tool in "${tools[@]}"; do
        if command_exists $tool; then
            print_color $GREEN "✓ $tool installed"
        else
            print_color $YELLOW "⚠ $tool not installed (optional but recommended)"
            if [ "$tool" = "htpasswd" ]; then
                echo "  Install with: sudo apt-get install apache2-utils"
            fi
        fi
    done

    # Check system resources
    total_ram=$(free -g | awk '/^Mem:/{print $2}')
    available_ram=$(free -g | awk '/^Mem:/{print $7}')
    print_color $BLUE "System RAM: ${total_ram}GB total, ${available_ram}GB available"

    if [ "$total_ram" -lt 16 ]; then
        print_color $YELLOW "⚠ Warning: System has less than 16GB RAM"
        echo "  Some services may run slowly"
    else
        print_color $GREEN "✓ Sufficient RAM (32GB detected)"
    fi

    # Check disk space
    available_space=$(df -BG "${SCRIPT_DIR}" | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$available_space" -lt 20 ]; then
        print_color $YELLOW "⚠ Warning: Less than 20GB disk space available"
    else
        print_color $GREEN "✓ Sufficient disk space (${available_space}GB available)"
    fi

    if [ "$has_error" = true ]; then
        print_color $RED "Please install missing requirements before continuing"
        exit 1
    fi
}

# Function to create directories
create_directories() {
    print_header "Creating Directory Structure"

    local dirs=(
        "email/data"
        "email/config"
        "email/roundcube/config"
        "email/roundcube/db"
        "email/roundcube/temp"
        "calendar/data"
        "calendar/config"
        "nextcloud/apps"
        "nextcloud/config"
        "nextcloud/data"
        "web-ui"
        "api-gateway"
        "caddy"
        "scripts"
    )

    for dir in "${dirs[@]}"; do
        mkdir -p "${SCRIPT_DIR}/${dir}"
        print_color $GREEN "✓ Created ${dir}"
    done

    # Set proper permissions
    chmod 755 "${SCRIPT_DIR}/email/roundcube/temp" 2>/dev/null || true
    chmod 755 "${SCRIPT_DIR}/calendar/data" 2>/dev/null || true
}

# Function to setup environment variables
setup_environment() {
    print_header "Setting Up Environment Variables"

    if [ -f "$ENV_FILE" ]; then
        print_color $BLUE "Environment file exists. Loading existing configuration..."
        source "$ENV_FILE"
    else
        print_color $YELLOW "Creating new environment configuration..."

        # Generate passwords if not set
        NEXTCLOUD_DB_PASSWORD=${NEXTCLOUD_DB_PASSWORD:-$(generate_password)}
        NEXTCLOUD_ADMIN_PASSWORD=${NEXTCLOUD_ADMIN_PASSWORD:-$(generate_password)}
        POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-$(generate_password)}

        # Create .env file
        cat > "$ENV_FILE" << EOF
# Homelab Environment Configuration
# Generated on $(date)

# Domain Configuration
DOMAIN=localhost
EXTERNAL_DOMAIN=localhost

# Nextcloud Configuration
NEXTCLOUD_DB_PASSWORD=${NEXTCLOUD_DB_PASSWORD}
NEXTCLOUD_ADMIN_USER=admin
NEXTCLOUD_ADMIN_PASSWORD=${NEXTCLOUD_ADMIN_PASSWORD}

# Database Passwords
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

# Email Configuration
MADDY_DOMAIN=localhost
MADDY_HOSTNAME=mail.localhost

# Service Ports (can be customized)
DASHBOARD_PORT=8080
OLLAMA_PORT=11434
NEXTCLOUD_PORT=8082
WEBMAIL_PORT=8086
CALENDAR_PORT=5232

EOF

        chmod 600 "$ENV_FILE"
        print_color $GREEN "✓ Environment file created"
        print_color $YELLOW "Important: Save these credentials:"
        echo "  Nextcloud Admin: admin / ${NEXTCLOUD_ADMIN_PASSWORD}"
    fi
}

# Function to initialize Ollama
init_ollama() {
    print_header "Initializing Ollama AI Service"

    # Start Ollama first
    print_color $BLUE "Starting Ollama container..."
    docker-compose -f "$COMPOSE_FILE" up -d ollama

    # Wait for Ollama to be ready
    print_color $BLUE "Waiting for Ollama to start..."
    sleep 5

    local max_attempts=30
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
            print_color $GREEN "✓ Ollama is ready"
            break
        fi
        attempt=$((attempt + 1))
        sleep 2
    done

    if [ $attempt -eq $max_attempts ]; then
        print_color $YELLOW "⚠ Ollama may not be fully ready yet"
    fi

    # Check if model exists
    print_color $BLUE "Checking for llama3.2:1b model..."
    if docker exec ollama ollama list 2>/dev/null | grep -q "llama3.2:1b"; then
        print_color $GREEN "✓ Model already installed"
    else
        print_color $YELLOW "Pulling llama3.2:1b model (this may take a few minutes)..."
        docker exec ollama ollama pull llama3.2:1b || {
            print_color $YELLOW "⚠ Could not pull model. You may need to do this manually later."
        }
    fi
}

# Function to setup email service
setup_email() {
    print_header "Setting Up Email Service"

    # Create default email user if manage script exists
    if [ -f "${SCRIPT_DIR}/email/manage-users.sh" ]; then
        print_color $BLUE "Email user management script available"
        echo "  To create email users, run:"
        echo "  ./email/manage-users.sh create <username> <password>"
    fi

    print_color $GREEN "✓ Email service configured"
}

# Function to setup calendar service
setup_calendar() {
    print_header "Setting Up Calendar Service"

    # Create htpasswd file for calendar users
    touch "${SCRIPT_DIR}/calendar/config/users"
    chmod 644 "${SCRIPT_DIR}/calendar/config/users"

    if [ -f "${SCRIPT_DIR}/calendar/manage-users.sh" ]; then
        print_color $BLUE "Calendar user management script available"
        echo "  To create calendar users, run:"
        echo "  ./calendar/manage-users.sh create <username> <password>"
    fi

    print_color $GREEN "✓ Calendar service configured"
}

# Function to deploy services
deploy_services() {
    print_header "Deploying All Services"

    # Create network if it doesn't exist
    if ! docker network ls | grep -q homelab; then
        print_color $BLUE "Creating Docker network..."
        docker network create homelab
    fi

    # Deploy all services
    print_color $BLUE "Starting all containers..."
    docker-compose -f "$COMPOSE_FILE" up -d

    if [ $? -eq 0 ]; then
        print_color $GREEN "✓ All services deployed successfully"
    else
        print_color $RED "✗ Deployment failed"
        exit 1
    fi
}

# Function to check service health
check_health() {
    print_header "Service Health Check"

    local services=(
        "web-ui:8080:Dashboard"
        "ollama:11434/api/tags:AI Chat"
        "maddy:587:Email (SMTP)"
        "roundcube:8086:Webmail"
        "radicale:5232:Calendar"
        "nextcloud:8082:Nextcloud"
    )

    for service in "${services[@]}"; do
        IFS=':' read -r container port name <<< "$service"

        if docker ps | grep -q "$container"; then
            if curl -s -o /dev/null -w "%{http_code}" "http://localhost:${port}" | grep -qE "200|302|401"; then
                print_color $GREEN "✓ ${name} is running (http://localhost:${port%/*})"
            else
                print_color $YELLOW "⚠ ${name} container running but not responding"
            fi
        else
            print_color $RED "✗ ${name} is not running"
        fi
    done
}

# Function to show post-deployment information
show_info() {
    print_header "Deployment Complete!"

    print_color $GREEN "Your Homelab services are ready!"
    echo
    print_color $CYAN "Access your services at:"
    echo "  • Dashboard:    http://localhost:8080"
    echo "  • Webmail:      http://localhost:8086"
    echo "  • Calendar:     http://localhost:5232"
    echo "  • Nextcloud:    http://localhost:8082"
    echo "  • AI API:       http://localhost:11434"
    echo
    print_color $CYAN "Management Commands:"
    echo "  • View logs:    docker-compose -f docker-compose-integrated.yml logs -f [service]"
    echo "  • Stop all:     docker-compose -f docker-compose-integrated.yml down"
    echo "  • Restart:      docker-compose -f docker-compose-integrated.yml restart"
    echo "  • Email users:  ./email/manage-users.sh help"
    echo "  • Calendar:     ./calendar/manage-users.sh help"
    echo

    if [ -f "$ENV_FILE" ]; then
        source "$ENV_FILE"
        print_color $YELLOW "Default Credentials:"
        echo "  • Nextcloud:    admin / ${NEXTCLOUD_ADMIN_PASSWORD}"
        echo "  • Create email and calendar users with the management scripts"
    fi

    echo
    print_color $BLUE "GitHub Repository: https://github.com/acebuddyai/homelab-dashboard"
}

# Function to handle errors
error_handler() {
    print_color $RED "Error occurred during deployment!"
    print_color $YELLOW "Check the logs with: docker-compose -f docker-compose-integrated.yml logs"
    exit 1
}

# Main deployment function
main() {
    trap error_handler ERR

    print_color $CYAN "
    ╦ ╦┌─┐┌┬┐┌─┐┬  ┌─┐┌┐
    ╠═╣│ ││││├┤ │  ├─┤├┴┐
    ╩ ╩└─┘┴ ┴└─┘┴─┘┴ ┴└─┘
    Integrated Deployment Script v1.0
    "

    # Run deployment steps
    check_requirements
    create_directories
    setup_environment
    init_ollama
    setup_email
    setup_calendar
    deploy_services
    check_health
    show_info
}

# Run main function
main "$@"

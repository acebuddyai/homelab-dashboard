#!/bin/bash
# =============================================================================
# MATRIX HOMESERVER ADMINISTRATION UTILITY
# =============================================================================
# Comprehensive management script for Matrix homeserver operations
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MATRIX_DIR="$SCRIPT_DIR/matrix"
HOMESERVER_CONFIG="$MATRIX_DIR/synapse/homeserver.yaml"

# Helper functions
print_header() {
    echo -e "${BLUE}🏠 Matrix Homeserver Admin - acebuddy.quest${NC}"
    echo -e "${BLUE}=============================================${NC}"
    echo ""
}

print_section() {
    echo -e "${CYAN}📋 $1${NC}"
    echo "$(printf '%.0s-' {1..50})"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${PURPLE}ℹ️  $1${NC}"
}

# Check if we're in the correct directory
check_environment() {
    if [ ! -f "$HOMESERVER_CONFIG" ]; then
        print_error "Matrix homeserver.yaml not found at $HOMESERVER_CONFIG"
        print_error "Please run this script from the homelab directory"
        exit 1
    fi
}

# Service status functions
show_service_status() {
    print_section "Service Status"

    services=("matrix-synapse" "matrix-postgres" "matrix-cinny" "matrix-bot" "caddy")

    for service in "${services[@]}"; do
        if docker ps --filter "name=$service" --filter "status=running" -q | grep -q .; then
            health=$(docker inspect --format='{{.State.Health.Status}}' "$service" 2>/dev/null || echo "no-healthcheck")
            if [ "$health" = "healthy" ]; then
                print_success "$service: Running (Healthy)"
            elif [ "$health" = "no-healthcheck" ]; then
                print_success "$service: Running"
            else
                print_warning "$service: Running ($health)"
            fi
        else
            print_error "$service: Not running"
        fi
    done

    echo ""
    print_info "Total Matrix containers: $(docker ps --filter "name=matrix-" --format '{{.Names}}' | wc -l)"
}

# Test email functionality
test_email_config() {
    print_section "Email Configuration Test"

    if [ -f "$MATRIX_DIR/test-email.py" ]; then
        echo "🧪 Testing SMTP connection..."
        cd "$MATRIX_DIR"
        if python3 test-email.py --skip-send; then
            print_success "Email configuration is working"
            echo ""
            read -p "Send test email? Enter email address (or press Enter to skip): " test_email
            if [ -n "$test_email" ]; then
                if python3 test-email.py --email "$test_email" --test-type admin-test; then
                    print_success "Test email sent to $test_email"
                else
                    print_error "Failed to send test email"
                fi
            fi
        else
            print_error "Email configuration test failed"
        fi
        cd "$SCRIPT_DIR"
    else
        print_error "Email test script not found"
    fi
}

# Show recent logs
show_logs() {
    local service=${1:-matrix-synapse}
    local lines=${2:-50}

    print_section "Recent Logs for $service"

    if docker ps --filter "name=$service" -q | grep -q .; then
        echo "📋 Last $lines lines from $service:"
        echo ""
        docker logs --tail "$lines" "$service" 2>&1 | tail -20
    else
        print_error "Service $service is not running"
    fi
}

# User management functions
list_users() {
    print_section "Matrix Users"

    echo "🔍 Querying Matrix database for users..."

    if docker exec matrix-postgres psql -U synapse -d synapse -t -c "
        SELECT
            name as username,
            admin,
            deactivated,
            to_timestamp(creation_ts/1000) as created,
            user_type
        FROM users
        WHERE name LIKE '@%:acebuddy.quest'
        ORDER BY creation_ts DESC;
    " 2>/dev/null; then
        print_success "User list retrieved"
    else
        print_error "Failed to query user database"
        print_info "Try: docker exec -it matrix-postgres psql -U synapse -d synapse"
    fi
}

# Create admin user
create_admin_user() {
    local username="$1"

    if [ -z "$username" ]; then
        read -p "Enter username (without @acebuddy.quest): " username
    fi

    if [ -z "$username" ]; then
        print_error "Username cannot be empty"
        return 1
    fi

    print_section "Creating Admin User: $username"

    echo "🔧 Creating admin user @$username:acebuddy.quest..."

    if docker exec -it matrix-synapse register_new_matrix_user \
        -u "$username" \
        -a \
        -c /data/homeserver.yaml \
        https://matrix.acebuddy.quest; then
        print_success "Admin user @$username:acebuddy.quest created"
    else
        print_error "Failed to create admin user"
    fi
}

# Matrix server information
show_server_info() {
    print_section "Matrix Server Information"

    echo "🏠 Server Details:"
    echo "   Domain: acebuddy.quest"
    echo "   Public URL: https://matrix.acebuddy.quest"
    echo "   Client URL: https://cinny.acebuddy.quest"
    echo ""

    echo "🔧 Configuration:"
    echo "   Config File: $HOMESERVER_CONFIG"
    echo "   Database: PostgreSQL (matrix-postgres)"
    echo "   Media Store: /data/media_store"
    echo ""

    if docker ps --filter "name=matrix-synapse" -q | grep -q .; then
        echo "📊 Synapse Version:"
        docker exec matrix-synapse python -c "import synapse; print(f'   Version: {synapse.__version__}')" 2>/dev/null || echo "   Version: Unable to determine"
        echo ""

        echo "💾 Database Stats:"
        docker exec matrix-postgres psql -U synapse -d synapse -t -c "
            SELECT
                'Users: ' || count(*)
            FROM users
            WHERE name LIKE '@%:acebuddy.quest';
        " 2>/dev/null || echo "   Unable to query database"

        docker exec matrix-postgres psql -U synapse -d synapse -t -c "
            SELECT
                'Rooms: ' || count(DISTINCT room_id)
            FROM room_memberships
            WHERE membership = 'join';
        " 2>/dev/null || echo "   Unable to query rooms"
    fi
}

# Backup Matrix data
backup_matrix() {
    print_section "Matrix Data Backup"

    local backup_dir="matrix-backup-$(date +%Y%m%d_%H%M%S)"

    echo "💾 Creating backup in $backup_dir..."
    mkdir -p "$backup_dir"

    # Backup configuration
    print_info "Backing up configuration files..."
    cp -r matrix/synapse "$backup_dir/synapse-config"
    cp -r matrix/cinny "$backup_dir/cinny-config"
    cp matrix/docker-compose.yml "$backup_dir/"

    # Backup database
    print_info "Backing up PostgreSQL database..."
    docker exec matrix-postgres pg_dump -U synapse synapse | gzip > "$backup_dir/matrix-database.sql.gz"

    # Backup media store (if requested)
    read -p "Backup media store? This may take a while (y/N): " backup_media
    if [[ "$backup_media" =~ ^[Yy]$ ]]; then
        print_info "Backing up media store..."
        docker run --rm -v matrix_media_store:/source -v "$(pwd)/$backup_dir":/backup alpine tar czf /backup/media-store.tar.gz -C /source .
    fi

    print_success "Backup completed: $backup_dir"
    print_info "Backup size: $(du -sh "$backup_dir" | cut -f1)"
}

# Reset user password
reset_user_password() {
    local username="$1"

    if [ -z "$username" ]; then
        read -p "Enter username to reset password for: " username
    fi

    if [ -z "$username" ]; then
        print_error "Username cannot be empty"
        return 1
    fi

    print_section "Resetting Password for $username"

    # Add @ and domain if not present
    if [[ "$username" != @* ]]; then
        username="@$username:acebuddy.quest"
    fi

    echo "🔐 Resetting password for $username..."

    if docker exec -it matrix-synapse hash_password -c /data/homeserver.yaml; then
        print_success "Password reset hash generated"
        print_info "You can now update the user's password in the database or use the admin API"
    else
        print_error "Failed to generate password hash"
    fi
}

# Matrix health check
health_check() {
    print_section "Matrix Health Check"

    echo "🏥 Checking Matrix server health..."

    # Check if services are running
    if ! docker ps --filter "name=matrix-synapse" -q | grep -q .; then
        print_error "Matrix Synapse is not running"
        return 1
    fi

    # Check Matrix API
    if curl -s -f https://matrix.acebuddy.quest/_matrix/client/versions > /dev/null; then
        print_success "Matrix API is responding"
    else
        print_error "Matrix API is not responding"
    fi

    # Check well-known endpoints
    if curl -s -f https://acebuddy.quest/.well-known/matrix/server > /dev/null; then
        print_success "Matrix well-known server endpoint working"
    else
        print_error "Matrix well-known server endpoint failed"
    fi

    # Check database connectivity
    if docker exec matrix-postgres pg_isready -U synapse -d synapse > /dev/null 2>&1; then
        print_success "PostgreSQL database is ready"
    else
        print_error "PostgreSQL database is not ready"
    fi

    # Check email if configured
    if grep -q "smtp_host:" "$HOMESERVER_CONFIG"; then
        echo ""
        echo "📧 Email configuration found - testing..."
        if [ -f "$MATRIX_DIR/test-email.py" ]; then
            cd "$MATRIX_DIR"
            if python3 test-email.py --skip-send > /dev/null 2>&1; then
                print_success "Email SMTP configuration working"
            else
                print_warning "Email SMTP configuration may have issues"
            fi
            cd "$SCRIPT_DIR"
        fi
    else
        print_warning "No email configuration found"
    fi
}

# Main menu
show_menu() {
    print_header

    echo "Choose an action:"
    echo ""
    echo "📊 Status & Information:"
    echo "  1) Show service status"
    echo "  2) Show server information"
    echo "  3) Health check"
    echo "  4) View logs"
    echo ""
    echo "👥 User Management:"
    echo "  5) List users"
    echo "  6) Create admin user"
    echo "  7) Reset user password"
    echo ""
    echo "📧 Email & Authentication:"
    echo "  8) Test email configuration"
    echo "  9) Enable QR code login (MAS)"
    echo " 10) Disable QR code login"
    echo ""
    echo "💾 Maintenance:"
    echo " 11) Backup Matrix data"
    echo " 12) View Matrix configuration"
    echo " 13) Restart Matrix services"
    echo ""
    echo "🚪 Other:"
    echo " 14) Exit"
    echo ""
}

# Handle menu selection
handle_selection() {
    local choice="$1"

    case $choice in
        1)
            show_service_status
            ;;
        2)
            show_server_info
            ;;
        3)
            health_check
            ;;
        4)
            echo ""
            echo "Available services: matrix-synapse, matrix-postgres, matrix-cinny, matrix-bot, caddy"
            read -p "Enter service name (default: matrix-synapse): " service
            service=${service:-matrix-synapse}
            read -p "Number of log lines (default: 50): " lines
            lines=${lines:-50}
            show_logs "$service" "$lines"
            ;;
        5)
            list_users
            ;;
        6)
            create_admin_user
            ;;
        7)
            reset_user_password
            ;;
        8)
            test_email_config
            ;;
        9)
            if [ -f "enable-qr-login.sh" ]; then
                echo ""
                print_warning "This will enable MAS and may affect existing user sessions"
                read -p "Continue? (y/N): " confirm
                if [[ "$confirm" =~ ^[Yy]$ ]]; then
                    ./enable-qr-login.sh
                else
                    print_info "QR login setup cancelled"
                fi
            else
                print_error "enable-qr-login.sh script not found"
            fi
            ;;
        10)
            if [ -f "disable-qr-login.sh" ]; then
                echo ""
                print_warning "This will disable MAS and revert to basic authentication"
                read -p "Continue? (y/N): " confirm
                if [[ "$confirm" =~ ^[Yy]$ ]]; then
                    ./disable-qr-login.sh
                else
                    print_info "QR login disable cancelled"
                fi
            else
                print_error "disable-qr-login.sh script not found"
            fi
            ;;
        11)
            backup_matrix
            ;;
        12)
            print_section "Matrix Configuration"
            echo "📄 Current homeserver.yaml:"
            echo ""
            head -20 "$HOMESERVER_CONFIG"
            echo "..."
            echo ""
            print_info "Full config: $HOMESERVER_CONFIG"
            print_info "View with: cat $HOMESERVER_CONFIG"
            ;;
        13)
            print_section "Restarting Matrix Services"
            echo "🔄 Restarting Matrix services..."
            cd "$MATRIX_DIR"
            docker-compose restart
            cd "$SCRIPT_DIR"
            print_success "Matrix services restarted"
            ;;
        14)
            echo ""
            print_info "👋 Goodbye!"
            exit 0
            ;;
        *)
            print_error "Invalid selection: $choice"
            ;;
    esac
}

# Quick status function for command line use
quick_status() {
    print_header
    show_service_status
    echo ""
    print_info "For full admin menu, run: ./matrix-admin.sh"
    echo ""
    print_info "Quick commands:"
    echo "   ./matrix-admin.sh logs [service] [lines]"
    echo "   ./matrix-admin.sh health"
    echo "   ./matrix-admin.sh users"
    echo "   ./matrix-admin.sh email-test"
}

# Command line interface
if [ $# -eq 0 ]; then
    # Interactive mode
    check_environment

    while true; do
        show_menu
        read -p "Enter your choice (1-14): " choice
        echo ""

        handle_selection "$choice"

        echo ""
        echo "Press Enter to continue..."
        read
        clear
    done
else
    # Command line mode
    check_environment

    case "$1" in
        "status"|"s")
            quick_status
            ;;
        "health"|"h")
            health_check
            ;;
        "logs"|"l")
            service=${2:-matrix-synapse}
            lines=${3:-50}
            show_logs "$service" "$lines"
            ;;
        "users"|"u")
            list_users
            ;;
        "email-test"|"e")
            test_email_config
            ;;
        "backup"|"b")
            backup_matrix
            ;;
        "restart"|"r")
            print_section "Restarting Matrix Services"
            cd "$MATRIX_DIR"
            docker-compose restart
            cd "$SCRIPT_DIR"
            print_success "Matrix services restarted"
            ;;
        "info"|"i")
            show_server_info
            ;;
        *)
            echo "Matrix Admin Utility"
            echo ""
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  status, s     - Show service status"
            echo "  health, h     - Run health checks"
            echo "  logs, l       - Show logs [service] [lines]"
            echo "  users, u      - List Matrix users"
            echo "  email-test, e - Test email configuration"
            echo "  backup, b     - Backup Matrix data"
            echo "  restart, r    - Restart Matrix services"
            echo "  info, i       - Show server information"
            echo ""
            echo "Interactive mode:"
            echo "  $0            - Launch interactive menu"
            echo ""
            echo "Examples:"
            echo "  $0 status"
            echo "  $0 logs matrix-synapse 100"
            echo "  $0 health"
            echo "  $0 email-test"
            ;;
    esac
fi

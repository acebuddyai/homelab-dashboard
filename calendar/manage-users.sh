#!/bin/bash

# Calendar User Management Script for Radicale CalDAV/CardDAV Server
# Usage: ./manage-users.sh [command] [arguments]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
HTPASSWD_FILE="./config/users"
CONTAINER_NAME="radicale"
DATA_DIR="./data"

# Function to print colored output
print_color() {
    color=$1
    shift
    echo -e "${color}$@${NC}"
}

# Function to check if htpasswd is available
check_htpasswd() {
    if ! command -v htpasswd &> /dev/null; then
        print_color $YELLOW "htpasswd not found. Installing apache2-utils..."
        sudo apt-get update && sudo apt-get install -y apache2-utils
    fi
}

# Function to check if bcrypt is available
check_bcrypt() {
    # Test if htpasswd supports bcrypt
    if ! htpasswd -B -n test testpass &> /dev/null; then
        print_color $RED "Error: htpasswd doesn't support bcrypt encryption!"
        print_color $YELLOW "Please install apache2-utils version 2.4.0 or higher"
        exit 1
    fi
}

# Function to create htpasswd file if it doesn't exist
init_htpasswd() {
    if [ ! -f "$HTPASSWD_FILE" ]; then
        print_color $YELLOW "Creating htpasswd file..."
        mkdir -p $(dirname "$HTPASSWD_FILE")
        touch "$HTPASSWD_FILE"
        chmod 644 "$HTPASSWD_FILE"
    fi
}

# Function to create a new user
create_user() {
    local username=$1
    local password=$2

    if [ -z "$username" ] || [ -z "$password" ]; then
        print_color $RED "Error: Username and password are required!"
        echo "Usage: $0 create <username> <password>"
        exit 1
    fi

    # Check if user already exists
    if [ -f "$HTPASSWD_FILE" ] && grep -q "^${username}:" "$HTPASSWD_FILE" 2>/dev/null; then
        print_color $RED "Error: User '$username' already exists!"
        exit 1
    fi

    print_color $BLUE "Creating calendar user: $username"

    # Create user with bcrypt encryption
    htpasswd -B -b "$HTPASSWD_FILE" "$username" "$password" 2>/dev/null

    if [ $? -eq 0 ]; then
        # Create user's calendar collection directory
        USER_DIR="${DATA_DIR}/collections/collection-root/${username}"
        mkdir -p "$USER_DIR"

        print_color $GREEN "✓ User $username created successfully!"
        print_color $YELLOW "Calendar settings:"
        echo "  - Username: $username"
        echo "  - CalDAV URL: http://localhost:5232/${username}/"
        echo "  - CardDAV URL: http://localhost:5232/${username}/"
        echo "  - Web Interface: http://localhost:5232"
        echo ""
        echo "  Client Configuration:"
        echo "  - Server: localhost:5232"
        echo "  - Protocol: CalDAV/CardDAV"
        echo "  - Authentication: Basic"

        # Restart container to apply changes
        if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
            print_color $BLUE "Restarting Radicale container..."
            docker restart ${CONTAINER_NAME} &>/dev/null
        fi
    else
        print_color $RED "✗ Failed to create user"
        exit 1
    fi
}

# Function to delete a user
delete_user() {
    local username=$1

    if [ -z "$username" ]; then
        print_color $RED "Error: Username is required!"
        echo "Usage: $0 delete <username>"
        exit 1
    fi

    # Check if user exists
    if [ ! -f "$HTPASSWD_FILE" ] || ! grep -q "^${username}:" "$HTPASSWD_FILE" 2>/dev/null; then
        print_color $RED "Error: User '$username' does not exist!"
        exit 1
    fi

    print_color $YELLOW "Deleting user: $username"
    read -p "This will also delete all calendars and contacts. Are you sure? (y/N): " confirm

    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        # Remove user from htpasswd file
        htpasswd -D "$HTPASSWD_FILE" "$username" 2>/dev/null

        # Remove user's data
        USER_DIR="${DATA_DIR}/collections/collection-root/${username}"
        if [ -d "$USER_DIR" ]; then
            print_color $YELLOW "Removing user data..."
            rm -rf "$USER_DIR"
        fi

        if [ $? -eq 0 ]; then
            print_color $GREEN "✓ User $username deleted successfully!"

            # Restart container to apply changes
            if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
                docker restart ${CONTAINER_NAME} &>/dev/null
            fi
        else
            print_color $RED "✗ Failed to delete user"
            exit 1
        fi
    else
        print_color $BLUE "Deletion cancelled"
    fi
}

# Function to list all users
list_users() {
    print_color $BLUE "Calendar Users:"
    echo "==============="

    if [ ! -f "$HTPASSWD_FILE" ]; then
        print_color $YELLOW "No users file found. No users configured."
        return
    fi

    # Extract usernames from htpasswd file
    while IFS=: read -r username _; do
        if [ ! -z "$username" ]; then
            # Check if user has data
            USER_DIR="${DATA_DIR}/collections/collection-root/${username}"
            if [ -d "$USER_DIR" ]; then
                collections=$(find "$USER_DIR" -type d -mindepth 1 2>/dev/null | wc -l)
                echo "  • $username (${collections} collections)"
            else
                echo "  • $username (no data)"
            fi
        fi
    done < "$HTPASSWD_FILE"

    # Show total count
    total=$(grep -c '^[^:]' "$HTPASSWD_FILE" 2>/dev/null || echo "0")
    echo ""
    print_color $GREEN "Total users: $total"
}

# Function to change password
change_password() {
    local username=$1
    local new_password=$2

    if [ -z "$username" ] || [ -z "$new_password" ]; then
        print_color $RED "Error: Username and new password are required!"
        echo "Usage: $0 password <username> <new_password>"
        exit 1
    fi

    # Check if user exists
    if [ ! -f "$HTPASSWD_FILE" ] || ! grep -q "^${username}:" "$HTPASSWD_FILE" 2>/dev/null; then
        print_color $RED "Error: User '$username' does not exist!"
        exit 1
    fi

    print_color $BLUE "Changing password for: $username"

    # Update password with bcrypt encryption
    htpasswd -B -b "$HTPASSWD_FILE" "$username" "$new_password" 2>/dev/null

    if [ $? -eq 0 ]; then
        print_color $GREEN "✓ Password changed successfully!"

        # Restart container to apply changes
        if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
            docker restart ${CONTAINER_NAME} &>/dev/null
        fi
    else
        print_color $RED "✗ Failed to change password"
        exit 1
    fi
}

# Function to test user authentication
test_auth() {
    local username=$1
    local password=$2

    if [ -z "$username" ] || [ -z "$password" ]; then
        print_color $RED "Error: Username and password are required!"
        echo "Usage: $0 test <username> <password>"
        exit 1
    fi

    print_color $BLUE "Testing authentication for: $username"

    # Test with curl
    response=$(curl -s -o /dev/null -w "%{http_code}" \
        -u "${username}:${password}" \
        http://localhost:5232/.web/ 2>/dev/null)

    if [ "$response" = "200" ] || [ "$response" = "302" ]; then
        print_color $GREEN "✓ Authentication successful!"
    else
        print_color $RED "✗ Authentication failed (HTTP $response)"
        exit 1
    fi
}

# Function to show help
show_help() {
    cat << EOF
Calendar User Management Script for Radicale CalDAV/CardDAV Server

Usage: $0 <command> [arguments]

Commands:
    create <username> <password>    Create a new calendar user
    delete <username>               Delete a calendar user
    list                           List all calendar users
    password <username> <password>  Change user password
    test <username> <password>     Test user authentication
    help                          Show this help message

Examples:
    $0 create john secretpass123
    $0 delete john
    $0 list
    $0 password john newpass456
    $0 test john newpass456

Configuration:
    Users file: ${HTPASSWD_FILE}
    Data directory: ${DATA_DIR}
    Container: ${CONTAINER_NAME}

Client Configuration:
    Server Address: localhost:5232
    CalDAV URL: http://localhost:5232/{username}/
    CardDAV URL: http://localhost:5232/{username}/

    Tested Clients:
    - Thunderbird (with TbSync + Provider for CalDAV & CardDAV)
    - Evolution
    - DAVx⁵ (Android)
    - iOS Calendar/Contacts (native)

Notes:
    - Passwords are encrypted using bcrypt
    - Each user gets their own calendar/contacts collection
    - The Radicale container will be restarted after user changes
    - Use strong passwords with mixed characters

EOF
}

# Main script logic
main() {
    case "$1" in
        create)
            check_htpasswd
            check_bcrypt
            init_htpasswd
            create_user "$2" "$3"
            ;;
        delete)
            delete_user "$2"
            ;;
        list)
            list_users
            ;;
        password)
            check_htpasswd
            check_bcrypt
            change_password "$2" "$3"
            ;;
        test)
            test_auth "$2" "$3"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_color $RED "Error: Unknown command '$1'"
            echo
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"

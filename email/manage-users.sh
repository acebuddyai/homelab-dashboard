#!/bin/bash

# Email User Management Script for Maddy Mail Server
# Usage: ./manage-users.sh [command] [arguments]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
CONTAINER_NAME="maddy-mail"
DOMAIN="${MADDY_DOMAIN:-localhost}"

# Function to print colored output
print_color() {
    color=$1
    shift
    echo -e "${color}$@${NC}"
}

# Function to check if container is running
check_container() {
    if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        print_color $RED "Error: Maddy container '${CONTAINER_NAME}' is not running!"
        print_color $YELLOW "Start it with: docker-compose up -d maddy"
        exit 1
    fi
}

# Function to create a new user
create_user() {
    local email=$1
    local password=$2

    if [ -z "$email" ] || [ -z "$password" ]; then
        print_color $RED "Error: Email and password are required!"
        echo "Usage: $0 create <email> <password>"
        exit 1
    fi

    # Validate email format
    if ! echo "$email" | grep -qE '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'; then
        # If no domain provided, append default domain
        if ! echo "$email" | grep -q '@'; then
            email="${email}@${DOMAIN}"
        else
            print_color $RED "Error: Invalid email format!"
            exit 1
        fi
    fi

    print_color $BLUE "Creating user: $email"

    # Create user using maddy CLI
    docker exec -it ${CONTAINER_NAME} maddy creds create "$email" <<< "$password"

    if [ $? -eq 0 ]; then
        print_color $GREEN "✓ User $email created successfully!"
        print_color $YELLOW "Email settings:"
        echo "  - Email: $email"
        echo "  - IMAP Server: localhost:143 (or 993 for SSL)"
        echo "  - SMTP Server: localhost:587 (or 465 for SSL)"
        echo "  - Webmail: http://localhost:8086"
    else
        print_color $RED "✗ Failed to create user"
        exit 1
    fi
}

# Function to delete a user
delete_user() {
    local email=$1

    if [ -z "$email" ]; then
        print_color $RED "Error: Email is required!"
        echo "Usage: $0 delete <email>"
        exit 1
    fi

    # Add domain if not present
    if ! echo "$email" | grep -q '@'; then
        email="${email}@${DOMAIN}"
    fi

    print_color $YELLOW "Deleting user: $email"
    read -p "Are you sure? (y/N): " confirm

    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        docker exec -it ${CONTAINER_NAME} maddy creds remove "$email"

        if [ $? -eq 0 ]; then
            print_color $GREEN "✓ User $email deleted successfully!"
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
    print_color $BLUE "Email Users:"
    echo "============"

    # List users from maddy
    docker exec ${CONTAINER_NAME} maddy creds list 2>/dev/null | while read user; do
        if [ ! -z "$user" ]; then
            echo "  • $user"
        fi
    done

    if [ $? -ne 0 ]; then
        print_color $YELLOW "No users found or unable to list users"
    fi
}

# Function to change password
change_password() {
    local email=$1
    local new_password=$2

    if [ -z "$email" ] || [ -z "$new_password" ]; then
        print_color $RED "Error: Email and new password are required!"
        echo "Usage: $0 password <email> <new_password>"
        exit 1
    fi

    # Add domain if not present
    if ! echo "$email" | grep -q '@'; then
        email="${email}@${DOMAIN}"
    fi

    print_color $BLUE "Changing password for: $email"

    # Update password using maddy CLI
    docker exec -it ${CONTAINER_NAME} maddy creds password "$email" <<< "$new_password"

    if [ $? -eq 0 ]; then
        print_color $GREEN "✓ Password changed successfully!"
    else
        print_color $RED "✗ Failed to change password"
        exit 1
    fi
}

# Function to show help
show_help() {
    cat << EOF
Email User Management Script for Maddy Mail Server

Usage: $0 <command> [arguments]

Commands:
    create <email> <password>    Create a new email user
    delete <email>               Delete an email user
    list                        List all email users
    password <email> <password>  Change user password
    help                        Show this help message

Examples:
    $0 create john@example.com secretpass123
    $0 create john secretpass123    # Will use default domain
    $0 delete john@example.com
    $0 list
    $0 password john@example.com newpass456

Configuration:
    Default domain: ${DOMAIN}
    Container: ${CONTAINER_NAME}

Notes:
    - If no domain is provided in the email, ${DOMAIN} will be used
    - Passwords should be strong and contain mixed characters
    - The Maddy container must be running

EOF
}

# Main script logic
main() {
    case "$1" in
        create)
            check_container
            create_user "$2" "$3"
            ;;
        delete)
            check_container
            delete_user "$2"
            ;;
        list)
            check_container
            list_users
            ;;
        password)
            check_container
            change_password "$2" "$3"
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

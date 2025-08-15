#!/bin/bash

# Node-RED Flow Import Script
# This script imports example flows into Node-RED

set -e

# Configuration
NODE_RED_URL="${NODE_RED_URL:-http://localhost:1880}"
FLOWS_DIR="$(dirname "$0")/flows"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if Node-RED is running
check_node_red() {
    echo "Checking Node-RED status..."
    if curl -s -f "${NODE_RED_URL}" > /dev/null 2>&1; then
        print_status "Node-RED is running at ${NODE_RED_URL}"
        return 0
    else
        print_error "Node-RED is not accessible at ${NODE_RED_URL}"
        echo "Please ensure Node-RED is running and try again."
        exit 1
    fi
}

# Import a single flow file
import_flow() {
    local flow_file="$1"
    local flow_name=$(basename "$flow_file" .json)

    echo "Importing flow: ${flow_name}..."

    if [ ! -f "$flow_file" ]; then
        print_error "Flow file not found: $flow_file"
        return 1
    fi

    # Read the flow content
    flow_content=$(cat "$flow_file")

    # Import the flow via Node-RED API
    response=$(curl -s -X POST "${NODE_RED_URL}/flows" \
        -H "Content-Type: application/json" \
        -H "Node-RED-Deployment-Type: flows" \
        -d "$flow_content" \
        -w "\n%{http_code}")

    http_code=$(echo "$response" | tail -n1)

    if [ "$http_code" = "204" ] || [ "$http_code" = "200" ]; then
        print_status "Successfully imported: ${flow_name}"
        return 0
    else
        print_error "Failed to import ${flow_name} (HTTP ${http_code})"
        echo "Response: $(echo "$response" | head -n-1)"
        return 1
    fi
}

# Get current flows (for backup)
backup_current_flows() {
    echo "Backing up current flows..."

    backup_dir="${FLOWS_DIR}/../backups"
    mkdir -p "$backup_dir"

    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_file="${backup_dir}/flows_backup_${timestamp}.json"

    current_flows=$(curl -s "${NODE_RED_URL}/flows")

    if [ -n "$current_flows" ] && [ "$current_flows" != "[]" ]; then
        echo "$current_flows" > "$backup_file"
        print_status "Current flows backed up to: $backup_file"
    else
        print_warning "No existing flows to backup"
    fi
}

# List available flow files
list_flows() {
    echo "Available flows to import:"
    echo "=========================="

    if [ -d "$FLOWS_DIR" ]; then
        for flow in "$FLOWS_DIR"/*.json; do
            if [ -f "$flow" ]; then
                flow_name=$(basename "$flow" .json)
                echo "  - $flow_name"
            fi
        done
    else
        print_warning "No flows directory found at: $FLOWS_DIR"
    fi
}

# Main menu
show_menu() {
    echo ""
    echo "Node-RED Flow Import Tool"
    echo "========================="
    echo "1. Import all example flows"
    echo "2. Import specific flow"
    echo "3. List available flows"
    echo "4. Backup current flows"
    echo "5. Check Node-RED status"
    echo "6. Exit"
    echo ""
    read -p "Select an option (1-6): " choice

    case $choice in
        1)
            import_all_flows
            ;;
        2)
            import_specific_flow
            ;;
        3)
            list_flows
            show_menu
            ;;
        4)
            backup_current_flows
            show_menu
            ;;
        5)
            check_node_red
            show_menu
            ;;
        6)
            echo "Exiting..."
            exit 0
            ;;
        *)
            print_error "Invalid option"
            show_menu
            ;;
    esac
}

# Import all flows
import_all_flows() {
    check_node_red
    backup_current_flows

    echo ""
    echo "Importing all example flows..."
    echo "=============================="

    if [ ! -d "$FLOWS_DIR" ]; then
        print_error "Flows directory not found: $FLOWS_DIR"
        return 1
    fi

    success_count=0
    fail_count=0

    for flow_file in "$FLOWS_DIR"/*.json; do
        if [ -f "$flow_file" ]; then
            if import_flow "$flow_file"; then
                ((success_count++))
            else
                ((fail_count++))
            fi
            echo ""
        fi
    done

    echo "=============================="
    print_status "Import complete!"
    echo "  Successful: $success_count"
    if [ $fail_count -gt 0 ]; then
        echo "  Failed: $fail_count"
    fi

    echo ""
    echo "Access Node-RED at: ${NODE_RED_URL}"
    echo ""

    show_menu
}

# Import specific flow
import_specific_flow() {
    check_node_red

    echo ""
    list_flows
    echo ""
    read -p "Enter flow name (without .json): " flow_name

    flow_file="${FLOWS_DIR}/${flow_name}.json"

    if [ -f "$flow_file" ]; then
        backup_current_flows
        import_flow "$flow_file"
    else
        print_error "Flow file not found: $flow_file"
    fi

    show_menu
}

# Handle command line arguments
if [ "$#" -gt 0 ]; then
    case "$1" in
        --import-all|-a)
            check_node_red
            backup_current_flows
            import_all_flows
            exit 0
            ;;
        --import|-i)
            if [ -n "$2" ]; then
                check_node_red
                backup_current_flows
                import_flow "$2"
                exit 0
            else
                print_error "Please specify a flow file to import"
                exit 1
            fi
            ;;
        --backup|-b)
            check_node_red
            backup_current_flows
            exit 0
            ;;
        --list|-l)
            list_flows
            exit 0
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --import-all, -a     Import all example flows"
            echo "  --import, -i <file>  Import specific flow file"
            echo "  --backup, -b         Backup current flows"
            echo "  --list, -l           List available flows"
            echo "  --help, -h           Show this help message"
            echo ""
            echo "Without options, runs in interactive mode"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
else
    # Interactive mode
    show_menu
fi

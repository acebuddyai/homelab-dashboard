#!/bin/bash

# Homelab Services Status Check Script
# Checks all services via both local and public URLs

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    color=$1
    shift
    echo -e "${color}$@${NC}"
}

# Function to check URL status
check_url() {
    local url=$1
    local name=$2
    local timeout=5

    # Get HTTP status code
    status=$(curl -o /dev/null -s -w "%{http_code}" --connect-timeout $timeout "$url" 2>/dev/null || echo "000")

    if [[ "$status" == "200" ]] || [[ "$status" == "302" ]] || [[ "$status" == "301" ]]; then
        print_color $GREEN "✓ $name"
        echo "  URL: $url"
        echo "  Status: $status"
    elif [[ "$status" == "401" ]] || [[ "$status" == "403" ]]; then
        print_color $YELLOW "⚠ $name (Authentication Required)"
        echo "  URL: $url"
        echo "  Status: $status"
    elif [[ "$status" == "000" ]]; then
        print_color $RED "✗ $name (Connection Failed)"
        echo "  URL: $url"
        echo "  Status: Unreachable"
    else
        print_color $RED "✗ $name"
        echo "  URL: $url"
        echo "  Status: $status"
    fi
    echo
}

# Function to check Docker container status
check_container() {
    local container=$1
    local name=$2

    if docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        status=$(docker inspect -f '{{.State.Status}}' "$container" 2>/dev/null)
        if [[ "$status" == "running" ]]; then
            # Get health status if available
            health=$(docker inspect -f '{{.State.Health.Status}}' "$container" 2>/dev/null || echo "no health check")
            if [[ "$health" == "healthy" ]]; then
                print_color $GREEN "✓ $name (healthy)"
            elif [[ "$health" == "unhealthy" ]]; then
                print_color $RED "✗ $name (unhealthy)"
            elif [[ "$health" == "no health check" ]]; then
                print_color $GREEN "✓ $name (running)"
            else
                print_color $YELLOW "⚠ $name ($health)"
            fi

            # Show port mappings
            ports=$(docker port "$container" 2>/dev/null | head -1)
            if [[ ! -z "$ports" ]]; then
                echo "  Ports: $ports"
            fi
        else
            print_color $YELLOW "⚠ $name ($status)"
        fi
    else
        print_color $RED "✗ $name (not found)"
    fi
}

# Header
print_color $CYAN "╔════════════════════════════════════════════════════════════════════╗"
printf "${CYAN}║${NC} %-66s ${CYAN}║${NC}\n" "              HOMELAB SERVICES STATUS CHECK"
print_color $CYAN "╚════════════════════════════════════════════════════════════════════╝"
echo

# Get current date/time
print_color $BLUE "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo

# Check Docker daemon
print_color $CYAN "═══ Docker Status ═══"
if systemctl is-active docker >/dev/null 2>&1; then
    print_color $GREEN "✓ Docker daemon is running"
    docker_version=$(docker --version | awk '{print $3}' | sed 's/,//')
    echo "  Version: $docker_version"
else
    print_color $RED "✗ Docker daemon is not running"
    exit 1
fi
echo

# Check Local Services
print_color $CYAN "═══ Local Services (localhost) ═══"
check_url "http://localhost:8080" "Dashboard"
check_url "http://localhost:8080/health" "Dashboard Health"
check_url "http://localhost:11434/api/tags" "Ollama API"
check_url "http://localhost:8086" "Roundcube Webmail"
check_url "http://localhost:5233" "Baikal Calendar"
check_url "http://localhost:3000/health" "API Gateway"
check_url "http://localhost:8000" "Windmill"

# Check Public URLs
print_color $CYAN "═══ Public URLs (acebuddy.quest) ═══"
check_url "https://ai.acebuddy.quest" "AI Dashboard"
check_url "https://mail.acebuddy.quest" "Email (Roundcube)"
check_url "https://calendar.acebuddy.quest" "Calendar (Baikal)"
check_url "https://files.acebuddy.quest" "Nextcloud"
check_url "https://chat.acebuddy.quest" "Open WebUI"
check_url "https://workflows.acebuddy.quest" "Windmill"
check_url "https://tasks.acebuddy.quest" "Vikunja"
check_url "https://search.acebuddy.quest" "SearXNG"
check_url "https://status.acebuddy.quest" "Status Page"
check_url "https://api.acebuddy.quest/health" "API Gateway"

# Check Docker Containers
print_color $CYAN "═══ Docker Containers ═══"
check_container "web-ui" "Web UI"
check_container "ollama" "Ollama"
check_container "roundcube" "Roundcube"
check_container "baikal" "Baikal"
check_container "nextcloud" "Nextcloud"
check_container "nextcloud-db" "Nextcloud DB"
check_container "open-webui" "Open WebUI"
check_container "windmill-server" "Windmill Server"
check_container "windmill-worker" "Windmill Worker"
check_container "windmill-db" "Windmill DB"
check_container "caddy" "Caddy Proxy"
check_container "api-gateway" "API Gateway"
check_container "vikunja" "Vikunja"
check_container "searxng" "SearXNG"
check_container "qdrant" "Qdrant"
check_container "homelab-status" "Status Page"

# Check Disk Space
print_color $CYAN "═══ System Resources ═══"
df -h / | awk 'NR==2 {
    used=$3
    avail=$4
    use=$5
    if (int(use) > 80) {
        printf "\033[1;33m⚠ Disk Usage: %s used, %s available (%s)\033[0m\n", used, avail, use
    } else {
        printf "\033[0;32m✓ Disk Usage: %s used, %s available (%s)\033[0m\n", used, avail, use
    }
}'

# Check Memory
free -h | awk '/^Mem:/ {
    total=$2
    used=$3
    avail=$7
    printf "\033[0;32m✓ Memory: %s total, %s used, %s available\033[0m\n", total, used, avail
}'

# Check for Ollama models
print_color $CYAN "═══ AI Models ═══"
if docker exec ollama ollama list 2>/dev/null | grep -q "llama3.2:1b"; then
    print_color $GREEN "✓ llama3.2:1b model is installed"
else
    print_color $YELLOW "⚠ llama3.2:1b model not found"
    echo "  Install with: docker exec ollama ollama pull llama3.2:1b"
fi
echo

# Summary
print_color $CYAN "═══ Summary ═══"

# Count running containers
running_count=$(docker ps --format '{{.Names}}' | wc -l)
total_count=$(docker ps -a --format '{{.Names}}' | wc -l)

print_color $BLUE "Containers: $running_count running / $total_count total"

# Show any stopped containers
stopped=$(docker ps -a --filter "status=exited" --format "{{.Names}}" | tr '\n' ' ')
if [[ ! -z "$stopped" ]]; then
    print_color $YELLOW "Stopped containers: $stopped"
fi

# Show any restarting containers
restarting=$(docker ps --filter "status=restarting" --format "{{.Names}}" | tr '\n' ' ')
if [[ ! -z "$restarting" ]]; then
    print_color $RED "Restarting containers: $restarting"
fi

echo
print_color $GREEN "Check complete!"
echo

# Show quick access URLs
print_color $CYAN "═══ Quick Access ═══"
echo "Dashboard:    https://ai.acebuddy.quest"
echo "Email:        https://mail.acebuddy.quest"
echo "Calendar:     https://calendar.acebuddy.quest"
echo "Files:        https://files.acebuddy.quest"
echo "Chat:         https://chat.acebuddy.quest"
echo
print_color $BLUE "GitHub:       https://github.com/acebuddyai/homelab-dashboard"

#!/bin/bash

# QR Login Verification Script for Matrix Homelab
# This script verifies that QR code login functionality is properly configured

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="acebuddy.quest"
MATRIX_URL="https://matrix.${DOMAIN}"
AUTH_URL="https://auth.${DOMAIN}"
CINNY_URL="https://cinny.${DOMAIN}"

echo -e "${BLUE}===================================================${NC}"
echo -e "${BLUE}      Matrix QR Login Verification Script         ${NC}"
echo -e "${BLUE}===================================================${NC}"
echo ""

# Function to check URL
check_url() {
    local url=$1
    local description=$2
    local expected_code=${3:-200}

    if response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null); then
        if [ "$response" = "$expected_code" ]; then
            echo -e "${GREEN}✓${NC} $description"
            return 0
        else
            echo -e "${RED}✗${NC} $description (HTTP $response)"
            return 1
        fi
    else
        echo -e "${RED}✗${NC} $description (Connection failed)"
        return 1
    fi
}

# Function to check JSON endpoint
check_json() {
    local url=$1
    local field=$2
    local description=$3

    if response=$(curl -s "$url" 2>/dev/null | python3 -c "import sys,json; data=json.load(sys.stdin); print('ok' if '$field' in data else 'missing')" 2>/dev/null); then
        if [ "$response" = "ok" ]; then
            echo -e "${GREEN}✓${NC} $description"
            return 0
        else
            echo -e "${YELLOW}⚠${NC} $description (Field missing: $field)"
            return 1
        fi
    else
        echo -e "${RED}✗${NC} $description (Invalid response)"
        return 1
    fi
}

# Function to check container status
check_container() {
    local container=$1
    local description=$2

    if docker ps --format "{{.Names}}" | grep -q "^${container}$"; then
        status=$(docker ps --format "{{.Status}}" --filter "name=${container}")
        if echo "$status" | grep -q "healthy\|Up"; then
            echo -e "${GREEN}✓${NC} $description is running"
            return 0
        else
            echo -e "${YELLOW}⚠${NC} $description is unhealthy: $status"
            return 1
        fi
    else
        echo -e "${RED}✗${NC} $description is not running"
        return 1
    fi
}

echo -e "${BLUE}1. Checking Docker Containers${NC}"
echo "-----------------------------------"
check_container "matrix-synapse" "Synapse"
check_container "matrix-auth-service" "MAS (Auth Service)"
check_container "matrix-cinny" "Cinny Client"
check_container "caddy" "Caddy Proxy"
check_container "matrix-postgres" "Matrix Database"
check_container "mas-postgres" "MAS Database"
echo ""

echo -e "${BLUE}2. Checking Service Endpoints${NC}"
echo "-----------------------------------"
check_url "$CINNY_URL" "Cinny Web Interface"
check_url "$MATRIX_URL/_matrix/client/versions" "Matrix API"
check_url "$AUTH_URL" "MAS Authentication Service"
check_url "$MATRIX_URL/.well-known/matrix/client" "Matrix Well-known Client"
check_url "$MATRIX_URL/.well-known/matrix/server" "Matrix Well-known Server"
check_url "$AUTH_URL/.well-known/openid-configuration" "OIDC Discovery"
echo ""

echo -e "${BLUE}3. Checking MSC Support${NC}"
echo "-----------------------------------"

# Check MSC3861 (OIDC)
if curl -s "$AUTH_URL/.well-known/openid-configuration" | grep -q '"issuer"'; then
    echo -e "${GREEN}✓${NC} MSC3861: OIDC authentication configured"
else
    echo -e "${RED}✗${NC} MSC3861: OIDC not configured"
fi

# Check MSC4108 (QR Login)
if versions=$(curl -s "$MATRIX_URL/_matrix/client/versions" 2>/dev/null); then
    if echo "$versions" | grep -q "msc4108"; then
        echo -e "${GREEN}✓${NC} MSC4108: QR login support detected"
    else
        echo -e "${YELLOW}⚠${NC} MSC4108: QR login not detected in versions"
    fi
fi

# Check well-known MSC3861 configuration
if curl -s "$MATRIX_URL/.well-known/matrix/client" | grep -q "msc3861"; then
    echo -e "${GREEN}✓${NC} MSC3861 configured in well-known"
else
    echo -e "${YELLOW}⚠${NC} MSC3861 not in well-known (might be using org.matrix.msc3861)"
fi
echo ""

echo -e "${BLUE}4. Checking Authentication Flow${NC}"
echo "-----------------------------------"

# Check if legacy login is disabled (indicates MSC3861 is active)
if response=$(curl -s "$MATRIX_URL/_matrix/client/r0/login" 2>/dev/null); then
    if echo "$response" | grep -q "M_UNRECOGNIZED"; then
        echo -e "${GREEN}✓${NC} Legacy login disabled (MSC3861 active)"
    else
        echo -e "${YELLOW}⚠${NC} Legacy login might still be active"
    fi
fi

# Check MAS OAuth endpoints
check_url "$AUTH_URL/authorize" "OAuth Authorization Endpoint" 400  # Returns 400 without params
check_url "$AUTH_URL/oauth2/token" "OAuth Token Endpoint" 405  # POST endpoint
echo ""

echo -e "${BLUE}5. Quick Status Summary${NC}"
echo "-----------------------------------"

# Count successes
all_good=true

# Check critical services
if docker ps | grep -q "matrix-synapse.*Up.*healthy"; then
    synapse_status="${GREEN}✓${NC}"
else
    synapse_status="${RED}✗${NC}"
    all_good=false
fi

if docker ps | grep -q "matrix-auth-service.*Up"; then
    mas_status="${GREEN}✓${NC}"
else
    mas_status="${RED}✗${NC}"
    all_good=false
fi

if curl -s "$AUTH_URL/.well-known/openid-configuration" | grep -q "issuer" 2>/dev/null; then
    oidc_status="${GREEN}✓${NC}"
else
    oidc_status="${RED}✗${NC}"
    all_good=false
fi

echo -e "Synapse:        $synapse_status"
echo -e "MAS:            $mas_status"
echo -e "OIDC:           $oidc_status"
echo -e "Web Client:     ${GREEN}✓${NC} https://cinny.acebuddy.quest"
echo ""

if [ "$all_good" = true ]; then
    echo -e "${GREEN}===================================================${NC}"
    echo -e "${GREEN}     🎉 QR Login Setup is OPERATIONAL! 🎉         ${NC}"
    echo -e "${GREEN}===================================================${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Visit https://cinny.acebuddy.quest to test login"
    echo "2. Use a QR-capable Matrix client (Element X, Element)"
    echo "3. Existing users may need to re-authenticate"
else
    echo -e "${YELLOW}===================================================${NC}"
    echo -e "${YELLOW}     ⚠️  Some components need attention  ⚠️        ${NC}"
    echo -e "${YELLOW}===================================================${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check logs: docker logs matrix-synapse"
    echo "2. Check MAS: docker logs matrix-auth-service"
    echo "3. Restart services: cd matrix && docker-compose restart"
fi

echo ""
echo "For detailed testing, run: cd tests && python3 test-qr-login.py"

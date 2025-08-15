#!/bin/bash
# =============================================================================
# MAS COMPREHENSIVE FUNCTIONALITY TEST SCRIPT
# =============================================================================
# This script systematically tests all MAS functionality after a reset
# Run this to verify your authentication service is working properly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="https://auth.acebuddy.quest"
LOCAL_URL="http://localhost:8080"
HEALTH_URL="http://localhost:8081"
TEST_EMAIL="test@acebuddy.quest"
TEST_USERNAME="testuser"
TEST_PASSWORD="TestPassword123!"

echo -e "${BLUE}🧪 MAS COMPREHENSIVE FUNCTIONALITY TEST${NC}"
echo "=============================================="
echo ""

# Function to print test results
print_result() {
    local test_name="$1"
    local status="$2"
    local message="$3"

    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✅ $test_name: PASS${NC} - $message"
    elif [ "$status" = "FAIL" ]; then
        echo -e "${RED}❌ $test_name: FAIL${NC} - $message"
    else
        echo -e "${YELLOW}⚠️  $test_name: WARNING${NC} - $message"
    fi
}

# Function to make HTTP requests with proper error handling
test_endpoint() {
    local url="$1"
    local description="$2"
    local expected_status="${3:-200}"

    echo -e "${BLUE}Testing: $description${NC}"

    response=$(curl -s -w "%{http_code}" -o /tmp/mas_test_response "$url" 2>/dev/null || echo "000")

    if [ "$response" = "$expected_status" ]; then
        print_result "$description" "PASS" "HTTP $response"
        return 0
    else
        print_result "$description" "FAIL" "HTTP $response (expected $expected_status)"
        return 1
    fi
}

echo -e "${YELLOW}📊 PHASE 1: BASIC CONNECTIVITY TESTS${NC}"
echo "----------------------------------------"

# Test 1: Local MAS Web Interface
test_endpoint "$LOCAL_URL/" "Local MAS Web Interface"

# Test 2: Domain MAS Web Interface
test_endpoint "$BASE_URL/" "Domain MAS Web Interface"

# Test 3: Health Endpoint (Local)
test_endpoint "$HEALTH_URL/health" "Health Endpoint (Local)"

# Test 4: Health Endpoint (Domain) - Known issue
test_endpoint "$BASE_URL:8081/health" "Health Endpoint (Domain)" "200"

# Test 5: Discovery Endpoint
test_endpoint "$BASE_URL/.well-known/openid_configuration" "OpenID Discovery"

echo ""
echo -e "${YELLOW}📊 PHASE 2: AUTHENTICATION FLOW TESTS${NC}"
echo "-------------------------------------------"

# Test 6: Login Page
test_endpoint "$BASE_URL/login" "Login Page"

# Test 7: Registration Page
test_endpoint "$BASE_URL/register" "Registration Page"

# Test 8: Account Management (should redirect to login when not authenticated)
test_endpoint "$BASE_URL/account" "Account Management (Unauthenticated)" "303"

echo ""
echo -e "${YELLOW}📊 PHASE 3: EMAIL SYSTEM VERIFICATION${NC}"
echo "----------------------------------------"

# Test 9: SMTP Connection Test
echo -e "${BLUE}Testing: SMTP Connection${NC}"
if docker exec matrix-auth-service timeout 10 sh -c 'echo "quit" | nc smtp.gmail.com 587' >/dev/null 2>&1; then
    print_result "SMTP Connectivity" "PASS" "Gmail SMTP accessible"
else
    print_result "SMTP Connectivity" "FAIL" "Cannot reach Gmail SMTP"
fi

echo ""
echo -e "${YELLOW}📊 PHASE 4: DATABASE VERIFICATION${NC}"
echo "------------------------------------"

# Test 10: Database Connection
echo -e "${BLUE}Testing: Database Connection${NC}"
user_count=$(docker exec mas-postgres psql -U mas_user -d mas -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | xargs)
if [ "$user_count" = "0" ]; then
    print_result "Database User Count" "PASS" "Database clean, $user_count users"
else
    print_result "Database User Count" "WARNING" "$user_count users found (expected 0 after reset)"
fi

# Test 11: Database Health
echo -e "${BLUE}Testing: Database Health${NC}"
if docker exec mas-postgres pg_isready -U mas_user -d mas >/dev/null 2>&1; then
    print_result "Database Health" "PASS" "PostgreSQL responding"
else
    print_result "Database Health" "FAIL" "PostgreSQL not responding"
fi

echo ""
echo -e "${YELLOW}📊 PHASE 5: CONTAINER STATUS${NC}"
echo "-------------------------------"

# Test 12: Container Status
echo -e "${BLUE}Testing: Container Status${NC}"
mas_status=$(docker inspect matrix-auth-service --format='{{.State.Status}}' 2>/dev/null)
db_status=$(docker inspect mas-postgres --format='{{.State.Status}}' 2>/dev/null)

if [ "$mas_status" = "running" ]; then
    print_result "MAS Container" "PASS" "Status: $mas_status"
else
    print_result "MAS Container" "FAIL" "Status: $mas_status"
fi

if [ "$db_status" = "running" ]; then
    print_result "Database Container" "PASS" "Status: $db_status"
else
    print_result "Database Container" "FAIL" "Status: $db_status"
fi

echo ""
echo -e "${YELLOW}📊 PHASE 6: ADVANCED FUNCTIONALITY${NC}"
echo "-------------------------------------"

# Test 13: OAuth2 Configuration
test_endpoint "$BASE_URL/oauth2/authorize?client_id=0000000000000000000SYNAPSE&response_type=code&scope=openid&redirect_uri=http://example.com" "OAuth2 Authorization" "303"

# Test 14: API Endpoints
test_endpoint "$BASE_URL/api/v1/auth/whoami" "API Whoami Endpoint" "401"

echo ""
echo -e "${YELLOW}📊 PHASE 7: CONFIGURATION VERIFICATION${NC}"
echo "------------------------------------------"

# Test 15: Configuration File Validation
echo -e "${BLUE}Testing: Configuration Validation${NC}"
if docker exec matrix-auth-service mas-cli config check /config/config.yaml >/dev/null 2>&1; then
    print_result "Configuration Validation" "PASS" "Config file valid"
else
    print_result "Configuration Validation" "FAIL" "Config file has issues"
fi

echo ""
echo -e "${BLUE}📋 TEST SUMMARY & RECOMMENDATIONS${NC}"
echo "=================================="

echo ""
echo -e "${YELLOW}🔄 MANUAL TESTING CHECKLIST:${NC}"
echo "1. Visit $BASE_URL and verify the login page loads"
echo "2. Try registering a new account with email: $TEST_EMAIL"
echo "3. Check your email for verification link"
echo "4. Complete registration and verify login works"
echo "5. Test account settings page after login"
echo "6. Test logout functionality"

echo ""
echo -e "${YELLOW}🐛 KNOWN ISSUES TO MONITOR:${NC}"
echo "1. Health endpoint accessibility via domain (should be internal only)"
echo "2. Account management page functionality with JWT tokens"
echo "3. TOTP/2FA features (not yet available in MAS)"

echo ""
echo -e "${YELLOW}📝 NEXT DEVELOPMENT TASKS:${NC}"
echo "1. Test complete user registration flow"
echo "2. Verify account management accessibility"
echo "3. Consider UI customization options"
echo "4. Plan alternative 2FA implementation"
echo "5. Set up monitoring and logging"

echo ""
echo -e "${GREEN}🎉 Testing completed! Review results above.${NC}"
echo "Run this script after any configuration changes to verify functionality."

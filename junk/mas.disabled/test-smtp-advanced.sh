#!/bin/bash
# =============================================================================
# Advanced SMTP Testing Script for Gmail - MAS Email Debug
# =============================================================================

set -e

echo "🔍 Advanced SMTP Testing for Gmail..."
echo "=================================================="

# Load environment variables
if [ -f "../.env" ]; then
    source ../.env
    echo "✅ Loaded environment from ../.env"
else
    echo "❌ Warning: ../.env file not found!"
    echo "💡 Make sure you're running this from the mas/ directory"
fi

echo ""
echo "📧 Current SMTP settings:"
echo "   Host: ${SMTP_HOST:-'NOT SET'}"
echo "   Port: ${SMTP_PORT:-'NOT SET'}"
echo "   User: ${SMTP_USER:-'NOT SET'}"
echo "   Pass: ${SMTP_PASSWORD:0:4}***${SMTP_PASSWORD: -4}"
echo ""

# Test 1: Basic TCP connectivity
echo "🧪 Test 1: Basic TCP connection to Gmail..."
if timeout 10s bash -c "</dev/tcp/${SMTP_HOST:-smtp.gmail.com}/${SMTP_PORT:-587}" 2>/dev/null; then
    echo "✅ TCP connection to ${SMTP_HOST:-smtp.gmail.com}:${SMTP_PORT:-587} works"
else
    echo "❌ TCP connection failed - checking firewall/network issues"
fi

echo ""

# Test 2: Test both Gmail ports
echo "🧪 Test 2: Testing both Gmail SMTP ports..."
timeout 5s bash -c "</dev/tcp/smtp.gmail.com/587" 2>/dev/null && echo "✅ Port 587 (STARTTLS) accessible" || echo "❌ Port 587 blocked"
timeout 5s bash -c "</dev/tcp/smtp.gmail.com/465" 2>/dev/null && echo "✅ Port 465 (TLS) accessible" || echo "❌ Port 465 blocked"

echo ""

# Test 3: SSL/TLS handshake test
echo "🧪 Test 3: SSL/TLS handshake test..."
echo "Testing STARTTLS on port 587:"
if echo "QUIT" | timeout 15s openssl s_client -connect smtp.gmail.com:587 -starttls smtp -quiet 2>/dev/null | grep -q "250"; then
    echo "✅ STARTTLS handshake successful on port 587"
else
    echo "❌ STARTTLS handshake failed on port 587"
fi

echo ""
echo "Testing direct TLS on port 465:"
if echo "QUIT" | timeout 15s openssl s_client -connect smtp.gmail.com:465 -quiet 2>/dev/null | grep -q "220"; then
    echo "✅ Direct TLS handshake successful on port 465"
else
    echo "❌ Direct TLS handshake failed on port 465"
fi

echo ""

# Test 4: SMTP EHLO command
echo "🧪 Test 4: SMTP EHLO command test..."
{
echo "EHLO localhost"
sleep 2
echo "QUIT"
} | timeout 15s nc smtp.gmail.com 587 2>/dev/null | head -20 && echo "✅ SMTP EHLO works" || echo "❌ SMTP EHLO failed"

echo ""

# Test 5: Full SMTP authentication test
echo "🧪 Test 5: Full SMTP authentication test..."
if [ -n "$SMTP_USER" ] && [ -n "$SMTP_PASSWORD" ]; then
    # Create base64 encoded credentials
    AUTH_STRING=$(echo -ne "\000${SMTP_USER}\000${SMTP_PASSWORD}" | base64 | tr -d '\n')

    echo "Testing SMTP AUTH with your credentials..."
    {
        echo "EHLO localhost"
        sleep 1
        echo "STARTTLS"
        sleep 2
        echo "EHLO localhost"
        sleep 1
        echo "AUTH PLAIN ${AUTH_STRING}"
        sleep 2
        echo "QUIT"
    } | timeout 20s openssl s_client -connect smtp.gmail.com:587 -starttls smtp -quiet 2>/dev/null | grep -E "(250|235|221)" && echo "✅ SMTP authentication successful" || echo "❌ SMTP authentication failed"
else
    echo "⚠️  Skipping auth test - SMTP credentials not set"
fi

echo ""

# Test 6: Environment variable verification
echo "🧪 Test 6: Environment variables check..."
echo "Required variables status:"
[ -n "$SMTP_HOST" ] && echo "✅ SMTP_HOST: $SMTP_HOST" || echo "❌ SMTP_HOST: Not set"
[ -n "$SMTP_PORT" ] && echo "✅ SMTP_PORT: $SMTP_PORT" || echo "❌ SMTP_PORT: Not set"
[ -n "$SMTP_USER" ] && echo "✅ SMTP_USER: $SMTP_USER" || echo "❌ SMTP_USER: Not set"
[ -n "$SMTP_PASSWORD" ] && echo "✅ SMTP_PASSWORD: ***set***" || echo "❌ SMTP_PASSWORD: Not set"
[ -n "$MATRIX_DOMAIN" ] && echo "✅ MATRIX_DOMAIN: $MATRIX_DOMAIN" || echo "❌ MATRIX_DOMAIN: Not set"

echo ""

# Test 7: Docker container environment check
echo "🧪 Test 7: Docker container environment check..."
if docker ps -q -f name=matrix-auth-service >/dev/null 2>&1; then
    echo "✅ MAS container is running"
    echo "Container environment variables:"
    docker exec matrix-auth-service env 2>/dev/null | grep -E "(SMTP|EMAIL|MATRIX)" | sort || echo "❌ Cannot access container environment"
else
    echo "⚠️  MAS container not running - start with 'docker-compose up -d'"
fi

echo ""

# Test 8: MAS config verification
echo "🧪 Test 8: MAS configuration verification..."
if [ -f "config.yaml" ]; then
    echo "✅ config.yaml exists"
    if grep -q "smtp" config.yaml; then
        echo "✅ SMTP configuration found in config.yaml"
        echo "Email config snippet:"
        grep -A 10 "email:" config.yaml | head -15
    else
        echo "❌ No SMTP configuration in config.yaml"
    fi
else
    echo "❌ config.yaml not found - run ./generate-config.sh"
fi

echo ""
echo "=================================================="
echo "📋 **TEST SUMMARY & RECOMMENDATIONS**"
echo "=================================================="

# Provide recommendations based on test results
if timeout 5s bash -c "</dev/tcp/smtp.gmail.com/587" 2>/dev/null; then
    echo "✅ RECOMMENDATION: Use port 587 with STARTTLS"
    echo "   Add to .env: SMTP_PORT=587"
    echo "   Config mode: start_tls"
else
    echo "🔄 RECOMMENDATION: Try port 465 with direct TLS"
    echo "   Add to .env: SMTP_PORT=465"
    echo "   Config mode: tls"
fi

echo ""
echo "🚀 **NEXT STEPS:**"
echo "1. Run: ./generate-config.sh"
echo "2. Run: docker-compose up -d"
echo "3. Monitor logs: docker logs -f matrix-auth-service"
echo "4. Test registration at: https://auth.${MATRIX_DOMAIN:-your-domain}/"

echo ""
echo "🐛 **DEBUG COMMANDS:**"
echo "• Watch email logs: docker logs -f matrix-auth-service 2>&1 | grep -i 'email\\|smtp\\|mail\\|lettre'"
echo "• Check config: docker exec matrix-auth-service mas-cli config dump | grep -A 20 email"
echo "• Restart service: docker-compose restart matrix-auth-service"

echo ""
echo "📞 **TROUBLESHOOTING:**"
echo "If emails still don't work:"
echo "1. Check Gmail app password is exactly 16 characters"
echo "2. Verify Gmail account has 2FA enabled"
echo "3. Try port 465 with mode: tls instead of start_tls"
echo "4. Check Gmail 'Less secure app access' settings"

echo ""
echo "Test completed at: $(date)"

#!/bin/bash
# =============================================================================
# MAS Startup Script with Proper Environment Loading
# =============================================================================

set -e

echo "🚀 Starting Matrix Authentication Service with SMTP support..."
echo "=============================================================="

# Navigate to MAS directory
cd "$(dirname "$0")"
MAS_DIR=$(pwd)
echo "📁 Working directory: $MAS_DIR"

# Load environment variables
if [ -f "../.env" ]; then
    echo "📋 Loading environment from ../.env"
    set -a  # automatically export all variables
    source ../.env
    set +a  # stop auto-exporting
    echo "✅ Environment loaded successfully"
else
    echo "❌ ERROR: ../.env file not found!"
    echo "💡 Please ensure .env file exists in the homelab root directory"
    exit 1
fi

echo ""
echo "📧 SMTP Configuration Check:"
echo "   Host: ${SMTP_HOST:-'NOT SET'}"
echo "   Port: ${SMTP_PORT:-'NOT SET'}"
echo "   User: ${SMTP_USER:-'NOT SET'}"
echo "   Pass: ${SMTP_PASSWORD:0:4}***${SMTP_PASSWORD: -4}"
echo "   Domain: ${MATRIX_DOMAIN:-'NOT SET'}"

# Verify critical variables
MISSING_VARS=()
[ -z "$SMTP_HOST" ] && MISSING_VARS+=("SMTP_HOST")
[ -z "$SMTP_PORT" ] && MISSING_VARS+=("SMTP_PORT")
[ -z "$SMTP_USER" ] && MISSING_VARS+=("SMTP_USER")
[ -z "$SMTP_PASSWORD" ] && MISSING_VARS+=("SMTP_PASSWORD")
[ -z "$MATRIX_DOMAIN" ] && MISSING_VARS+=("MATRIX_DOMAIN")
[ -z "$MAS_POSTGRES_PASSWORD" ] && MISSING_VARS+=("MAS_POSTGRES_PASSWORD")

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo ""
    echo "❌ ERROR: Missing required environment variables:"
    printf "   - %s\n" "${MISSING_VARS[@]}"
    echo ""
    echo "💡 Please add these to your ../.env file"
    exit 1
fi

echo ""
echo "🔧 Regenerating MAS configuration..."
./generate-config.sh

echo ""
echo "🐳 Starting Docker services..."

# Export environment for docker-compose
export SMTP_HOST
export SMTP_PORT
export SMTP_USER
export SMTP_PASSWORD
export MATRIX_DOMAIN
export MAS_POSTGRES_PASSWORD
export MAS_ENCRYPTION_KEY
export MATRIX_SECRET
export SYNAPSE_CLIENT_SECRET

# Start services
docker-compose up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "🔍 Checking MAS container environment..."
if docker exec matrix-auth-service env | grep -q SMTP_HOST; then
    echo "✅ SMTP environment variables loaded in container:"
    docker exec matrix-auth-service env | grep -E "(SMTP|MATRIX_DOMAIN)" | sort
else
    echo "❌ SMTP environment variables not found in container"
    echo "🔧 Container environment:"
    docker exec matrix-auth-service env | grep -E "(SMTP|MATRIX|MAS)" | sort || echo "No relevant env vars found"
fi

echo ""
echo "📧 Email configuration in MAS:"
docker exec matrix-auth-service mas-cli config dump 2>/dev/null | grep -A 15 "email:" || echo "❌ Cannot dump MAS config"

echo ""
echo "🎯 **READY FOR TESTING!**"
echo "=============================================================="
echo "✅ MAS is running with Gmail SMTP configuration"
echo "🌐 Web interface: https://auth.${MATRIX_DOMAIN}/"
echo "📧 Email from: acebuddyai@gmail.com"
echo ""
echo "🧪 **Test Steps:**"
echo "1. Open: https://auth.${MATRIX_DOMAIN}/"
echo "2. Click 'Register' or 'Forgot Password'"
echo "3. Enter a test email address"
echo "4. Watch for email delivery"
echo ""
echo "🐛 **Debug Commands:**"
echo "• Watch email logs: docker logs -f matrix-auth-service 2>&1 | grep -i 'email\\|smtp\\|mail\\|lettre'"
echo "• Restart MAS: docker-compose restart matrix-auth-service"
echo "• Check health: curl -s http://localhost:8081/health"
echo ""
echo "🔧 **If emails don't work, try:**"
echo "1. Check Gmail spam folder"
echo "2. Verify Gmail app password (16 chars)"
echo "3. Try port 465 with TLS mode instead"
echo ""
echo "Startup completed at: $(date)"

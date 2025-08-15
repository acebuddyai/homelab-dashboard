#!/bin/bash
# =============================================================================
# SMTP Email Testing Script for MAS
# =============================================================================

echo "📧 Testing SMTP configuration for MAS..."

# Load environment variables
if [ -f "../.env" ]; then
    export $(grep -v "^#" ../.env | xargs)
else
    echo "❌ Error: ../.env file not found!"
    exit 1
fi

echo "🔍 SMTP Settings from environment:"
echo "   Host: $SMTP_HOST"
echo "   Port: $SMTP_PORT"
echo "   User: $SMTP_USER"
echo "   Password: ${SMTP_PASSWORD:0:4}***${SMTP_PASSWORD: -4}"
echo ""

# Test SMTP connection using openssl
echo "🧪 Testing SMTP connection with STARTTLS..."
timeout 10s openssl s_client -connect $SMTP_HOST:$SMTP_PORT -starttls smtp -quit 2>/dev/null && echo "✅ SMTP connection successful" || echo "❌ SMTP connection failed"

echo ""
echo "📋 Next steps:"
echo "1. Go to https://auth.acebuddy.quest/"
echo "2. Try 'Register' or 'Forgot Password'"
echo "3. Watch logs: docker logs -f matrix-auth-service | grep -i email"

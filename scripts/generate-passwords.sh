#!/bin/bash

# Generate secure passwords for Homelab AI Assistant
# This script generates cryptographically secure passwords and updates the .env file

set -e

echo "🔐 Generating secure passwords for Homelab AI Assistant..."

# Function to generate secure password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Function to generate token
generate_token() {
    openssl rand -hex 32
}

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env from template..."
    cp .env.template .env
fi

# Backup existing .env
if [ -f .env ]; then
    echo "💾 Backing up existing .env to .env.backup..."
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
fi

# Generate passwords
echo "🔑 Generating passwords..."

WINDMILL_DB_PASSWORD=$(generate_password)
POSTGRES_PASSWORD=$(generate_password)
JWT_SECRET=$(generate_token)
WINDMILL_TOKEN=$(generate_token)
SEARXNG_SECRET=$(generate_password)
REDIS_PASSWORD=$(generate_password)
QDRANT_API_KEY=$(generate_token)
GRAFANA_ADMIN_PASSWORD=$(generate_password)

# Update .env file
echo "📝 Updating .env file..."

# Function to update or add environment variable
update_env() {
    local key=$1
    local value=$2

    if grep -q "^${key}=" .env; then
        # Update existing
        sed -i.bak "s|^${key}=.*|${key}=${value}|" .env
    else
        # Add new
        echo "${key}=${value}" >> .env
    fi
}

# Update all passwords
update_env "WINDMILL_DB_PASSWORD" "$WINDMILL_DB_PASSWORD"
update_env "POSTGRES_PASSWORD" "$POSTGRES_PASSWORD"
update_env "JWT_SECRET" "$JWT_SECRET"
update_env "WINDMILL_TOKEN" "$WINDMILL_TOKEN"
update_env "SEARXNG_SECRET" "$SEARXNG_SECRET"
update_env "REDIS_PASSWORD" "$REDIS_PASSWORD"
update_env "QDRANT_API_KEY" "$QDRANT_API_KEY"
update_env "GRAFANA_ADMIN_PASSWORD" "$GRAFANA_ADMIN_PASSWORD"

# Clean up backup files
rm -f .env.bak

# Save passwords to a secure file (optional)
if [ "$1" == "--save" ]; then
    echo "💾 Saving passwords to passwords.txt (KEEP THIS SECURE!)..."
    cat > passwords.txt << EOF
===========================================
Homelab AI Assistant - Generated Passwords
Generated: $(date)
===========================================

Database Passwords:
-------------------
WINDMILL_DB_PASSWORD: $WINDMILL_DB_PASSWORD
POSTGRES_PASSWORD: $POSTGRES_PASSWORD
REDIS_PASSWORD: $REDIS_PASSWORD

API Keys & Tokens:
------------------
JWT_SECRET: $JWT_SECRET
WINDMILL_TOKEN: $WINDMILL_TOKEN
SEARXNG_SECRET: $SEARXNG_SECRET
QDRANT_API_KEY: $QDRANT_API_KEY

Admin Passwords:
----------------
GRAFANA_ADMIN_PASSWORD: $GRAFANA_ADMIN_PASSWORD

===========================================
⚠️  IMPORTANT: Store this file securely!
===========================================
EOF
    chmod 600 passwords.txt
    echo "⚠️  passwords.txt created - store it securely and delete after saving!"
fi

echo ""
echo "✅ Password generation complete!"
echo ""
echo "🔒 Security Recommendations:"
echo "  1. Review the .env file"
echo "  2. Change default usernames if needed"
echo "  3. Enable 2FA where possible"
echo "  4. Use a password manager for production"
echo "  5. Rotate passwords regularly"
echo ""

# Display summary
echo "📊 Summary:"
echo "  - Passwords generated: 8"
echo "  - .env file updated: ✓"
echo "  - Backup created: .env.backup.$(date +%Y%m%d_%H%M%S)"
echo ""
echo "Next step: Run './scripts/initialize.sh' to initialize the system"

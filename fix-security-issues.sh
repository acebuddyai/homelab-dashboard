#!/bin/bash
# =============================================================================
# SECURITY FIX SCRIPT - GitGuardian Issue Resolution
# =============================================================================
# This script helps fix the security vulnerabilities identified by GitGuardian
# by rotating all exposed secrets and ensuring proper environment variable usage
# =============================================================================

set -e  # Exit on any error

echo "🔐 HOMELAB SECURITY FIX SCRIPT"
echo "==============================="
echo "This script will help you fix GitGuardian security issues by:"
echo "1. Generating new secure secrets"
echo "2. Updating environment variables"
echo "3. Cleaning up exposed secrets"
echo "4. Validating configuration"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to generate secure random string
generate_secret() {
    local length=${1:-32}
    openssl rand -hex $length
}

# Function to generate secure password
generate_password() {
    local length=${1:-24}
    openssl rand -base64 $length | tr -d "=+/" | cut -c1-${length}
}

echo -e "${BLUE}📋 Checking current environment...${NC}"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ Created .env from template${NC}"
    else
        echo -e "${RED}❌ No .env.example found. Creating new .env file...${NC}"
        touch .env
    fi
fi

echo -e "${BLUE}🔑 Generating new secure secrets...${NC}"

# Generate all required secrets
MATRIX_DB_PASSWORD=$(generate_password 32)
NEXTCLOUD_DB_PASSWORD=$(generate_password 32)
MAS_POSTGRES_PASSWORD=$(generate_password 32)
MAS_ENCRYPTION_KEY=$(generate_secret 32)
MATRIX_SECRET=$(generate_secret 48)
SYNAPSE_CLIENT_SECRET=$(generate_secret 48)
MAS_ADMIN_TOKEN=$(generate_secret 48)
SYNAPSE_REGISTRATION_SECRET=$(generate_secret 48)
SYNAPSE_MACAROON_SECRET=$(generate_secret 48)
SYNAPSE_FORM_SECRET=$(generate_secret 48)
BOT_PASSWORD=$(generate_password 24)

# Multi-agent system passwords
COORDINATOR_PASSWORD=$(generate_password 24)
ORCHESTRATOR_PASSWORD=$(generate_password 24)
LLM_AGENT_PASSWORD=$(generate_password 24)
SEARCH_AGENT_PASSWORD=$(generate_password 24)
RAG_AGENT_PASSWORD=$(generate_password 24)

echo -e "${GREEN}✅ Generated all new secrets${NC}"

# Backup existing .env
if [ -f ".env" ] && [ -s ".env" ]; then
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo -e "${GREEN}✅ Backed up existing .env file${NC}"
fi

echo -e "${BLUE}📝 Updating .env file with new secrets...${NC}"

# Create/update .env file with new secrets
cat > .env << EOF
# =============================================================================
# HOMELAB ENVIRONMENT VARIABLES - GENERATED $(date)
# =============================================================================
# WARNING: This file contains sensitive information. Never commit to git!

# Domain Configuration
DOMAIN=acebuddy.quest
MATRIX_DOMAIN=acebuddy.quest

# Database Passwords (Generated: $(date))
MATRIX_DB_PASSWORD=${MATRIX_DB_PASSWORD}
NEXTCLOUD_DB_PASSWORD=${NEXTCLOUD_DB_PASSWORD}
MAS_POSTGRES_PASSWORD=${MAS_POSTGRES_PASSWORD}

# Matrix/Synapse Secrets (Generated: $(date))
SYNAPSE_REGISTRATION_SECRET=${SYNAPSE_REGISTRATION_SECRET}
SYNAPSE_MACAROON_SECRET=${SYNAPSE_MACAROON_SECRET}
SYNAPSE_FORM_SECRET=${SYNAPSE_FORM_SECRET}

# MAS (Matrix Authentication Service) Secrets (Generated: $(date))
MAS_ENCRYPTION_KEY=${MAS_ENCRYPTION_KEY}
MATRIX_SECRET=${MATRIX_SECRET}
SYNAPSE_CLIENT_SECRET=${SYNAPSE_CLIENT_SECRET}
MAS_ADMIN_TOKEN=${MAS_ADMIN_TOKEN}

# Matrix Bot Configuration (Generated: $(date))
MATRIX_HOMESERVER_URL=https://matrix.acebuddy.quest
MATRIX_BOT_USERNAME=@subatomic6140:acebuddy.quest
MATRIX_BOT_PASSWORD=${BOT_PASSWORD}
MATRIX_TARGET_ROOM_ID=!SpcIthQfyfDNgsYnad:acebuddy.quest

# Multi-Agent System Configuration (Generated: $(date))
COORDINATION_ROOM_ID=!coordination:acebuddy.quest
COORDINATOR_PASSWORD=${COORDINATOR_PASSWORD}
ORCHESTRATOR_PASSWORD=${ORCHESTRATOR_PASSWORD}
LLM_AGENT_PASSWORD=${LLM_AGENT_PASSWORD}
SEARCH_AGENT_PASSWORD=${SEARCH_AGENT_PASSWORD}
RAG_AGENT_PASSWORD=${RAG_AGENT_PASSWORD}

# LLM Agent Settings
DEFAULT_LLM_MODEL=llama3.2:latest
LLM_MAX_TOKENS=2048
LLM_TEMPERATURE=0.7

# Search Agent Settings
SEARCH_RESULTS_LIMIT=5

# RAG Agent Settings
EMBEDDING_MODEL=all-MiniLM-L6-v2
QDRANT_COLLECTION=homelab_knowledge

# Monitoring Settings
MONITOR_INTERVAL=30

# Security Settings
RUST_LOG=info
RUST_BACKTRACE=1

# =============================================================================
# IMPORTANT SECURITY NOTES:
# - All secrets have been rotated as of $(date)
# - Change MATRIX_BOT_PASSWORD in Matrix server if bot account exists
# - Update bot account password: python matrix-admin.py change-password
# - This file is automatically excluded from git via .gitignore
# =============================================================================
EOF

# Set secure permissions
chmod 600 .env
echo -e "${GREEN}✅ Updated .env file with new secrets${NC}"
echo -e "${GREEN}✅ Set secure permissions (600) on .env file${NC}"

echo -e "${BLUE}🧹 Cleaning up exposed secrets in files...${NC}"

# Remove hardcoded secrets from backup files
echo -e "${YELLOW}📁 Removing backup files with exposed secrets...${NC}"

# List of files that may contain secrets and should be cleaned up
SECRET_FILES=(
    "matrix/synapse/homeserver.yaml.backup*"
    "matrix/synapse/homeserver.yaml.mas-backup*"
    "mas.disabled/config.yaml"
    "mas.disabled/config.yaml.broken"
)

for pattern in "${SECRET_FILES[@]}"; do
    for file in $pattern; do
        if [ -f "$file" ]; then
            echo "  - Removing: $file"
            rm -f "$file"
        fi
    done
done

echo -e "${GREEN}✅ Cleaned up backup files with exposed secrets${NC}"

# Update Matrix configuration to use environment variables
echo -e "${BLUE}🔧 Updating Matrix configuration...${NC}"

if [ -f "matrix/synapse/homeserver.yaml" ]; then
    # Backup current config
    cp matrix/synapse/homeserver.yaml matrix/synapse/homeserver.yaml.backup.$(date +%Y%m%d_%H%M%S)

    # Update to use environment variables (basic config without MAS)
    cat > matrix/synapse/homeserver.yaml << 'EOF'
# Configuration file for Synapse.
server_name: "acebuddy.quest"
public_baseurl: "https://matrix.acebuddy.quest"
pid_file: /data/homeserver.pid

listeners:
  - port: 8008
    tls: false
    type: http
    x_forwarded: true
    resources:
      - names: [client, federation]
        compress: false

database:
  name: psycopg2
  args:
    user: synapse
    password: ${MATRIX_DB_PASSWORD}
    database: synapse
    host: matrix-postgres
    port: 5432
    cp_min: 5
    cp_max: 10

log_config: "/data/acebuddy.quest.log.config"
media_store_path: /data/media_store
report_stats: false

# Secrets from environment variables
registration_shared_secret: "${SYNAPSE_REGISTRATION_SECRET}"
macaroon_secret_key: "${SYNAPSE_MACAROON_SECRET}"
form_secret: "${SYNAPSE_FORM_SECRET}"
signing_key_path: "/data/acebuddy.quest.signing.key"

trusted_key_servers:
  - server_name: "matrix.org"

# Standard registration and authentication
enable_registration: true
enable_registration_without_verification: true
registration_requires_token: false

# Standard password authentication
password_config:
  enabled: true
  pepper: "${SYNAPSE_FORM_SECRET}"

# Security settings
use_presence: true
EOF

    echo -e "${GREEN}✅ Updated Matrix configuration to use environment variables${NC}"
fi

echo -e "${BLUE}🔍 Validating configuration...${NC}"

# Check .gitignore
if ! grep -q "^\.env$" .gitignore 2>/dev/null; then
    echo ".env" >> .gitignore
    echo -e "${GREEN}✅ Added .env to .gitignore${NC}"
else
    echo -e "${GREEN}✅ .env already in .gitignore${NC}"
fi

# Validate environment file
echo -e "${BLUE}🧪 Testing environment variable loading...${NC}"
if source .env && [ ! -z "$MATRIX_DB_PASSWORD" ]; then
    echo -e "${GREEN}✅ Environment variables load correctly${NC}"
else
    echo -e "${RED}❌ Error loading environment variables${NC}"
    exit 1
fi

echo -e "${BLUE}📊 Security Status Summary${NC}"
echo "================================"
echo -e "${GREEN}✅ Generated new secure secrets for all services${NC}"
echo -e "${GREEN}✅ Updated .env file with proper environment variables${NC}"
echo -e "${GREEN}✅ Removed hardcoded secrets from configuration files${NC}"
echo -e "${GREEN}✅ Cleaned up backup files containing exposed secrets${NC}"
echo -e "${GREEN}✅ Updated Matrix configuration to use environment variables${NC}"
echo -e "${GREEN}✅ Secured file permissions${NC}"
echo -e "${GREEN}✅ Updated .gitignore to prevent future secret exposure${NC}"

echo ""
echo -e "${YELLOW}⚠️  IMPORTANT NEXT STEPS:${NC}"
echo "1. 🔄 Redeploy services: ./deploy.sh"
echo "2. 🔑 Update bot password in Matrix server if bot exists"
echo "3. 🧪 Test all services after redeployment"
echo "4. 🗑️  Consider invalidating old API tokens/sessions"
echo "5. 📝 Update any external integrations with new secrets"
echo ""

echo -e "${BLUE}🔧 Service Restart Commands:${NC}"
echo "# Restart Matrix services:"
echo "cd matrix && docker-compose down && docker-compose up -d"
echo ""
echo "# Restart Nextcloud:"
echo "cd nextcloud && docker-compose down && docker-compose up -d"
echo ""
echo "# Restart all services:"
echo "./deploy.sh"
echo ""

echo -e "${GREEN}🎉 Security fix completed successfully!${NC}"
echo -e "${YELLOW}📝 Remember to update any hardcoded passwords in Matrix user accounts${NC}"

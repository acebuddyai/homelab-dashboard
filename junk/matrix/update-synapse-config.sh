#!/bin/bash
set -e
echo "🔧 Updating Synapse configuration with environment variables..."

if [ -f "../.env" ]; then
    echo "📋 Loading environment variables from ../.env"
    export $(grep -v "^#" ../.env | xargs)
else
    echo "❌ Error: ../.env file not found!"
    exit 1
fi

required_vars=("MATRIX_SECRET" "SYNAPSE_CLIENT_SECRET")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: Required environment variable $var is not set!"
        exit 1
    fi
done

# Create backup in /tmp to avoid permission issues
BACKUP_FILE="/tmp/homeserver.yaml.backup.$(date +%Y%m%d_%H%M%S)"
cp synapse/homeserver.yaml "$BACKUP_FILE"
echo "📋 Backup created at: $BACKUP_FILE"

# Update the experimental_features section with environment variables
sed -i.tmp \
    -e "/admin_token:/c\\    admin_token: \"$MATRIX_SECRET\"" \
    -e "/client_secret:/c\\    client_secret: \"$SYNAPSE_CLIENT_SECRET\"" \
    synapse/homeserver.yaml

rm -f synapse/homeserver.yaml.tmp

echo "✅ Synapse configuration updated successfully"
echo "🎯 Updated secrets:"
echo "   - Matrix secret: ${MATRIX_SECRET:0:16}..."
echo "   - Client secret: ${SYNAPSE_CLIENT_SECRET:0:16}..."
echo "✨ Done!"

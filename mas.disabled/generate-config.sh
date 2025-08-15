#!/bin/bash
set -e
echo "🔧 Generating MAS configuration from template with SMTP support..."

if [ -f "../.env" ]; then
    echo "📋 Loading environment variables from ../.env"
    export $(grep -v "^#" ../.env | xargs)
else
    echo "❌ Error: ../.env file not found!"
    exit 1
fi

# Updated required variables to include SMTP
required_vars=("MATRIX_DOMAIN" "MAS_POSTGRES_PASSWORD" "MAS_ENCRYPTION_KEY" "MATRIX_SECRET" "SYNAPSE_CLIENT_SECRET" "SMTP_HOST" "SMTP_PORT" "SMTP_USER" "SMTP_PASSWORD" "EMAIL")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo "❌ Error: Missing required environment variables:"
    printf "   - %s\n" "${missing_vars[@]}"
    exit 1
fi

if command -v envsubst >/dev/null 2>&1; then
    envsubst < config.template.yaml > config.yaml
    echo "✅ MAS config generated successfully using envsubst"
else
    echo "⚠️  envsubst not found, using sed as fallback"
    sed -e "s/\${MATRIX_DOMAIN}/$MATRIX_DOMAIN/g" \
        -e "s/\${MAS_POSTGRES_PASSWORD}/$MAS_POSTGRES_PASSWORD/g" \
        -e "s/\${MAS_ENCRYPTION_KEY}/$MAS_ENCRYPTION_KEY/g" \
        -e "s/\${MATRIX_SECRET}/$MATRIX_SECRET/g" \
        -e "s/\${SYNAPSE_CLIENT_SECRET}/$SYNAPSE_CLIENT_SECRET/g" \
        -e "s/\${SMTP_HOST}/$SMTP_HOST/g" \
        -e "s/\${SMTP_PORT}/$SMTP_PORT/g" \
        -e "s/\${SMTP_USER}/$SMTP_USER/g" \
        -e "s/\${SMTP_PASSWORD}/$SMTP_PASSWORD/g" \
        -e "s/\${EMAIL}/$EMAIL/g" \
        config.template.yaml > config.yaml
    echo "✅ MAS config generated successfully using sed"
fi

chmod 644 config.yaml
echo "🎯 SMTP Configuration loaded:"
echo "   - SMTP Host: $SMTP_HOST:$SMTP_PORT"
echo "   - SMTP User: $SMTP_USER"
echo "   - From Email: $SMTP_USER"
echo "✨ Done! MAS configuration is ready with email support."

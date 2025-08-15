#!/bin/bash

# Matrix Bot Deployment Script
# This script builds and deploys the Matrix bot

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the correct directory
if [[ ! -f "docker-compose.yml" ]]; then
    print_error "docker-compose.yml not found. Please run this script from the matrix directory."
    exit 1
fi

# Check if bot directory exists
if [[ ! -d "bot" ]]; then
    print_error "Bot directory not found. Please ensure the bot code is in the ./bot directory."
    exit 1
fi

print_status "Starting Matrix Bot deployment..."

# Build the bot image
print_status "Building Matrix bot Docker image..."
docker-compose build matrix-bot

if [[ $? -eq 0 ]]; then
    print_success "Bot image built successfully"
else
    print_error "Failed to build bot image"
    exit 1
fi

# Stop existing bot if running
print_status "Stopping existing bot container (if running)..."
docker-compose stop matrix-bot 2>/dev/null || true
docker-compose rm -f matrix-bot 2>/dev/null || true

# Start the bot
print_status "Starting Matrix bot..."
docker-compose up -d matrix-bot

if [[ $? -eq 0 ]]; then
    print_success "Bot started successfully"
else
    print_error "Failed to start bot"
    exit 1
fi

# Wait a moment for the container to start
sleep 3

# Check bot status
print_status "Checking bot status..."
if docker-compose ps matrix-bot | grep -q "Up"; then
    print_success "Bot is running!"

    # Show recent logs
    print_status "Recent bot logs:"
    docker-compose logs --tail=20 matrix-bot

    echo ""
    print_success "Matrix bot deployment completed successfully!"
    print_status "To view live logs, run: docker-compose logs -f matrix-bot"
    print_status "To stop the bot, run: docker-compose stop matrix-bot"
else
    print_error "Bot failed to start properly"
    print_status "Checking logs for errors..."
    docker-compose logs matrix-bot
    exit 1
fi

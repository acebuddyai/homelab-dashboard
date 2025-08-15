#!/bin/bash

# Script to initialize Ollama with required models
set -e

echo "Initializing Ollama..."

# Wait for Ollama to be ready
echo "Waiting for Ollama service to be ready..."
until curl -f http://localhost:11434/api/tags > /dev/null 2>&1; do
    echo "Waiting for Ollama to start..."
    sleep 5
done

echo "Ollama is ready!"

# Pull a smaller model optimized for CPU
echo "Pulling Llama 3.2 3B model (CPU optimized)..."
echo "This model is optimized for systems with limited resources"
curl -X POST http://localhost:11434/api/pull \
    -H "Content-Type: application/json" \
    -d '{"name": "llama3.2:3b"}' \
    --no-progress-meter | while IFS= read -r line; do
    echo "$line" | jq -r '.status // empty' 2>/dev/null || echo "$line"
done

# Also pull the 1B model as a fallback for faster responses
echo "Pulling Llama 3.2 1B model (lightweight)..."
curl -X POST http://localhost:11434/api/pull \
    -H "Content-Type: application/json" \
    -d '{"name": "llama3.2:1b"}' \
    --no-progress-meter | while IFS= read -r line; do
    echo "$line" | jq -r '.status // empty' 2>/dev/null || echo "$line"
done

# Pull a lightweight embedding model
echo "Pulling lightweight embedding model..."
curl -X POST http://localhost:11434/api/pull \
    -H "Content-Type: application/json" \
    -d '{"name": "nomic-embed-text:latest"}' \
    --no-progress-meter | while IFS= read -r line; do
    echo "$line" | jq -r '.status // empty' 2>/dev/null || echo "$line"
done

# Verify models are installed
echo "Verifying installed models..."
curl -s http://localhost:11434/api/tags | jq -r '.models[].name' || echo "Failed to list models"

echo "Ollama initialization complete!"
echo ""
echo "Models installed for CPU-only operation:"
echo "- llama3.2:3b (Main model - balanced performance)"
echo "- llama3.2:1b (Fast model - quick responses)"
echo "- nomic-embed-text (Embeddings for RAG)"
echo ""
echo "Tip: Use llama3.2:1b for faster responses when testing"

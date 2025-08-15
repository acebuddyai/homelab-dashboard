# Homelab AI Stack Makefile
.PHONY: help up down start stop restart logs init-ollama test clean build status ps

# Default target
help:
	@echo "Homelab AI Stack Management"
	@echo "============================"
	@echo ""
	@echo "Available commands:"
	@echo "  make up              - Start all AI services in background"
	@echo "  make down            - Stop and remove all AI services"
	@echo "  make start           - Start stopped services"
	@echo "  make stop            - Stop running services"
	@echo "  make restart         - Restart all services"
	@echo "  make logs            - View logs for all services"
	@echo "  make logs-api        - View API gateway logs"
	@echo "  make logs-ollama     - View Ollama logs"
	@echo "  make init-ollama     - Initialize Ollama with models"
	@echo "  make test            - Test API connectivity"
	@echo "  make test-chat       - Open chat test page"
	@echo "  make clean           - Stop services and remove volumes"
	@echo "  make build           - Build/rebuild all services"
	@echo "  make status          - Check service health status"
	@echo "  make ps              - List running services"
	@echo "  make shell-api       - Open shell in API gateway container"
	@echo "  make shell-ollama    - Open shell in Ollama container"
	@echo ""

# Start all services
up:
	@echo "Starting AI stack services..."
	docker-compose -f docker-compose-ai-stack.yml up -d
	@echo "Waiting for services to be ready..."
	@sleep 5
	@echo "Services started! Access the UI at http://localhost:8080"
	@echo "Run 'make init-ollama' to download AI models"

# Stop and remove services
down:
	@echo "Stopping AI stack services..."
	docker-compose -f docker-compose-ai-stack.yml down

# Start stopped services
start:
	@echo "Starting AI stack services..."
	docker-compose -f docker-compose-ai-stack.yml start

# Stop services without removing
stop:
	@echo "Stopping AI stack services..."
	docker-compose -f docker-compose-ai-stack.yml stop

# Restart all services
restart: stop start
	@echo "Services restarted successfully"

# View logs for all services
logs:
	docker-compose -f docker-compose-ai-stack.yml logs -f

# View API gateway logs
logs-api:
	docker-compose -f docker-compose-ai-stack.yml logs -f api-gateway

# View Ollama logs
logs-ollama:
	docker-compose -f docker-compose-ai-stack.yml logs -f ollama

# View web UI logs
logs-ui:
	docker-compose -f docker-compose-ai-stack.yml logs -f web-ui

# Initialize Ollama with models
init-ollama:
	@echo "Checking if Ollama is running..."
	@docker-compose -f docker-compose-ai-stack.yml ps ollama | grep -q "Up" || (echo "Starting Ollama..." && docker-compose -f docker-compose-ai-stack.yml up -d ollama)
	@echo "Waiting for Ollama to be ready..."
	@sleep 10
	@echo "Initializing Ollama models..."
	@chmod +x scripts/init-ollama.sh
	@./scripts/init-ollama.sh

# Test API connectivity
test:
	@echo "Testing API Gateway health..."
	@curl -f http://localhost:3000/health && echo "\n✅ API Gateway is healthy" || echo "\n❌ API Gateway is not responding"
	@echo ""
	@echo "Testing Ollama..."
	@curl -f http://localhost:11434/api/tags && echo "\n✅ Ollama is healthy" || echo "\n❌ Ollama is not responding"
	@echo ""
	@echo "Testing Redis..."
	@docker exec ai-redis redis-cli ping > /dev/null 2>&1 && echo "✅ Redis is healthy" || echo "❌ Redis is not responding"
	@echo ""
	@echo "Testing Qdrant..."
	@curl -f http://localhost:6333/collections > /dev/null 2>&1 && echo "✅ Qdrant is healthy" || echo "❌ Qdrant is not responding"

# Open test chat page
test-chat:
	@echo "Opening chat test page..."
	@command -v xdg-open > /dev/null 2>&1 && xdg-open http://localhost:8080/test-chat.html || \
	command -v open > /dev/null 2>&1 && open http://localhost:8080/test-chat.html || \
	echo "Please open http://localhost:8080/test-chat.html in your browser"

# Clean everything (including volumes)
clean:
	@echo "⚠️  WARNING: This will remove all data volumes!"
	@echo "Press Ctrl+C to cancel, or wait 5 seconds to continue..."
	@sleep 5
	docker-compose -f docker-compose-ai-stack.yml down -v
	@echo "All services and volumes removed"

# Build/rebuild services
build:
	@echo "Building services..."
	docker-compose -f docker-compose-ai-stack.yml build --no-cache
	@echo "Build complete"

# Check service status
status:
	@echo "Service Status:"
	@echo "==============="
	@docker-compose -f docker-compose-ai-stack.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

# List running services
ps:
	docker-compose -f docker-compose-ai-stack.yml ps

# Shell into API gateway
shell-api:
	docker exec -it api-gateway /bin/sh

# Shell into Ollama
shell-ollama:
	docker exec -it ollama /bin/bash

# Shell into web UI
shell-ui:
	docker exec -it web-ui /bin/sh

# Pull latest images
pull:
	@echo "Pulling latest images..."
	docker-compose -f docker-compose-ai-stack.yml pull

# View resource usage
stats:
	docker stats --no-stream $$(docker-compose -f docker-compose-ai-stack.yml ps -q)

# Test a simple chat message
test-message:
	@echo "Sending test message to AI..."
	@curl -X POST http://localhost:3000/api/ai/chat \
		-H "Content-Type: application/json" \
		-d '{"model": "llama3.2:latest", "messages": [{"role": "user", "content": "Say hello in one sentence"}], "stream": false}' \
		| jq -r '.message.content // .response // "No response received"'

# Download models only
models-download:
	@echo "Downloading Llama 3.2 model..."
	@curl -X POST http://localhost:11434/api/pull \
		-H "Content-Type: application/json" \
		-d '{"name": "llama3.2:latest"}' \
		--no-progress-meter | while IFS= read -r line; do \
			echo "$$line" | jq -r '.status // empty' 2>/dev/null || echo "$$line"; \
		done
	@echo "Model download complete"

# List installed models
models-list:
	@echo "Installed Ollama models:"
	@curl -s http://localhost:11434/api/tags | jq -r '.models[].name' || echo "Failed to list models"

# Quick start (all-in-one)
quickstart: up
	@sleep 10
	@$(MAKE) init-ollama
	@$(MAKE) test
	@echo ""
	@echo "🚀 AI Chat is ready!"
	@echo "Open http://localhost:8080 in your browser"

# Development mode - with live logs
dev: up
	@echo "Starting in development mode with logs..."
	docker-compose -f docker-compose-ai-stack.yml logs -f

# Backup volumes
backup:
	@echo "Creating backup of Docker volumes..."
	@mkdir -p backups
	@docker run --rm -v ollama_data:/data -v $$(pwd)/backups:/backup alpine tar czf /backup/ollama_data_$$(date +%Y%m%d_%H%M%S).tar.gz -C /data .
	@docker run --rm -v qdrant_data:/data -v $$(pwd)/backups:/backup alpine tar czf /backup/qdrant_data_$$(date +%Y%m%d_%H%M%S).tar.gz -C /data .
	@docker run --rm -v redis_data:/data -v $$(pwd)/backups:/backup alpine tar czf /backup/redis_data_$$(date +%Y%m%d_%H%M%S).tar.gz -C /data .
	@echo "Backup complete! Files saved to ./backups/"

# Monitor services with watch
monitor:
	watch -n 2 'docker-compose -f docker-compose-ai-stack.yml ps && echo "" && docker stats --no-stream $$(docker-compose -f docker-compose-ai-stack.yml ps -q)'

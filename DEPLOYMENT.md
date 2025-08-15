# Homelab AI Assistant - Deployment Guide

## 📋 Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Installation](#detailed-installation)
- [Configuration](#configuration)
- [Service Architecture](#service-architecture)
- [Accessing the System](#accessing-the-system)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)
- [Security Considerations](#security-considerations)
- [Backup and Recovery](#backup-and-recovery)

## 🌟 Overview

The Homelab AI Assistant is a self-hosted, privacy-focused AI system that combines:
- **Local LLM inference** via Ollama
- **Workflow automation** with Node-RED
- **Vector database** for RAG/memory (Qdrant)
- **Web search** capabilities (SearXNG)
- **Task management** integration
- **Knowledge management** system
- **Beautiful web UI** for interaction

### Key Features
- ✅ 100% self-hosted and private
- ✅ No external API dependencies
- ✅ Truly open-source stack (Apache 2.0/MIT licenses)
- ✅ Modular and extensible architecture
- ✅ Docker-based deployment
- ✅ Automatic SSL with Caddy

## 📦 Prerequisites

### Hardware Requirements
- **Minimum:**
  - 4 CPU cores
  - 8GB RAM
  - 50GB storage
  
- **Recommended:**
  - 8+ CPU cores
  - 16GB+ RAM
  - 100GB+ SSD storage
  - GPU (optional, for faster LLM inference)

### Software Requirements
- Docker 20.10+
- Docker Compose 2.0+
- Git
- Linux/macOS/WSL2 (for Windows)
- Domain name (optional, for external access)

### Network Requirements
- Ports 80/443 (HTTP/HTTPS)
- Port 3000 (API Gateway)
- Port 1880 (Node-RED)
- Port 6333 (Qdrant)

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/homelab-ai.git
cd homelab-ai

# 2. Copy environment template
cp .env.template .env

# 3. Generate secure passwords
./scripts/generate-passwords.sh

# 4. Edit .env with your settings
nano .env

# 5. Start the stack
docker-compose -f docker-compose-ai-stack.yml up -d

# 6. Initialize the system
./scripts/initialize.sh

# 7. Access the web UI
open http://localhost:3000
```

## 📚 Detailed Installation

### Step 1: System Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker (if not installed)
curl -fsSL https://get.docker.com | sudo sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version
```

### Step 2: Network Configuration

```bash
# Create Docker network
docker network create homelab --subnet=172.20.0.0/16

# Configure firewall (if using ufw)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 3000/tcp
```

### Step 3: Environment Configuration

Edit `.env` file with your specific settings:

```env
# Domain Configuration
DOMAIN=yourdomain.com
ADMIN_EMAIL=admin@yourdomain.com

# Database Passwords (generate secure ones)
POSTGRES_PASSWORD=<generate-secure-password>

# API Keys
JWT_SECRET=<generate-jwt-secret>
NODE_RED_CREDENTIAL_SECRET=<generate-credential-secret>
SEARXNG_SECRET=<generate-secret>

# Model Configuration
DEFAULT_LLM_MODEL=llama3.2:latest
EMBEDDING_MODEL=all-minilm
```

### Step 4: SSL Configuration (Optional)

If using a domain with Caddy for automatic SSL:

```bash
# Update Caddyfile with your domain
nano caddy/Caddyfile

# Replace acebuddy.quest with your domain
sed -i 's/acebuddy.quest/yourdomain.com/g' caddy/Caddyfile
```

### Step 5: Deploy Services

```bash
# Start core services
docker-compose -f docker-compose-ai-stack.yml up -d

# Monitor startup
docker-compose -f docker-compose-ai-stack.yml logs -f

# Verify all services are running
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### Step 6: Initialize Databases

```bash
# Initialize Qdrant collections
curl -X PUT "http://localhost:6333/collections/knowledge_base" \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "size": 384,
      "distance": "Cosine"
    }
  }'

curl -X PUT "http://localhost:6333/collections/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "size": 384,
      "distance": "Cosine"
    }
  }'

curl -X PUT "http://localhost:6333/collections/briefings" \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "size": 384,
      "distance": "Cosine"
    }
  }'
```

### Step 7: Download LLM Models

```bash
# Pull default models
docker exec -it ollama ollama pull llama3.2:latest
docker exec -it ollama ollama pull all-minilm:latest

# Optional: Pull additional models
docker exec -it ollama ollama pull mixtral:latest
docker exec -it ollama ollama pull codellama:latest
```

### Step 8: Deploy Node-RED Flows

```bash
# Node-RED flows are managed through the web interface
# Access Node-RED at http://localhost:1880
# Import flows from the flows/ directory or create new ones

# To backup flows:
docker exec -it node-red cat /data/flows.json > flows_backup.json
```

## ⚙️ Configuration

### Service URLs

After deployment, services are available at:

| Service | Internal URL | External URL | Purpose |
|---------|-------------|--------------|---------|
| Web UI | http://localhost:8080 | https://ai.yourdomain.com | Main interface |
| API Gateway | http://localhost:3000 | https://api.yourdomain.com | API endpoint |
| Node-RED | http://localhost:1880 | https://workflows.yourdomain.com | Flow automation |
| Open WebUI | http://localhost:8080 | https://chat.yourdomain.com | LLM chat interface |
| Qdrant | http://localhost:6333 | Internal only | Vector database |
| Redis | redis://localhost:6379 | Internal only | Cache/sessions |

### Model Configuration

Configure LLM models in `.env`:

```env
# Available models
DEFAULT_LLM_MODEL=llama3.2:latest  # Fast, general purpose
# DEFAULT_LLM_MODEL=mixtral:latest  # Powerful, slower
# DEFAULT_LLM_MODEL=codellama:latest  # Code-focused

# Embedding model (don't change unless necessary)
EMBEDDING_MODEL=all-minilm
```

### Workflow Configuration

Flows are stored in Node-RED and can include:
- Home automation flows
- API integrations
- Data processing pipelines
- `task_automation.py` - Task management
- `knowledge_management.py` - RAG and document management

## 🏗️ Service Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     User Interface                       │
│                  (Web UI / Mobile App)                   │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                     API Gateway                          │
│                  (Node.js / Express)                     │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   Node-RED   │   │    Ollama    │   │    Qdrant    │
│    (Flows)   │   │    (LLMs)    │   │   (Vectors)  │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                    ┌──────────────┐
                    │    Redis     │
                    │   (Cache)    │
                    └──────────────┘
```

### Container Details

| Container | Image | Purpose | Resources |
|-----------|-------|---------|-----------|
| ollama | ollama/ollama:latest | LLM inference | 4GB+ RAM |
| open-webui | ghcr.io/open-webui/open-webui:main | Chat UI | 512MB RAM |
| node-red | nodered/node-red:latest | Flow automation | 512MB RAM |
| qdrant | qdrant/qdrant:latest | Vector database | 1GB RAM |
| redis | redis:7-alpine | Cache/sessions | 256MB RAM |
| searxng | searxng/searxng:latest | Web search | 512MB RAM |
| api-gateway | Custom Node.js | API routing | 512MB RAM |
| caddy | caddy:latest | Reverse proxy/SSL | 128MB RAM |

## 🌐 Accessing the System

### Local Access
```bash
# Web UI
http://localhost:8080

# API Gateway
http://localhost:3000

# Node-RED
http://localhost:1880
```

### External Access (with domain)
```bash
# Web UI
https://ai.yourdomain.com

# API endpoints
https://api.yourdomain.com

# Workflow management
https://workflows.yourdomain.com
```

### Default Credentials

- **Node-RED**: Configure through web interface on first access
- **Open WebUI**: No auth by default (enable in production)

## 🔧 Troubleshooting

### Common Issues

#### 1. Services Won't Start
```bash
# Check logs
docker-compose -f docker-compose-ai-stack.yml logs <service-name>

# Check resource usage
docker stats

# Restart specific service
docker-compose -f docker-compose-ai-stack.yml restart <service-name>
```

#### 2. LLM Not Responding
```bash
# Check Ollama status
docker exec -it ollama ollama list

# Pull model if missing
docker exec -it ollama ollama pull llama3.2:latest

# Check Ollama logs
docker logs ollama
```

#### 3. Database Connection Issues
```bash
# Check Node-RED
curl http://localhost:1880

# Check Qdrant
curl http://localhost:6333/health

# Check Redis
docker exec -it redis redis-cli ping
```

#### 4. Memory Issues
```bash
# Increase Docker memory limit
# Edit /etc/docker/daemon.json
{
  "default-ulimits": {
    "memlock": {
      "soft": -1,
      "hard": -1
    }
  }
}

# Restart Docker
sudo systemctl restart docker
```

### Debug Commands

```bash
# View all logs
docker-compose -f docker-compose-ai-stack.yml logs -f

# Check network connectivity
docker network inspect homelab

# Test API endpoint
curl http://localhost:3000/health

# Check disk usage
docker system df

# Clean up unused resources
docker system prune -a
```

## 🔨 Maintenance

### Daily Tasks
- Monitor system health via Analytics tab
- Review error logs
- Check disk space

### Weekly Tasks
```bash
# Backup databases
./scripts/backup.sh

# Update container images
docker-compose -f docker-compose-ai-stack.yml pull

# Clean old logs
docker exec -it <container> sh -c 'find /var/log -type f -mtime +7 -delete'
```

### Monthly Tasks
```bash
# Full system backup
./scripts/full-backup.sh

# Update LLM models
docker exec -it ollama ollama pull llama3.2:latest

# Backup Node-RED flows
docker exec -it node-red cat /data/flows.json > backups/flows_$(date +%Y%m%d).json
```

## 🔒 Security Considerations

### Network Security
```bash
# Use firewall rules
sudo ufw enable
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS

# Restrict internal services
# Edit docker-compose to bind to localhost only
ports:
  - "127.0.0.1:6333:6333"  # Qdrant
  - "127.0.0.1:6379:6379"  # Redis
```

### Authentication
- Enable authentication in Open WebUI for production
- Use strong passwords for all services
- Implement JWT tokens for API access
- Regular password rotation

### Data Protection
```bash
# Encrypt sensitive data at rest
# Enable PostgreSQL encryption
POSTGRES_INITDB_ARGS="--data-encryption"

# Use encrypted volumes
docker volume create --driver local \
  --opt type=luks \
  --opt device=/dev/vdb \
  encrypted_volume
```

### Updates
```bash
# Regular security updates
apt update && apt upgrade -y

# Update Docker images
docker-compose -f docker-compose-ai-stack.yml pull
docker-compose -f docker-compose-ai-stack.yml up -d
```

## 💾 Backup and Recovery

### Automated Backups

Create `scripts/backup.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/backups/homelab-ai/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Backup Node-RED data
docker cp node-red:/data $BACKUP_DIR/node-red-data
docker exec redis redis-cli SAVE
docker cp redis:/data/dump.rdb $BACKUP_DIR/

# Backup Qdrant
curl -X POST http://localhost:6333/snapshots

# Backup volumes
docker run --rm -v homelab_qdrant_storage:/data -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/qdrant.tar.gz /data

# Backup configuration
cp -r .env caddy/ $BACKUP_DIR/

echo "Backup completed: $BACKUP_DIR"
```

### Recovery Process

```bash
# Stop services
docker-compose -f docker-compose-ai-stack.yml down

# Restore Node-RED data
docker cp backup/node-red-data/. node-red:/data/
docker cp backup/dump.rdb redis:/data/

# Restore volumes
docker run --rm -v homelab_qdrant_storage:/data -v $(pwd)/backup:/backup \
  alpine tar xzf /backup/qdrant.tar.gz -C /

# Restart services
docker-compose -f docker-compose-ai-stack.yml up -d
```

## 📊 Monitoring

### Health Checks

```bash
# Create health check script
cat > scripts/health-check.sh << 'EOF'
#!/bin/bash

echo "Checking service health..."

# Check each service
services=("ollama" "node-red" "qdrant" "redis" "api-gateway")

for service in "${services[@]}"; do
    if docker ps | grep -q $service; then
        echo "✓ $service is running"
    else
        echo "✗ $service is down"
    fi
done

# Check API endpoints
curl -s http://localhost:3000/health > /dev/null && \
    echo "✓ API Gateway responding" || \
    echo "✗ API Gateway not responding"

curl -s http://localhost:6333/health > /dev/null && \
    echo "✓ Qdrant responding" || \
    echo "✗ Qdrant not responding"
EOF

chmod +x scripts/health-check.sh
```

### Prometheus Metrics (Optional)

Add to `docker-compose-ai-stack.yml`:
```yaml
prometheus:
  image: prom/prometheus:latest
  container_name: prometheus
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
    - prometheus_data:/prometheus
  command:
    - '--config.file=/etc/prometheus/prometheus.yml'
    - '--storage.tsdb.path=/prometheus'
  ports:
    - "9090:9090"
  networks:
    homelab:
      ipv4_address: 172.20.0.60

grafana:
  image: grafana/grafana:latest
  container_name: grafana
  volumes:
    - grafana_data:/var/lib/grafana
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin
  ports:
    - "3001:3000"
  networks:
    homelab:
      ipv4_address: 172.20.0.61
```

## 🚨 Disaster Recovery

### Emergency Procedures

1. **Service Failure**
   ```bash
   # Quick restart
   ./scripts/emergency-restart.sh
   
   # Full reset
   docker-compose -f docker-compose-ai-stack.yml down
   docker system prune -a
   docker-compose -f docker-compose-ai-stack.yml up -d
   ```

2. **Data Corruption**
   ```bash
   # Restore from latest backup
   ./scripts/restore-latest.sh
   ```

3. **Complete System Failure**
   ```bash
   # Fresh deployment with data restore
   ./scripts/disaster-recovery.sh
   ```

## 📝 License

This project uses only truly open-source components:
- Ollama (MIT)
- Node-RED (Apache 2.0)
- Qdrant (Apache 2.0)
- Redis (BSD)
- PostgreSQL (PostgreSQL License)
- Node.js (MIT)
- Caddy (Apache 2.0)

## 🤝 Support

For issues and questions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review logs: `docker-compose logs`
3. Open an issue on GitHub
4. Join our Discord community

## 🎉 Next Steps

After successful deployment:
1. Access the Web UI and create your first task
2. Upload documents to the knowledge base
3. Configure daily briefing preferences
4. Explore workflow automation
5. Customize the system for your needs

Congratulations! Your personal AI assistant is ready to use. 🚀
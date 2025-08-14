# 🤖 Multi-Agent Matrix System Setup Guide

**Transform your Matrix homeserver into a collaborative multi-agent AI system**

## 🎯 Overview

This guide helps you deploy a sophisticated multi-agent system where AI bots can communicate, coordinate, and chain their capabilities through Matrix rooms. Built on your existing homelab infrastructure with Matrix, Ollama, and Docker.

## 🏗️ Architecture

```
Matrix Homeserver (Your existing setup)
├── 🎯 Orchestrator Agent (Central coordinator)
├── 🧠 LLM Agent (Ollama integration)
├── 🔍 Search Agent (Web search via SearXNG)
├── 📚 RAG Agent (Vector knowledge base)
└── 👥 Human Users (Element/Cinny clients)

Supporting Services:
├── 🔍 SearXNG (Web search engine)
├── 🗄️ Qdrant (Vector database)
└── 🔴 Redis (Agent coordination)
```

## 🚀 Quick Start

### Prerequisites
- ✅ Matrix Synapse running
- ✅ Ollama with models available
- ✅ Docker and Docker Compose
- ✅ Environment variables configured

### Step 1: Security Setup
```bash
cd ~/homelab

# Generate secure secrets for all agents
./fix-security-issues.sh

# This creates/updates .env with multi-agent credentials
```

### Step 2: Deploy Multi-Agent System
```bash
# Deploy the full multi-agent system
./deploy-multi-agents.sh
```

This script will:
- Create bot user accounts in Matrix
- Deploy supporting services (SearXNG, Qdrant, Redis)
- Build and deploy agent containers
- Perform health checks

### Step 3: Create Matrix Rooms
Use Element, Cinny, or your Matrix client to create:

1. **Coordination Room**: `#bot-coordination:yourdomain.com`
   - Private room for agent-to-agent communication
   - Invite: @orchestrator, @llm, @search, @rag

2. **Agent Workspace**: `#agents:yourdomain.com`
   - Public room for human-agent interaction
   - Invite all bots and users

### Step 4: Update Configuration
```bash
# Get the room ID from your Matrix client
# Update .env file with actual room IDs
nano .env

# Add these lines:
COORDINATION_ROOM_ID=!actual_room_id:yourdomain.com

# Restart agents to pick up new configuration
docker restart matrix-orchestrator matrix-llm-agent
```

## 🎮 Using the Multi-Agent System

### Basic Commands

#### Orchestrator Commands
```
!orchestrator help                    # Show help
!orchestrator status                  # System status
!orchestrator agents                  # List active agents
!orchestrator ask llm "question"      # Direct agent query
```

#### Agent Chaining
```
!orchestrator chain search->llm "Find Python tutorials and summarize them"
!orchestrator chain search->rag->llm "Research quantum computing, store knowledge, then explain"
```

#### Individual Agent Commands
```
!llm "What is machine learning?"      # Direct LLM query
!llm summarize "long text here"       # Text summarization
!llm translate spanish "Hello world"  # Language translation
!llm code "Python sorting function"   # Code generation
```

### Advanced Workflows

#### Research Workflow
```
# Step 1: Search for information
!orchestrator ask search "latest AI developments 2024"

# Step 2: Store and analyze
!orchestrator chain search->rag->llm "AI developments 2024"

# Step 3: Generate report
!orchestrator ask llm "Create a comprehensive report on AI developments in 2024"
```

#### Knowledge Management
```
# Store information in vector database
!orchestrator ask rag "store this document: [paste content]"

# Query knowledge base
!orchestrator ask rag "find documents about machine learning"

# Combine with LLM for answers
!orchestrator chain rag->llm "What do we know about neural networks?"
```

## 🔧 Configuration

### Environment Variables

Key configuration in `.env`:

```bash
# Multi-Agent System
COORDINATION_ROOM_ID=!coordination_room_id:yourdomain.com
ORCHESTRATOR_PASSWORD=secure_generated_password
LLM_AGENT_PASSWORD=secure_generated_password
SEARCH_AGENT_PASSWORD=secure_generated_password
RAG_AGENT_PASSWORD=secure_generated_password

# LLM Settings
DEFAULT_LLM_MODEL=llama3.2:latest
LLM_MAX_TOKENS=2048
LLM_TEMPERATURE=0.7

# Search Settings
SEARCH_RESULTS_LIMIT=5

# RAG Settings
EMBEDDING_MODEL=all-MiniLM-L6-v2
QDRANT_COLLECTION=homelab_knowledge
```

### Agent Capabilities

| Agent | Capabilities | Use Cases |
|-------|--------------|-----------|
| **Orchestrator** | Agent discovery, message routing, workflow coordination | Central command, multi-agent workflows |
| **LLM** | Text generation, summarization, Q&A, code generation | General AI assistance, content creation |
| **Search** | Web search, result filtering, source validation | Research, fact-checking, current information |
| **RAG** | Document storage, semantic search, knowledge retrieval | Knowledge management, document analysis |

## 🛠️ Management Commands

### Check System Status
```bash
# View all agent containers
docker ps --filter network=homelab

# Check specific agent logs
docker logs -f matrix-orchestrator
docker logs -f matrix-llm-agent

# Health check all services
docker exec matrix-orchestrator python -c "print('Orchestrator OK')"
docker exec matrix-llm-agent python -c "print('LLM Agent OK')"
```

### Restart Agents
```bash
# Restart specific agent
docker restart matrix-orchestrator

# Restart all agents
docker restart matrix-orchestrator matrix-llm-agent

# Full system restart
cd matrix && docker-compose restart
```

### Scale the System
```bash
# Add more LLM agents for load balancing
docker run -d --name matrix-llm-agent-2 \
  --network homelab \
  -e MATRIX_BOT_USERNAME=@llm2:yourdomain.com \
  [other env vars] \
  homelab/llm-agent:latest
```

## 🔍 Troubleshooting

### Common Issues

#### Agent Not Responding
```bash
# Check if agent is running
docker ps | grep matrix-

# Check logs for errors
docker logs matrix-orchestrator

# Verify Matrix connection
docker exec matrix-orchestrator python -c "import asyncio; print('Connection test')"
```

#### Room Access Issues
```bash
# Verify room permissions
# Ensure bots are invited to coordination room
# Check COORDINATION_ROOM_ID is correct
```

#### Ollama Connection Issues
```bash
# Test Ollama connectivity
curl http://172.20.0.30:11434/api/tags

# Check LLM agent Ollama config
docker logs matrix-llm-agent | grep -i ollama
```

### Performance Tuning

#### Optimize LLM Performance
```bash
# Adjust token limits for faster responses
LLM_MAX_TOKENS=1024

# Reduce temperature for more focused responses
LLM_TEMPERATURE=0.3

# Use faster models for simple tasks
DEFAULT_LLM_MODEL=llama3.2:3b
```

#### Scale for High Load
```bash
# Deploy multiple LLM agents
# Use Redis for better coordination
# Implement load balancing in orchestrator
```

## 🔐 Security Considerations

### Bot Account Security
- ✅ Generated passwords are 24+ characters
- ✅ Bot accounts have limited privileges
- ✅ Coordination room is private
- ✅ Audit logs available via Matrix

### Network Security
- ✅ All agents run in isolated Docker network
- ✅ No external ports exposed except via Caddy
- ✅ Inter-service communication encrypted
- ✅ Environment variables for secrets

### Monitoring
```bash
# Monitor agent activity
docker logs -f matrix-orchestrator | grep -i "command\|request"

# Check resource usage
docker stats matrix-orchestrator matrix-llm-agent

# Network monitoring
docker network inspect homelab
```

## 🚀 Next Steps

### Phase 1: Basic Operation
- [ ] Deploy and test basic agent communication
- [ ] Create and test simple workflows
- [ ] Familiarize with command syntax

### Phase 2: Advanced Features
- [ ] Deploy Search and RAG agents
- [ ] Create complex multi-step workflows
- [ ] Build knowledge base with RAG

### Phase 3: Customization
- [ ] Add custom agents for specific tasks
- [ ] Integrate with external APIs
- [ ] Create automated workflows

### Phase 4: Scaling
- [ ] Deploy multiple instances of agents
- [ ] Implement load balancing
- [ ] Add monitoring dashboard

## 📚 Additional Resources

### Development
- [Matrix Bot SDK Documentation](https://matrix-nio.readthedocs.io/)
- [Ollama API Reference](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [SearXNG Configuration](https://docs.searxng.org/)
- [Qdrant Vector Database](https://qdrant.tech/documentation/)

### Community
- Matrix Room: `#homelab-agents:yourdomain.com`
- GitHub Issues: Report bugs and feature requests
- Documentation: Contribute improvements

---

**🎉 Welcome to the future of collaborative AI!**

Your multi-agent Matrix system enables sophisticated AI workflows through natural conversation in Matrix rooms. Agents can search the web, process documents, generate content, and coordinate complex tasks - all while maintaining full transparency and user control.
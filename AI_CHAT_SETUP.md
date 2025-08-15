# AI Chat Setup and Testing Guide

## Overview
This guide helps you set up and test the AI chat functionality in the Homelab AI Assistant. The chat uses Ollama for running LLMs locally and provides a web interface for interaction.

## Quick Start

### 1. Start the AI Stack
```bash
cd homelab
docker-compose -f docker-compose-ai-stack.yml up -d
```

### 2. Initialize Ollama
Wait for Ollama to start, then run:
```bash
./scripts/init-ollama.sh
```

This will:
- Pull the Llama 3.2 model
- Pull the embedding model for RAG
- Verify the installation

### 3. Access the Chat Interface

#### Option A: Main Interface
- Open: http://localhost:8080
- Or if deployed: https://ai.acebuddy.quest

#### Option B: Test Interface
- Open: http://localhost:8080/test-chat.html
- This provides a simplified interface for testing

## Services and Ports

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| Web UI | 8080 | http://localhost:8080 | Main chat interface |
| API Gateway | 3000 | http://localhost:3000 | Backend API |
| Ollama | 11434 | http://localhost:11434 | LLM service |
| Redis | 6379 | redis://localhost:6379 | Cache |
| Qdrant | 6333 | http://localhost:6333 | Vector database |
| SearXNG | 8888 | http://localhost:8888 | Search engine |
| Node-RED | 1880 | http://localhost:1880 | Flow automation |

## Testing the Chat

### Basic Test
1. Open the chat interface
2. Type "Hello, how are you?" and press Enter
3. You should see:
   - Your message appear immediately
   - A typing indicator while processing
   - The AI's response

### What to Expect
- **Response Time**: First response may take 10-30 seconds (model loading)
- **Subsequent Messages**: Should respond in 2-5 seconds
- **Visual Feedback**: 
  - Input disabled while processing
  - Typing indicator shows AI is thinking
  - Timestamps on all messages
  - Connection status indicator

## Configuration

### Frontend Settings
Click the settings icon (⚙️) in the top-right to configure:
- **API URL**: Backend server location
- **Model**: Which Ollama model to use
- **User ID**: For personalization (future feature)

### Available Models
- `llama3.2:latest` - Default, balanced performance
- `mixtral:latest` - More advanced, requires more resources
- `codellama:latest` - Specialized for code

## Troubleshooting

### Chat Not Responding

1. **Check Ollama is running:**
```bash
docker logs ollama
curl http://localhost:11434/api/tags
```

2. **Check API Gateway:**
```bash
docker logs api-gateway
curl http://localhost:3000/health
```

3. **Verify model is installed:**
```bash
docker exec ollama ollama list
```

### Connection Issues

If you see "Disconnected" status:

1. **Check all services are running:**
```bash
docker-compose -f docker-compose-ai-stack.yml ps
```

2. **Check network connectivity:**
```bash
# Test API Gateway
curl http://localhost:3000/health

# Test Ollama
curl http://localhost:11434/api/tags
```

3. **Review logs:**
```bash
docker-compose -f docker-compose-ai-stack.yml logs -f api-gateway
docker-compose -f docker-compose-ai-stack.yml logs -f ollama
```

### Slow Responses

1. **First message is always slower** - Ollama loads the model into memory
2. **Check system resources:**
```bash
docker stats
```
3. **Consider using a smaller model** if resources are limited

### Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "AI service unavailable" | Ollama not running | Start Ollama service |
| "Invalid response format" | API compatibility issue | Check API Gateway logs |
| "Connection to AI service lost" | Network/service issue | Restart services |

## Development Testing

### Using the Test Page
The test page (`test-chat.html`) provides:
- Simple, focused interface
- Real-time connection status
- Console logging for debugging
- Easy API URL switching

### Monitoring Requests
Open browser DevTools (F12) to see:
- Request/response details
- Timing information
- Error messages

### Testing Different Scenarios

1. **Normal conversation:**
```
You: What is Docker?
AI: Docker is a containerization platform...
```

2. **Code generation:**
```
You: Write a Python hello world
AI: Here's a simple Python hello world...
```

3. **Error handling:**
```
Stop Ollama, then try to send a message
You should see a clear error message
```

## Performance Tips

1. **Pre-load models** - Run init script after startup
2. **Keep services running** - Avoid frequent restarts
3. **Monitor resources** - Use `docker stats` to check memory/CPU
4. **Adjust model size** - Use smaller models if needed

## Next Steps

Once basic chat is working:

1. **Test memory/knowledge features** - Store and retrieve information
2. **Try workflow automation** - Use Node-RED flows
3. **Enable web search** - Configure SearXNG
4. **Set up embeddings** - For semantic search

## Support

If issues persist:
1. Check the full logs: `docker-compose -f docker-compose-ai-stack.yml logs`
2. Verify all environment variables are set
3. Ensure ports are not already in use
4. Check Docker has sufficient resources allocated

## Notes

- **GPU Support**: If you have an NVIDIA GPU, Ollama will automatically use it
- **Model Downloads**: First-time model pulls can take 5-10 minutes
- **Data Persistence**: All data is stored in Docker volumes
- **Security**: Default setup is for local/development use only
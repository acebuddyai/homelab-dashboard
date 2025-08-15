#!/bin/bash

# Update Matrix multi-agent system with new coordination room ID
# New room: https://matrix.to/#/!jmBxWMDJcwdoMnXGJE:acebuddy.quest

echo "==================================="
echo "Matrix Multi-Agent Room Update"
echo "==================================="
echo

# New coordination room ID
export NEW_COORDINATION_ROOM_ID="!jmBxWMDJcwdoMnXGJE:acebuddy.quest"
echo "✅ New coordination room ID: $NEW_COORDINATION_ROOM_ID"
echo

# Update .env file if it exists
ENV_FILE="../.env"
if [ -f "$ENV_FILE" ]; then
    echo "📝 Updating .env file..."
    # Backup the original .env file
    cp "$ENV_FILE" "${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"

    # Update or add COORDINATION_ROOM_ID
    if grep -q "^COORDINATION_ROOM_ID=" "$ENV_FILE"; then
        sed -i "s|^COORDINATION_ROOM_ID=.*|COORDINATION_ROOM_ID=$NEW_COORDINATION_ROOM_ID|" "$ENV_FILE"
        echo "   - Updated existing COORDINATION_ROOM_ID"
    else
        echo "COORDINATION_ROOM_ID=$NEW_COORDINATION_ROOM_ID" >> "$ENV_FILE"
        echo "   - Added COORDINATION_ROOM_ID"
    fi
else
    echo "⚠️  .env file not found at $ENV_FILE"
    echo "   Creating temporary environment variable export"
fi

echo
echo "🛑 Stopping current agents..."
docker stop matrix-llm-agent 2>/dev/null || echo "   - LLM agent not running"
docker stop matrix-orchestrator 2>/dev/null || echo "   - Orchestrator not running"

echo
echo "🗑️  Removing old containers..."
docker rm matrix-llm-agent 2>/dev/null || echo "   - LLM agent container not found"
docker rm matrix-orchestrator 2>/dev/null || echo "   - Orchestrator container not found"

echo
echo "🚀 Starting agents with new coordination room..."

# Export the variable for docker-compose
export COORDINATION_ROOM_ID="$NEW_COORDINATION_ROOM_ID"

# Start just the LLM agent first (using the standalone version)
echo "   Starting LLM agent..."
docker run -d \
    --name matrix-llm-agent \
    --network homelab \
    --ip 172.20.0.27 \
    -e MATRIX_HOMESERVER_URL="http://matrix-synapse:8008" \
    -e MATRIX_BOT_USERNAME="@subatomic6140:acebuddy.quest" \
    -e MATRIX_BOT_PASSWORD="entourage8-shuffling-poncho" \
    -e COORDINATION_ROOM_ID="$NEW_COORDINATION_ROOM_ID" \
    -e OLLAMA_URL="http://172.20.0.30:11434" \
    -e DEFAULT_LLM_MODEL="llama3.2:latest" \
    -v llm_agent_store:/app/store \
    --restart unless-stopped \
    homelab/llm-agent:latest

# Give the LLM agent time to start and join the room
sleep 5

# Start the orchestrator
echo "   Starting Orchestrator agent..."
docker run -d \
    --name matrix-orchestrator \
    --network homelab \
    --ip 172.20.0.26 \
    -e MATRIX_HOMESERVER_URL="http://matrix-synapse:8008" \
    -e MATRIX_BOT_USERNAME="@unmolded8581:acebuddy.quest" \
    -e MATRIX_BOT_PASSWORD="evacuate-gambling2-penniless" \
    -e COORDINATION_ROOM_ID="$NEW_COORDINATION_ROOM_ID" \
    -e AGENT_DISCOVERY_ENABLED="true" \
    -e WORKFLOW_TIMEOUT="300" \
    -v orchestrator_store:/app/store \
    --restart unless-stopped \
    homelab/orchestrator:latest 2>/dev/null || echo "   - Orchestrator image not found, skipping"

echo
echo "⏳ Waiting for agents to initialize..."
sleep 10

echo
echo "📊 Checking agent status..."
echo

# Check if agents are running
if docker ps | grep -q matrix-llm-agent; then
    echo "✅ LLM agent is running"
    echo "   Checking logs..."
    docker logs --tail 10 matrix-llm-agent 2>&1 | grep -E "(Joined room|Successfully|online|Grandpa)" | head -5
else
    echo "❌ LLM agent is not running"
    echo "   Last logs:"
    docker logs --tail 10 matrix-llm-agent 2>&1
fi

echo

if docker ps | grep -q matrix-orchestrator; then
    echo "✅ Orchestrator is running"
    echo "   Checking logs..."
    docker logs --tail 10 matrix-orchestrator 2>&1 | grep -E "(Joined room|Successfully|online|discovered)" | head -5
else
    echo "⚠️  Orchestrator is not running (image may not be built yet)"
fi

echo
echo "==================================="
echo "Summary"
echo "==================================="
echo "Room ID: $NEW_COORDINATION_ROOM_ID"
echo "Room Link: https://matrix.to/#/$NEW_COORDINATION_ROOM_ID"
echo
echo "Agent Accounts:"
echo "  LLM Agent: @subatomic6140:acebuddy.quest"
echo "  Orchestrator: @unmolded8581:acebuddy.quest"
echo
echo "Next Steps:"
echo "1. Check the Matrix room to see if agents have joined"
echo "2. Test communication by sending a message in the room"
echo "3. Monitor agent discovery with: docker logs -f matrix-llm-agent"
echo
echo "To view agent logs:"
echo "  docker logs matrix-llm-agent"
echo "  docker logs matrix-orchestrator"
echo

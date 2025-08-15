#!/usr/bin/env python3
"""
Orchestrator Agent - Central coordinator for multi-agent system
Manages bot discovery, message routing, and multi-bot workflows
"""

import asyncio
import logging
import json
import os
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import re
import uuid

from nio import MatrixRoom, RoomMessageText

from .base_agent import BaseMatrixAgent, AgentMessage, parse_mention, format_agent_response

logger = logging.getLogger(__name__)

@dataclass
class RegisteredAgent:
    """Information about a registered agent"""
    agent_id: str
    display_name: str
    capabilities: List[str]
    status: str
    last_seen: datetime
    user_id: str = ""

    def is_online(self, timeout_minutes: int = 5) -> bool:
        """Check if agent is considered online based on last_seen"""
        return (datetime.now() - self.last_seen).total_seconds() < (timeout_minutes * 60)

@dataclass
class WorkflowStep:
    """Single step in a multi-agent workflow"""
    agent_id: str
    action: str
    input_data: Any
    output: Optional[Any] = None
    status: str = "pending"  # pending, running, completed, failed
    error: Optional[str] = None

@dataclass
class Workflow:
    """Multi-agent workflow definition"""
    id: str
    name: str
    steps: List[WorkflowStep]
    requester: str
    room_id: str
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"
    current_step: int = 0
    context: Dict[str, Any] = field(default_factory=dict)

class OrchestratorAgent(BaseMatrixAgent):
    """
    Orchestrator Agent - manages the multi-agent system

    Responsibilities:
    - Agent discovery and registration
    - Message routing between agents
    - Multi-agent workflow coordination
    - Load balancing and capability matching
    - System health monitoring
    """

    def __init__(self,
                 homeserver_url: str,
                 username: str,
                 password: str,
                 store_path: Optional[str] = None):

        super().__init__(
            homeserver_url=homeserver_url,
            username=username,
            password=password,
            display_name="🎯 Orchestrator",
            capabilities=[
                "agent_discovery",
                "message_routing",
                "workflow_coordination",
                "system_monitoring",
                "capability_matching"
            ],
            store_path=store_path
        )

        # Agent registry
        self.agents: Dict[str, RegisteredAgent] = {}
        self.capability_map: Dict[str, Set[str]] = {}  # capability -> set of agent_ids

        # Workflow management
        self.active_workflows: Dict[str, Workflow] = {}
        self.workflow_history: List[str] = []

        # Message routing
        self.pending_requests: Dict[str, Dict[str, Any]] = {}
        self.request_timeouts: Dict[str, datetime] = {}

        # System state
        self.system_stats = {
            "messages_routed": 0,
            "workflows_completed": 0,
            "agents_discovered": 0,
            "uptime_start": datetime.now()
        }

        # Register message handlers
        self._register_handlers()

        logger.info("Orchestrator agent initialized")

    def _register_handlers(self):
        """Register handlers for different message types"""
        self.register_message_handler("agent_online", self._handle_agent_online)
        self.register_message_handler("agent_offline", self._handle_agent_offline)
        self.register_message_handler("capability_query", self._handle_capability_query)
        self.register_message_handler("route_request", self._handle_route_request)
        self.register_message_handler("workflow_request", self._handle_workflow_request)
        self.register_message_handler("task_response", self._handle_task_response)
        self.register_message_handler("health_check", self._handle_health_check_msg)

    async def process_user_message(self, room: MatrixRoom, event: RoomMessageText):
        """Process messages from human users"""
        body = event.body.strip()
        sender = event.sender

        # Check if message mentions orchestrator
        command = parse_mention(body, self.agent_id)
        if not command and not body.startswith("!orchestrator"):
            return

        # Extract command
        if body.startswith("!orchestrator"):
            command = body[13:].strip()

        if not command:
            await self._send_help(room.room_id)
            return

        logger.info(f"Processing command from {sender}: {command}")

        try:
            # Parse and execute command
            if command.lower().startswith("help"):
                await self._send_help(room.room_id)
            elif command.lower().startswith("status"):
                await self._send_status(room.room_id)
            elif command.lower().startswith("agents"):
                await self._send_agent_list(room.room_id)
            elif command.lower().startswith("capabilities"):
                await self._send_capabilities(room.room_id)
            elif command.lower().startswith("chain"):
                await self._handle_chain_command(command, room.room_id, sender)
            elif command.lower().startswith("ask"):
                await self._handle_ask_command(command, room.room_id, sender)
            elif command.lower().startswith("workflow"):
                await self._handle_workflow_command(command, room.room_id, sender)
            else:
                await self.send_message(
                    room.room_id,
                    f"❓ Unknown command: `{command}`. Type `!orchestrator help` for available commands."
                )

        except Exception as e:
            logger.error(f"Error processing command '{command}': {e}")
            await self.send_message(
                room.room_id,
                f"❌ Error processing command: {str(e)}"
            )

    async def _send_help(self, room_id: str):
        """Send help message"""
        help_text = """🎯 **Orchestrator Agent Commands**

**Basic Commands:**
• `!orchestrator help` - Show this help
• `!orchestrator status` - System status
• `!orchestrator agents` - List active agents
• `!orchestrator capabilities` - Show agent capabilities

**Agent Interaction:**
• `!orchestrator ask <agent> <message>` - Send message to specific agent
• `!orchestrator chain <agent1>-><agent2> <message>` - Chain multiple agents

**Advanced Workflows:**
• `!orchestrator workflow create <name> <steps>` - Create workflow
• `!orchestrator workflow list` - List active workflows
• `!orchestrator workflow status <id>` - Check workflow status

**Examples:**
• `!orchestrator ask llm "What is quantum computing?"`
• `!orchestrator chain search->llm "Find and summarize Python tutorials"`
• `!orchestrator workflow create research "search->rag->llm"`
"""
        await self.send_message(room_id, help_text)

    async def _send_status(self, room_id: str):
        """Send system status"""
        uptime = datetime.now() - self.system_stats["uptime_start"]
        online_agents = len([a for a in self.agents.values() if a.is_online()])

        status_text = f"""📊 **System Status**

**Orchestrator Health:** ✅ Online
**Uptime:** {str(uptime).split('.')[0]}
**Active Agents:** {online_agents}/{len(self.agents)}
**Messages Routed:** {self.system_stats['messages_routed']}
**Workflows Completed:** {self.system_stats['workflows_completed']}
**Active Workflows:** {len(self.active_workflows)}

**Agent Status:**
{self._format_agent_status()}
"""
        await self.send_message(room_id, status_text)

    async def _send_agent_list(self, room_id: str):
        """Send list of registered agents"""
        if not self.agents:
            await self.send_message(room_id, "📭 No agents currently registered")
            return

        agent_list = "🤖 **Registered Agents:**\n\n"
        for agent in self.agents.values():
            status_emoji = "🟢" if agent.is_online() else "🔴"
            capabilities = ", ".join(agent.capabilities)
            agent_list += f"{status_emoji} **{agent.display_name}** (`{agent.agent_id}`)\n"
            agent_list += f"   ⚡ Capabilities: {capabilities}\n"
            agent_list += f"   🕐 Last seen: {agent.last_seen.strftime('%H:%M:%S')}\n\n"

        await self.send_message(room_id, agent_list)

    async def _send_capabilities(self, room_id: str):
        """Send capability mapping"""
        if not self.capability_map:
            await self.send_message(room_id, "📭 No capabilities registered")
            return

        capabilities_text = "⚡ **Available Capabilities:**\n\n"
        for capability, agent_ids in self.capability_map.items():
            online_agents = [aid for aid in agent_ids
                           if aid in self.agents and self.agents[aid].is_online()]
            if online_agents:
                capabilities_text += f"• **{capability}**: {', '.join(online_agents)}\n"

        await self.send_message(room_id, capabilities_text)

    async def _handle_chain_command(self, command: str, room_id: str, sender: str):
        """Handle chain command: chain agent1->agent2->agent3 message"""
        try:
            # Parse: chain search->llm "find tutorials"
            parts = command[5:].strip()  # Remove "chain"

            if "->" not in parts:
                await self.send_message(room_id, "❌ Invalid chain format. Use: `chain agent1->agent2 message`")
                return

            # Split chain spec and message
            chain_and_msg = parts.split(' ', 1)
            if len(chain_and_msg) != 2:
                await self.send_message(room_id, "❌ Missing message. Use: `chain agent1->agent2 \"your message\"`")
                return

            chain_spec, message = chain_and_msg
            agents = [a.strip() for a in chain_spec.split('->')]

            # Validate agents exist and are online
            missing_agents = []
            for agent_id in agents:
                if agent_id not in self.agents or not self.agents[agent_id].is_online():
                    missing_agents.append(agent_id)

            if missing_agents:
                await self.send_message(
                    room_id,
                    f"❌ Agents not available: {', '.join(missing_agents)}"
                )
                return

            # Create and execute workflow
            workflow_id = await self._create_chain_workflow(agents, message, sender, room_id)
            await self.send_message(
                room_id,
                f"🔄 Started chain workflow `{workflow_id}` with {len(agents)} agents"
            )

        except Exception as e:
            logger.error(f"Error handling chain command: {e}")
            await self.send_message(room_id, f"❌ Error creating chain: {str(e)}")

    async def _handle_ask_command(self, command: str, room_id: str, sender: str):
        """Handle direct ask command: ask agent message"""
        try:
            # Parse: ask llm "what is AI?"
            parts = command[3:].strip().split(' ', 1)  # Remove "ask"

            if len(parts) != 2:
                await self.send_message(room_id, "❌ Usage: `ask <agent> \"your message\"`")
                return

            agent_id, message = parts
            message = message.strip('"\'')  # Remove quotes

            # Check if agent exists and is online
            if agent_id not in self.agents:
                await self.send_message(room_id, f"❌ Agent `{agent_id}` not found")
                return

            if not self.agents[agent_id].is_online():
                await self.send_message(room_id, f"❌ Agent `{agent_id}` is offline")
                return

            # Route message to agent
            request_id = await self._route_message_to_agent(
                agent_id, "user_request", message, sender, room_id
            )

            if request_id:
                await self.send_message(
                    room_id,
                    f"📤 Sent message to {agent_id}. Request ID: `{request_id}`"
                )
            else:
                await self.send_message(room_id, "❌ Failed to send message")

        except Exception as e:
            logger.error(f"Error handling ask command: {e}")
            await self.send_message(room_id, f"❌ Error: {str(e)}")

    async def _handle_workflow_command(self, command: str, room_id: str, sender: str):
        """Handle workflow management commands"""
        # TODO: Implement workflow creation, listing, and management
        await self.send_message(room_id, "🚧 Workflow commands coming soon!")

    # Agent Management
    async def _handle_agent_online(self, agent_msg: AgentMessage, room: MatrixRoom):
        """Handle agent coming online"""
        try:
            content = agent_msg.content
            agent_id = content["agent_id"]

            # Register or update agent
            self.agents[agent_id] = RegisteredAgent(
                agent_id=agent_id,
                display_name=content["display_name"],
                capabilities=content["capabilities"],
                status=content["status"],
                last_seen=datetime.now(),
                user_id=agent_msg.sender
            )

            # Update capability map
            for capability in content["capabilities"]:
                if capability not in self.capability_map:
                    self.capability_map[capability] = set()
                self.capability_map[capability].add(agent_id)

            self.system_stats["agents_discovered"] += 1
            logger.info(f"Agent {agent_id} registered with capabilities: {content['capabilities']}")

        except Exception as e:
            logger.error(f"Error handling agent online: {e}")

    async def _handle_agent_offline(self, agent_msg: AgentMessage, room: MatrixRoom):
        """Handle agent going offline"""
        try:
            agent_id = agent_msg.content["agent_id"]

            if agent_id in self.agents:
                self.agents[agent_id].status = "offline"
                logger.info(f"Agent {agent_id} went offline")

        except Exception as e:
            logger.error(f"Error handling agent offline: {e}")

    # Message Routing
    async def _route_message_to_agent(self,
                                     agent_id: str,
                                     message_type: str,
                                     content: Any,
                                     requester: str,
                                     room_id: str) -> Optional[str]:
        """Route a message to a specific agent"""
        try:
            request_id = str(uuid.uuid4())

            # Store pending request
            self.pending_requests[request_id] = {
                "agent_id": agent_id,
                "requester": requester,
                "room_id": room_id,
                "timestamp": datetime.now()
            }

            # Send to agent
            msg_id = await self.send_to_agent(
                target_agent=agent_id,
                message_type=message_type,
                content=content,
                context={
                    "request_id": request_id,
                    "requester": requester,
                    "room_id": room_id
                }
            )

            if msg_id:
                self.system_stats["messages_routed"] += 1
                return request_id
            return None

        except Exception as e:
            logger.error(f"Error routing message to {agent_id}: {e}")
            return None

    async def _create_chain_workflow(self,
                                   agents: List[str],
                                   message: str,
                                   requester: str,
                                   room_id: str) -> str:
        """Create a chain workflow"""
        workflow_id = str(uuid.uuid4())[:8]

        # Create workflow steps
        steps = []
        for i, agent_id in enumerate(agents):
            step = WorkflowStep(
                agent_id=agent_id,
                action="process",
                input_data=message if i == 0 else None  # First step gets the message
            )
            steps.append(step)

        # Create workflow
        workflow = Workflow(
            id=workflow_id,
            name=f"chain_{workflow_id}",
            steps=steps,
            requester=requester,
            room_id=room_id
        )

        self.active_workflows[workflow_id] = workflow

        # Start execution
        asyncio.create_task(self._execute_workflow(workflow_id))

        return workflow_id

    async def _execute_workflow(self, workflow_id: str):
        """Execute a workflow"""
        try:
            workflow = self.active_workflows[workflow_id]
            workflow.status = "running"

            for i, step in enumerate(workflow.steps):
                step.status = "running"
                workflow.current_step = i

                # Determine input data
                if i == 0:
                    input_data = step.input_data
                else:
                    # Use output from previous step
                    prev_step = workflow.steps[i-1]
                    input_data = prev_step.output

                # Execute step
                request_id = await self._route_message_to_agent(
                    step.agent_id,
                    "workflow_step",
                    input_data,
                    workflow.requester,
                    workflow.room_id
                )

                if not request_id:
                    step.status = "failed"
                    step.error = "Failed to route message"
                    workflow.status = "failed"
                    break

                # Wait for response (TODO: implement proper waiting mechanism)
                await asyncio.sleep(2)  # Placeholder
                step.status = "completed"
                step.output = f"Output from {step.agent_id}"  # Placeholder

            if workflow.status != "failed":
                workflow.status = "completed"
                self.system_stats["workflows_completed"] += 1

            # Send completion message
            await self.send_message(
                workflow.room_id,
                f"✅ Workflow `{workflow_id}` completed with status: {workflow.status}"
            )

        except Exception as e:
            logger.error(f"Error executing workflow {workflow_id}: {e}")
            workflow.status = "failed"

    # Helper methods
    def _format_agent_status(self) -> str:
        """Format agent status for display"""
        if not self.agents:
            return "No agents registered"

        status_lines = []
        for agent in self.agents.values():
            emoji = "🟢" if agent.is_online() else "🔴"
            status_lines.append(f"{emoji} {agent.agent_id}")

        return "\n".join(status_lines)

    async def _handle_capability_query(self, agent_msg: AgentMessage, room: MatrixRoom):
        """Handle capability query from agents"""
        # TODO: Implement capability queries
        pass

    async def _handle_route_request(self, agent_msg: AgentMessage, room: MatrixRoom):
        """Handle message routing requests from agents"""
        # TODO: Implement agent-to-agent routing
        pass

    async def _handle_workflow_request(self, agent_msg: AgentMessage, room: MatrixRoom):
        """Handle workflow requests from agents"""
        # TODO: Implement workflow requests
        pass

    async def _handle_task_response(self, agent_msg: AgentMessage, room: MatrixRoom):
        """Handle task responses from agents"""
        # TODO: Implement response handling for pending requests
        pass

    async def _handle_health_check_msg(self, agent_msg: AgentMessage, room: MatrixRoom):
        """Handle health check messages"""
        await self.reply_to_agent(
            agent_msg,
            await self.handle_health_check(),
            room.room_id
        )

    async def get_status(self) -> Dict[str, Any]:
        """Return orchestrator status"""
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "registered_agents": len(self.agents),
            "active_workflows": len(self.active_workflows),
            "system_stats": self.system_stats,
            "capabilities": self.capabilities
        }

    async def handle_health_check(self) -> Dict[str, Any]:
        """Handle health check requests"""
        online_agents = len([a for a in self.agents.values() if a.is_online()])

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "orchestrator_id": self.agent_id,
            "registered_agents": len(self.agents),
            "online_agents": online_agents,
            "active_workflows": len(self.active_workflows),
            "uptime": str(datetime.now() - self.system_stats["uptime_start"])
        }

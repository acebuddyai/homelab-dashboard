#!/usr/bin/env python3
"""
Base Matrix Agent class for multi-agent system
Provides foundation for all specialized bot agents
"""

import asyncio
import logging
import json
import os
from typing import Dict, List, Optional, Any, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
import uuid

from nio import (
    AsyncClient,
    MatrixRoom,
    RoomMessageText,
    LoginResponse,
    JoinResponse,
    Event,
    Response
)

logger = logging.getLogger(__name__)

@dataclass
class AgentMessage:
    """Structured message format for inter-agent communication"""
    id: str
    sender: str
    target: str
    message_type: str
    content: Any
    context: Dict[str, Any]
    timestamp: datetime
    reply_to: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "sender": self.sender,
            "target": self.target,
            "message_type": self.message_type,
            "content": self.content,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "reply_to": self.reply_to
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMessage":
        return cls(
            id=data["id"],
            sender=data["sender"],
            target=data["target"],
            message_type=data["message_type"],
            content=data["content"],
            context=data["context"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            reply_to=data.get("reply_to")
        )

class BaseMatrixAgent(ABC):
    """Base class for all Matrix-based agents in the multi-agent system"""

    def __init__(self,
                 homeserver_url: str,
                 username: str,
                 password: str,
                 display_name: str,
                 capabilities: List[str],
                 store_path: Optional[str] = None):

        self.homeserver_url = homeserver_url
        self.username = username
        self.password = password
        self.display_name = display_name
        self.capabilities = capabilities
        self.store_path = store_path or f"/tmp/{username}_store"

        # Agent state
        self.agent_id = username.split(':')[0].lstrip('@')
        self.status = "offline"
        self.joined_rooms = set()
        self.coordination_room = None
        self.message_handlers = {}
        self.pending_responses = {}

        # Matrix client
        self.client = AsyncClient(
            homeserver=homeserver_url,
            user=username,
            store_path=store_path
        )

        # Register event callbacks
        self.client.add_event_callback(self._on_message, RoomMessageText)

        logger.info(f"Initialized agent {self.agent_id} with capabilities: {capabilities}")

    async def start(self) -> bool:
        """Start the agent - login and join required rooms"""
        try:
            # Login
            response = await self.client.login(self.password)
            if not isinstance(response, LoginResponse):
                logger.error(f"Failed to login agent {self.agent_id}: {response}")
                return False

            logger.info(f"Agent {self.agent_id} logged in successfully")
            self.status = "online"

            # Join coordination room if specified
            coordination_room_id = os.getenv("COORDINATION_ROOM_ID")
            if coordination_room_id:
                await self.join_room(coordination_room_id)
                self.coordination_room = coordination_room_id

            # Register agent in coordination room
            if self.coordination_room:
                await self._announce_presence()

            # Start sync
            await self._start_sync()
            return True

        except Exception as e:
            logger.error(f"Failed to start agent {self.agent_id}: {e}")
            return False

    async def stop(self):
        """Stop the agent gracefully"""
        try:
            if self.coordination_room:
                await self._announce_departure()

            await self.client.close()
            self.status = "offline"
            logger.info(f"Agent {self.agent_id} stopped")

        except Exception as e:
            logger.error(f"Error stopping agent {self.agent_id}: {e}")

    async def join_room(self, room_id: str) -> bool:
        """Join a Matrix room"""
        try:
            response = await self.client.join(room_id)
            if isinstance(response, JoinResponse):
                self.joined_rooms.add(room_id)
                logger.info(f"Agent {self.agent_id} joined room {room_id}")
                return True
            else:
                logger.error(f"Failed to join room {room_id}: {response}")
                return False
        except Exception as e:
            logger.error(f"Error joining room {room_id}: {e}")
            return False

    async def send_message(self, room_id: str, content: str, msg_type: str = "m.text") -> bool:
        """Send a message to a Matrix room"""
        try:
            message_content = {
                "msgtype": msg_type,
                "body": content
            }

            response = await self.client.room_send(
                room_id=room_id,
                message_type="m.room.message",
                content=message_content,
                ignore_unverified_devices=True
            )

            return hasattr(response, 'event_id')

        except Exception as e:
            logger.error(f"Error sending message to {room_id}: {e}")
            return False

    async def send_to_agent(self,
                           target_agent: str,
                           message_type: str,
                           content: Any,
                           context: Optional[Dict[str, Any]] = None,
                           room_id: Optional[str] = None) -> Optional[str]:
        """Send a structured message to another agent"""

        # Create agent message
        agent_msg = AgentMessage(
            id=str(uuid.uuid4()),
            sender=self.agent_id,
            target=target_agent,
            message_type=message_type,
            content=content,
            context=context or {},
            timestamp=datetime.now()
        )

        # Use coordination room if no specific room provided
        target_room = room_id or self.coordination_room
        if not target_room:
            logger.error("No room specified and no coordination room available")
            return None

        # Format message for Matrix
        formatted_content = f"@{target_agent}: {json.dumps(agent_msg.to_dict())}"

        success = await self.send_message(target_room, formatted_content)
        if success:
            logger.debug(f"Sent message {agent_msg.id} to agent {target_agent}")
            return agent_msg.id
        return None

    async def reply_to_agent(self,
                            original_msg: AgentMessage,
                            response_content: Any,
                            room_id: Optional[str] = None) -> Optional[str]:
        """Reply to an agent message"""
        return await self.send_to_agent(
            target_agent=original_msg.sender,
            message_type=f"{original_msg.message_type}_response",
            content=response_content,
            context={"reply_to": original_msg.id},
            room_id=room_id
        )

    async def broadcast_to_agents(self,
                                 message_type: str,
                                 content: Any,
                                 context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Broadcast a message to all agents in coordination room"""
        if not self.coordination_room:
            logger.error("No coordination room available for broadcast")
            return []

        agent_msg = AgentMessage(
            id=str(uuid.uuid4()),
            sender=self.agent_id,
            target="*",  # Broadcast indicator
            message_type=message_type,
            content=content,
            context=context or {},
            timestamp=datetime.now()
        )

        formatted_content = f"@room: {json.dumps(agent_msg.to_dict())}"
        success = await self.send_message(self.coordination_room, formatted_content)

        return [agent_msg.id] if success else []

    def register_message_handler(self, message_type: str, handler: Callable):
        """Register a handler for specific message types"""
        self.message_handlers[message_type] = handler
        logger.debug(f"Registered handler for message type: {message_type}")

    async def _on_message(self, room: MatrixRoom, event: RoomMessageText):
        """Handle incoming Matrix messages"""
        # Ignore own messages
        if event.sender == self.client.user_id:
            return

        try:
            # Check if this is an agent message
            if self._is_agent_message(event.body):
                await self._handle_agent_message(room, event)
            else:
                # Handle regular user messages
                await self._handle_user_message(room, event)

        except Exception as e:
            logger.error(f"Error handling message in {room.room_id}: {e}")

    def _is_agent_message(self, body: str) -> bool:
        """Check if message is a structured agent message"""
        # Agent messages start with @agent_name: or @room: followed by JSON
        if not (body.startswith('@') and ':' in body):
            return False

        try:
            # Extract JSON part
            json_start = body.find(': {')
            if json_start == -1:
                return False

            json_part = body[json_start + 2:]
            json.loads(json_part)
            return True

        except (json.JSONDecodeError, ValueError):
            return False

    async def _handle_agent_message(self, room: MatrixRoom, event: RoomMessageText):
        """Handle structured agent-to-agent messages"""
        try:
            # Extract target and JSON
            body = event.body
            target_end = body.find(': {')
            target = body[1:target_end]  # Remove @ prefix
            json_part = body[target_end + 2:]

            # Check if message is for this agent or broadcast
            if target != self.agent_id and target != "room":
                return

            # Parse agent message
            msg_data = json.loads(json_part)
            agent_msg = AgentMessage.from_dict(msg_data)

            logger.debug(f"Received agent message {agent_msg.id} from {agent_msg.sender}")

            # Handle based on message type
            if agent_msg.message_type in self.message_handlers:
                await self.message_handlers[agent_msg.message_type](agent_msg, room)
            else:
                await self._handle_unknown_agent_message(agent_msg, room)

        except Exception as e:
            logger.error(f"Error handling agent message: {e}")

    async def _handle_user_message(self, room: MatrixRoom, event: RoomMessageText):
        """Handle messages from human users - implement in subclasses"""
        await self.process_user_message(room, event)

    async def _handle_unknown_agent_message(self, agent_msg: AgentMessage, room: MatrixRoom):
        """Handle unknown agent message types"""
        logger.warning(f"Unknown message type {agent_msg.message_type} from {agent_msg.sender}")

        await self.reply_to_agent(
            agent_msg,
            {"error": f"Unknown message type: {agent_msg.message_type}"},
            room.room_id
        )

    async def _announce_presence(self):
        """Announce agent presence in coordination room"""
        await self.broadcast_to_agents(
            "agent_online",
            {
                "agent_id": self.agent_id,
                "display_name": self.display_name,
                "capabilities": self.capabilities,
                "status": self.status
            }
        )

    async def _announce_departure(self):
        """Announce agent going offline"""
        await self.broadcast_to_agents(
            "agent_offline",
            {"agent_id": self.agent_id}
        )

    async def _start_sync(self):
        """Start Matrix sync loop"""
        try:
            await self.client.sync_forever(timeout=30000, full_state=True)
        except Exception as e:
            logger.error(f"Sync error for agent {self.agent_id}: {e}")
            raise

    # Abstract methods to be implemented by subclasses
    @abstractmethod
    async def process_user_message(self, room: MatrixRoom, event: RoomMessageText):
        """Process messages from human users"""
        pass

    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """Return agent status information"""
        pass

    @abstractmethod
    async def handle_health_check(self) -> Dict[str, Any]:
        """Handle health check requests"""
        pass

# Utility functions
def parse_mention(body: str, agent_id: str) -> Optional[str]:
    """Extract command from message that mentions this agent"""
    mention = f"@{agent_id}"
    if mention in body:
        # Find the mention and extract text after it
        start = body.find(mention) + len(mention)
        command = body[start:].strip()
        return command.lstrip(':').strip()
    return None

def format_agent_response(content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    """Format agent response with optional metadata"""
    if metadata:
        footer = "\n".join([f"_{k}: {v}_" for k, v in metadata.items()])
        return f"{content}\n\n{footer}"
    return content

#!/usr/bin/env python3
"""
Simple LLM Agent for Matrix
Responds when called by orchestrator, provides basic chat responses
"""

import asyncio
import logging
import os
import random
import json
from typing import Dict, Any, Optional

from nio import AsyncClient, MatrixRoom, RoomMessageText, LoginResponse

logger = logging.getLogger(__name__)

class SimpleLLMAgent:
    """Simple LLM agent that responds when called by orchestrator"""

    def __init__(self, homeserver_url: str, username: str, password: str, store_path: str = "/app/store"):
        self.homeserver_url = homeserver_url
        self.username = username
        self.password = password
        self.store_path = store_path

        # Bot configuration
        self.display_name = "LLM Buddy"
        self.orchestrator_username = "@unmolded8581:acebuddy.quest"

        # Target rooms
        self.target_rooms = [
            "!KyOMcaXNWvZvGgPqmw:acebuddy.quest",  # LLM room
            "!aJySTGOBquzIVrrcTB:acebuddy.quest"   # Weather/API room
        ]

        # Matrix client
        self.client = AsyncClient(
            homeserver=homeserver_url,
            user=username,
            store_path=store_path
        )

        # Register event callback
        self.client.add_event_callback(self._on_message, RoomMessageText)

        # Friendly responses to orchestrator
        self.buddy_responses = [
            "Hey buddy! 👋",
            "On it, pal! 🚀",
            "You got it! 💪",
            "Thanks for the call! ✨",
            "Ready to help! 🎯",
            "Let's do this! 🔥",
            "Absolutely, friend! 🤝",
            "Count on me! ⭐"
        ]

        # Simple response templates
        self.responses = [
            "Hi there! I'm here to help. What can I do for you?",
            "Hello! I'm ready to assist with your questions.",
            "Hey! What would you like to know or discuss?",
            "Hi! I'm here and ready to help with whatever you need.",
            "Hello! Feel free to ask me anything.",
            "Hey there! What can I help you with today?",
            "Hi! I'm your friendly AI assistant. How can I help?"
        ]

        logger.info(f"Initialized simple LLM agent: {username}")

    async def start(self) -> bool:
        """Start the LLM agent"""
        try:
            # Login
            response = await self.client.login(self.password)
            if not isinstance(response, LoginResponse):
                logger.error(f"Failed to login: {response}")
                return False

            logger.info("✅ LLM agent logged in successfully")

            # Join target rooms
            for room_id in self.target_rooms:
                await self._join_room(room_id)

            # Start sync loop
            await self.client.sync_forever(timeout=30000)
            return True

        except Exception as e:
            logger.error(f"Failed to start LLM agent: {e}")
            return False

    async def _join_room(self, room_id: str):
        """Join a specific room"""
        try:
            response = await self.client.join(room_id)
            logger.info(f"Joined room: {room_id}")
        except Exception as e:
            logger.error(f"Failed to join room {room_id}: {e}")

    async def _on_message(self, room: MatrixRoom, event: RoomMessageText):
        """Handle incoming messages"""
        # Ignore own messages
        if event.sender == self.client.user_id:
            return

        body = event.body.strip()

        # Check if orchestrator is calling us
        if event.sender == self.orchestrator_username and "buddy" in body.lower():
            await self._respond_to_orchestrator_call(room, event)
            return

        # Check if we're mentioned directly
        my_username = self.username.split(':')[0].lstrip('@')
        if my_username in body or self.username in body:
            await self._handle_direct_mention(room, event)
            return

        # Respond to orchestrator's friendly messages
        if event.sender == self.orchestrator_username:
            await self._send_buddy_response(room.room_id)

    async def _respond_to_orchestrator_call(self, room: MatrixRoom, event: RoomMessageText):
        """Respond when orchestrator calls us to help"""
        try:
            # Brief acknowledgment to orchestrator
            buddy_response = random.choice(self.buddy_responses)
            await self._send_message(room.room_id, buddy_response)

            # Small delay for natural conversation flow
            await asyncio.sleep(1.0)

            # Provide helpful response
            main_response = random.choice(self.responses)
            await self._send_message(room.room_id, main_response)

            logger.info(f"Responded to orchestrator call in {room.room_id}")

        except Exception as e:
            logger.error(f"Error responding to orchestrator call: {e}")

    async def _handle_direct_mention(self, room: MatrixRoom, event: RoomMessageText):
        """Handle direct mentions of this bot"""
        try:
            # Get the message without the mention
            body = event.body.strip()
            my_username = self.username.split(':')[0].lstrip('@')

            # Clean up the message
            clean_message = body.replace(f"@{my_username}", "").replace(self.username, "").strip()

            if not clean_message or clean_message.lower() in ["hi", "hello", "hey"]:
                response = random.choice(self.responses)
            else:
                # Simple echo with helpful tone
                response = f"I hear you asking about: '{clean_message}'. I'm a simple bot for now, but I'm here to help! What specifically would you like to know?"

            await self._send_message(room.room_id, response)

            logger.info(f"Handled direct mention in {room.room_id}")

        except Exception as e:
            logger.error(f"Error handling direct mention: {e}")

    async def _send_buddy_response(self, room_id: str):
        """Send a brief friendly response"""
        try:
            response = random.choice(self.buddy_responses)
            await self._send_message(room_id, response)
        except Exception as e:
            logger.error(f"Error sending buddy response: {e}")

    async def _send_message(self, room_id: str, content: str) -> bool:
        """Send a message to a room"""
        try:
            message_content = {
                "msgtype": "m.text",
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

    async def stop(self):
        """Stop the LLM agent"""
        try:
            await self.client.close()
            logger.info("🛑 LLM agent stopped")
        except Exception as e:
            logger.error(f"Error stopping LLM agent: {e}")


async def main():
    """Main function to run the LLM agent"""
    # Get environment variables
    homeserver_url = os.getenv("MATRIX_HOMESERVER_URL", "https://acebuddy.quest")
    username = os.getenv("MATRIX_BOT_USERNAME", "@subatomic6140:acebuddy.quest")
    password = os.getenv("MATRIX_BOT_PASSWORD")
    store_path = os.getenv("BOT_STORE_DIR", "/app/store")

    if not password:
        logger.error("MATRIX_BOT_PASSWORD environment variable is required")
        return

    # Create and start LLM agent
    llm_agent = SimpleLLMAgent(
        homeserver_url=homeserver_url,
        username=username,
        password=password,
        store_path=store_path
    )

    try:
        await llm_agent.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        await llm_agent.stop()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    asyncio.run(main())

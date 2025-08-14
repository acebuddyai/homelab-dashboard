#!/usr/bin/env python3
"""
Simple Orchestrator Agent for Matrix
Responds to "das" or "Das" and coordinates with LLM bot
"""

import asyncio
import logging
import os
import random
from typing import Dict, Any

from nio import AsyncClient, MatrixRoom, RoomMessageText, LoginResponse

logger = logging.getLogger(__name__)

class SimpleOrchestratorAgent:
    """Simple orchestrator that responds to 'das' and calls LLM bot"""

    def __init__(self, homeserver_url: str, username: str, password: str, store_path: str = "/app/store"):
        self.homeserver_url = homeserver_url
        self.username = username
        self.password = password
        self.store_path = store_path

        # Bot configuration
        self.display_name = "Das Bot (Orchestrator)"
        self.llm_bot_username = "@subatomic6140:acebuddy.quest"

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

        # Friend responses for bot-to-bot chat
        self.friendly_responses = [
            "Got it buddy! 🤝",
            "On it, pal! 👍",
            "Thanks friend! 💪",
            "You rock! ⭐",
            "Great work buddy! 🎯",
            "Perfect, thanks! ✨",
            "Awesome job! 🔥",
            "Thanks pal! 🙌"
        ]

        logger.info(f"Initialized simple orchestrator: {username}")

    async def start(self) -> bool:
        """Start the orchestrator agent"""
        try:
            # Login
            response = await self.client.login(self.password)
            if not isinstance(response, LoginResponse):
                logger.error(f"Failed to login: {response}")
                return False

            logger.info("✅ Orchestrator logged in successfully")

            # Join target rooms
            for room_id in self.target_rooms:
                await self._join_room(room_id)

            # Start sync loop
            await self.client.sync_forever(timeout=30000)
            return True

        except Exception as e:
            logger.error(f"Failed to start orchestrator: {e}")
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

        # Ignore messages from the LLM bot (to avoid loops)
        if event.sender == self.llm_bot_username:
            # But respond friendly if it mentions us
            if self.username.split(':')[0].lstrip('@') in event.body.lower():
                await self._send_friendly_response(room.room_id)
            return

        body = event.body.strip()

        # Check for "das" or "Das" trigger
        if body.lower() == "das" or body == "Das":
            await self._handle_das_request(room, event)

    async def _handle_das_request(self, room: MatrixRoom, event: RoomMessageText):
        """Handle 'das' requests - acknowledge and call LLM bot"""
        try:
            # Quick acknowledgment
            ack_message = "📥 Got it! Let me get my buddy to help you..."
            await self._send_message(room.room_id, ack_message)

            # Small delay for natural feel
            await asyncio.sleep(0.5)

            # Call the LLM bot
            call_message = f"{self.llm_bot_username} buddy, can you help here? 🤖"
            await self._send_message(room.room_id, call_message)

            logger.info(f"Handled 'das' request in {room.room_id} from {event.sender}")

        except Exception as e:
            logger.error(f"Error handling das request: {e}")

    async def _send_friendly_response(self, room_id: str):
        """Send a brief friendly response to LLM bot"""
        try:
            response = random.choice(self.friendly_responses)
            await self._send_message(room_id, response)
        except Exception as e:
            logger.error(f"Error sending friendly response: {e}")

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
        """Stop the orchestrator agent"""
        try:
            await self.client.close()
            logger.info("🛑 Orchestrator stopped")
        except Exception as e:
            logger.error(f"Error stopping orchestrator: {e}")


async def main():
    """Main function to run the orchestrator"""
    # Get environment variables
    homeserver_url = os.getenv("MATRIX_HOMESERVER_URL", "https://acebuddy.quest")
    username = os.getenv("MATRIX_BOT_USERNAME", "@unmolded8581:acebuddy.quest")
    password = os.getenv("MATRIX_BOT_PASSWORD")
    store_path = os.getenv("BOT_STORE_DIR", "/app/store")

    if not password:
        logger.error("MATRIX_BOT_PASSWORD environment variable is required")
        return

    # Create and start orchestrator
    orchestrator = SimpleOrchestratorAgent(
        homeserver_url=homeserver_url,
        username=username,
        password=password,
        store_path=store_path
    )

    try:
        await orchestrator.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        await orchestrator.stop()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    asyncio.run(main())

#!/usr/bin/env python3
"""
Simple Das Handler for Matrix
Works alongside existing agents to handle "das" or "Das" triggers
"""

import asyncio
import logging
import os
import sys
import signal
from typing import Optional

try:
    from nio import AsyncClient, MatrixRoom, RoomMessageText, LoginResponse
except ImportError:
    print("Error: matrix-nio not installed. Please install with: pip install matrix-nio[e2e]")
    sys.exit(1)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class DasHandler:
    """Simple handler that responds to 'das' or 'Das' and triggers responses"""

    def __init__(self):
        # Configuration from environment or defaults
        self.homeserver_url = os.getenv("MATRIX_HOMESERVER_URL", "https://acebuddy.quest")
        self.username = os.getenv("DAS_USERNAME", "@headscarf4716:acebuddy.quest")  # Use your own account
        self.password = os.getenv("DAS_PASSWORD", "")

        # Target rooms where das should work
        self.target_rooms = [
            "!KyOMcaXNWvZvGgPqmw:acebuddy.quest",  # LLM room
            "!aJySTGOBquzIVrrcTB:acebuddy.quest"   # Weather/API room
        ]

        # Bot usernames to call
        self.orchestrator_user = "@unmolded8581:acebuddy.quest"
        self.llm_user = "@subatomic6140:acebuddy.quest"

        # Matrix client
        self.client = AsyncClient(
            homeserver=self.homeserver_url,
            user=self.username,
            store_path=f"/tmp/das_handler_store"
        )

        # Register callback
        self.client.add_event_callback(self._on_message, RoomMessageText)

        # Running state
        self.running = False

        logger.info(f"Das Handler initialized for {self.username}")

    async def start(self) -> bool:
        """Start the das handler"""
        try:
            if not self.password:
                logger.error("DAS_PASSWORD environment variable is required")
                return False

            # Login
            response = await self.client.login(self.password)
            if not isinstance(response, LoginResponse):
                logger.error(f"Failed to login: {response}")
                return False

            logger.info("✅ Das Handler logged in successfully")

            # Join target rooms if not already joined
            for room_id in self.target_rooms:
                try:
                    await self.client.join(room_id)
                    logger.info(f"Joined/confirmed room: {room_id}")
                except Exception as e:
                    logger.warning(f"Could not join room {room_id}: {e}")

            # Start sync
            self.running = True
            await self.client.sync_forever(timeout=30000)
            return True

        except Exception as e:
            logger.error(f"Failed to start das handler: {e}")
            return False

    async def _on_message(self, room: MatrixRoom, event: RoomMessageText):
        """Handle incoming messages"""
        # Ignore own messages
        if event.sender == self.client.user_id:
            return

        # Only work in target rooms
        if room.room_id not in self.target_rooms:
            return

        body = event.body.strip()

        # Check for "das" or "Das" trigger
        if body.lower() == "das" or body == "Das":
            await self._handle_das_request(room, event)

    async def _handle_das_request(self, room: MatrixRoom, event: RoomMessageText):
        """Handle 'das' requests"""
        try:
            logger.info(f"Das trigger detected in {room.room_id} from {event.sender}")

            # Quick acknowledgment
            await self._send_message(room.room_id, "📥 Das request received! Getting assistance...")

            # Small delay for natural feel
            await asyncio.sleep(1)

            # Determine which room we're in and provide appropriate help
            if room.room_id == "!KyOMcaXNWvZvGgPqmw:acebuddy.quest":  # LLM room
                # Call LLM bot directly
                await self._send_message(
                    room.room_id,
                    f"{self.llm_user} Hey buddy! Someone needs help with AI/LLM stuff. Can you assist? 🤖"
                )
                await asyncio.sleep(0.5)
                await self._send_message(
                    room.room_id,
                    "🎯 This is the LLM room - ask questions about AI, coding, analysis, or general assistance!"
                )

            elif room.room_id == "!aJySTGOBquzIVrrcTB:acebuddy.quest":  # Weather/API room
                # Call orchestrator for API stuff
                await self._send_message(
                    room.room_id,
                    f"{self.orchestrator_user} Hey pal! Someone needs help with APIs or weather. Can you coordinate? 🌤️"
                )
                await asyncio.sleep(0.5)
                await self._send_message(
                    room.room_id,
                    "🌍 This is the API/Weather room - ask about weather, web searches, or API integrations!"
                )
            else:
                # Generic help
                await self._send_message(
                    room.room_id,
                    f"{self.llm_user} {self.orchestrator_user} Someone said 'das' - they need help! 🆘"
                )

        except Exception as e:
            logger.error(f"Error handling das request: {e}")
            await self._send_message(room.room_id, "❌ Sorry, had trouble processing that request.")

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
        """Stop the das handler"""
        try:
            self.running = False
            await self.client.close()
            logger.info("🛑 Das Handler stopped")
        except Exception as e:
            logger.error(f"Error stopping das handler: {e}")


def setup_signal_handlers(handler):
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        logger.info(f"📶 Received signal {signum}")
        handler.running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Main function"""
    logger.info("🎯 Das Handler for Matrix")
    logger.info("========================")
    logger.info("Responds to 'das' or 'Das' and calls appropriate bots")
    logger.info("")
    logger.info("Environment variables needed:")
    logger.info("  DAS_PASSWORD - Your Matrix account password")
    logger.info("  DAS_USERNAME - Your Matrix username (optional, defaults to @headscarf4716:acebuddy.quest)")
    logger.info("  MATRIX_HOMESERVER_URL - Matrix server URL (optional)")
    logger.info("")

    handler = DasHandler()
    setup_signal_handlers(handler)

    try:
        await handler.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        await handler.stop()

    logger.info("✨ Das handler exited")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Das handler stopped by user")
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)

#!/usr/bin/env python3
"""
Simple Das Trigger for Matrix
A lightweight script that responds to "das" and triggers existing bots
"""

import asyncio
import logging
import os
import sys
import signal
import random
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

class DasTrigger:
    """Simple trigger that responds to 'das' and coordinates with existing bots"""

    def __init__(self):
        # Configuration
        self.homeserver_url = "https://acebuddy.quest"
        self.username = "@headscarf4716:acebuddy.quest"  # Your account
        self.password = os.getenv("HEADSCARF_PASSWORD", "")

        # Target rooms
        self.target_rooms = [
            "!KyOMcaXNWvZvGgPqmw:acebuddy.quest",  # LLM room
            "!aJySTGOBquzIVrrcTB:acebuddy.quest"   # Weather/API room
        ]

        # Existing bot accounts
        self.orchestrator = "@unmolded8581:acebuddy.quest"
        self.llm_bot = "@subatomic6140:acebuddy.quest"

        # Simple friendly responses
        self.orchestrator_calls = [
            f"{self.orchestrator} buddy, someone needs help here! 🤝",
            f"{self.orchestrator} pal, can you coordinate this request? 🎯",
            f"{self.orchestrator} friend, time to shine! ⭐",
            f"Hey {self.orchestrator}, got a coordination request! 🚀"
        ]

        self.llm_calls = [
            f"{self.llm_bot} buddy, someone needs your expertise! 🧠",
            f"{self.llm_bot} pal, can you help out here? 💡",
            f"{self.llm_bot} friend, time for some AI magic! ✨",
            f"Hey {self.llm_bot}, got a question for you! 🤖"
        ]

        # Matrix client
        self.client = AsyncClient(
            homeserver=self.homeserver_url,
            user=self.username,
            store_path="/tmp/das_trigger_store"
        )

        # Register callback
        self.client.add_event_callback(self._on_message, RoomMessageText)

        self.running = False
        logger.info(f"Das Trigger initialized for {self.username}")

    async def start(self) -> bool:
        """Start the das trigger"""
        if not self.password:
            logger.error("HEADSCARF_PASSWORD environment variable required")
            logger.info("Set it with: export HEADSCARF_PASSWORD='your_password'")
            return False

        try:
            # Login
            response = await self.client.login(self.password)
            if not isinstance(response, LoginResponse):
                logger.error(f"Login failed: {response}")
                return False

            logger.info("✅ Das Trigger logged in successfully")

            # Join target rooms
            for room_id in self.target_rooms:
                try:
                    await self.client.join(room_id)
                    logger.info(f"Joined room: {room_id}")
                except Exception as e:
                    logger.warning(f"Could not join {room_id}: {e}")

            self.running = True
            logger.info("🎯 Das Trigger is ready! Type 'das' in any target room to test.")

            # Start sync
            await self.client.sync_forever(timeout=30000)
            return True

        except Exception as e:
            logger.error(f"Start failed: {e}")
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

        # Check for das trigger
        if body.lower() == "das" or body == "Das":
            await self._handle_das(room, event)

    async def _handle_das(self, room: MatrixRoom, event: RoomMessageText):
        """Handle das trigger - call appropriate bots"""
        try:
            logger.info(f"Das detected in {room.room_id} from {event.sender}")

            # Quick acknowledgment
            await self._send_message(room.room_id, "📥 Das! Getting the team together...")

            await asyncio.sleep(0.5)

            # Determine room and call appropriate bots
            if room.room_id == "!KyOMcaXNWvZvGgPqmw:acebuddy.quest":
                # LLM room - call orchestrator first, then LLM
                orch_call = random.choice(self.orchestrator_calls)
                await self._send_message(room.room_id, orch_call)

                await asyncio.sleep(1)

                llm_call = random.choice(self.llm_calls)
                await self._send_message(room.room_id, llm_call)

                await asyncio.sleep(0.5)
                await self._send_message(room.room_id, "🤖 This is the LLM room - great for AI questions, coding help, and analysis!")

            elif room.room_id == "!aJySTGOBquzIVrrcTB:acebuddy.quest":
                # Weather/API room - orchestrator focus
                orch_call = random.choice(self.orchestrator_calls)
                await self._send_message(room.room_id, orch_call)

                await asyncio.sleep(1)

                llm_call = random.choice(self.llm_calls)
                await self._send_message(room.room_id, llm_call)

                await asyncio.sleep(0.5)
                await self._send_message(room.room_id, "🌤️ This is the API/Weather room - perfect for weather queries and web searches!")

            # Add a friendly demo of how to talk to bots directly
            await asyncio.sleep(1)
            await self._send_message(
                room.room_id,
                f"💡 Tip: You can also talk directly to {self.llm_bot} by just saying hello, or mention them with @!"
            )

        except Exception as e:
            logger.error(f"Error handling das: {e}")

    async def _send_message(self, room_id: str, content: str) -> bool:
        """Send a message to a room"""
        try:
            await self.client.room_send(
                room_id=room_id,
                message_type="m.room.message",
                content={
                    "msgtype": "m.text",
                    "body": content
                },
                ignore_unverified_devices=True
            )
            return True
        except Exception as e:
            logger.error(f"Send error: {e}")
            return False

    async def stop(self):
        """Stop the trigger"""
        try:
            self.running = False
            await self.client.close()
            logger.info("🛑 Das Trigger stopped")
        except Exception as e:
            logger.error(f"Stop error: {e}")


async def main():
    """Main function"""
    print("🎯 Simple Das Trigger for Matrix")
    print("================================")
    print("This script adds 'das' trigger functionality to your existing Matrix bots.")
    print("")
    print("Setup:")
    print("1. Set your password: export HEADSCARF_PASSWORD='your_matrix_password'")
    print("2. Run this script: python3 simple-das-trigger.py")
    print("3. Go to either Matrix room and type 'das' or 'Das'")
    print("4. Watch the orchestrator and LLM bots get called!")
    print("")
    print("Rooms monitored:")
    print("- !KyOMcaXNWvZvGgPqmw:acebuddy.quest (LLM)")
    print("- !aJySTGOBquzIVrrcTB:acebuddy.quest (Weather/API)")
    print("")

    trigger = DasTrigger()

    def signal_handler(signum, frame):
        logger.info(f"Signal {signum} received")
        trigger.running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await trigger.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        await trigger.stop()

    print("\n👋 Das Trigger stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
    except Exception as e:
        print(f"💥 Error: {e}")
        sys.exit(1)

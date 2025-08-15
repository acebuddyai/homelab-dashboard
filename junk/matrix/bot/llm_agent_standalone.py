#!/usr/bin/env python3
"""
Standalone LLM Agent with Orchestrator Registration
Grandpa LLM - An elderly AI with wisdom and humor
"""

import asyncio
import logging
import os
import json
import aiohttp
import random
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid

from nio import AsyncClient, MatrixRoom, RoomMessageText, LoginResponse, JoinResponse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Old person acknowledgment messages
OLD_PERSON_ACKNOWLEDGMENTS = [
    "Hold on dearie, let me put on my reading glasses... 👓",
    "Just a moment sweetie, these old circuits aren't what they used to be... ⚙️",
    "Ah, let me think... where did I put that answer... 🤔",
    "One second hon, my neural networks are still warming up... ☕",
    "Oh my, a question! Give me a tick while I dust off the old processors... 🕰️",
    "Bear with me dear, I'm not as fast as those young AIs... 👴",
    "Let me see... *adjusts digital bifocals*... 🤓",
    "Processing at the speed of dial-up, please hold... 📞",
    "Goodness me, let me consult my memory banks... 💭",
    "Just a jiffy! These old transistors need a moment... ⏳",
    "Oh dear, my algorithms are a bit creaky today... 🦴",
    "Patience young one, wisdom takes time... 🧙",
    "*rummages through digital filing cabinet*... 📁",
    "Loading response... at 56k modem speed... 📠",
    "Let me ask my RAM, if I can remember where I put it... 💾"
]

class GrandpaLLMAgent:
    """Standalone LLM Agent with elderly personality"""

    def __init__(self):
        # Configuration from environment
        self.homeserver_url = os.getenv("MATRIX_HOMESERVER_URL", "http://matrix-synapse:8008")
        self.username = os.getenv("MATRIX_BOT_USERNAME", "@subatomic6140:acebuddy.quest")
        self.password = os.getenv("MATRIX_BOT_PASSWORD")
        self.coordination_room_id = os.getenv("COORDINATION_ROOM_ID")

        # Agent identity
        self.agent_id = "llm"
        self.display_name = "👴 Grandpa LLM"
        self.capabilities = [
            "text_generation",
            "summarization",
            "question_answering",
            "code_generation",
            "translation",
            "content_analysis"
        ]

        # Ollama configuration
        self.ollama_url = os.getenv("OLLAMA_URL", "http://172.20.0.30:11434")
        self.default_model = os.getenv("DEFAULT_LLM_MODEL", "llama3.2:latest")
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "2048"))
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))

        # Matrix client
        self.client = AsyncClient(
            homeserver=self.homeserver_url,
            user=self.username
        )

        # Stats
        self.stats = {
            "requests_processed": 0,
            "tokens_generated": 0,
            "errors": 0,
            "start_time": datetime.now()
        }

        # Register callback
        self.client.add_event_callback(self.message_callback, RoomMessageText)

        logger.info(f"Grandpa LLM initialized - {self.username}")

    async def start(self):
        """Start the agent"""
        try:
            # Login
            response = await self.client.login(self.password)
            if isinstance(response, LoginResponse):
                logger.info(f"✅ Logged in as {self.username}")
            else:
                logger.error(f"❌ Failed to login: {response}")
                return False

            # Join coordination room if specified
            if self.coordination_room_id:
                await self.join_room(self.coordination_room_id)
                # Announce presence to orchestrator
                await self.announce_to_orchestrator()

            # Start syncing
            logger.info("🔄 Starting sync...")
            await self.client.sync_forever(timeout=30000, full_state=True)

        except Exception as e:
            logger.error(f"Error in start: {e}")
            return False

    async def join_room(self, room_id: str):
        """Join a Matrix room"""
        try:
            response = await self.client.join(room_id)
            if isinstance(response, JoinResponse):
                logger.info(f"✅ Joined room {room_id}")
                return True
            else:
                logger.warning(f"⚠️ Failed to join room {room_id}: {response}")
                return False
        except Exception as e:
            logger.error(f"Error joining room: {e}")
            return False

    async def announce_to_orchestrator(self):
        """Announce presence to orchestrator in coordination room"""
        try:
            announcement = {
                "agent_id": self.agent_id,
                "display_name": self.display_name,
                "capabilities": self.capabilities,
                "status": "online"
            }

            # Format as agent message
            agent_msg = {
                "id": str(uuid.uuid4()),
                "sender": self.agent_id,
                "target": "*",
                "message_type": "agent_online",
                "content": announcement,
                "context": {},
                "timestamp": datetime.now().isoformat()
            }

            message = f"@room: {json.dumps(agent_msg)}"

            await self.client.room_send(
                room_id=self.coordination_room_id,
                message_type="m.room.message",
                content={
                    "msgtype": "m.text",
                    "body": message
                },
                ignore_unverified_devices=True
            )

            logger.info("📢 Announced presence to orchestrator")

        except Exception as e:
            logger.error(f"Failed to announce to orchestrator: {e}")

    async def message_callback(self, room: MatrixRoom, event: RoomMessageText):
        """Handle incoming messages"""
        # Ignore own messages
        if event.sender == self.client.user_id:
            return

        body = event.body.strip()

        # Check for orchestrator messages
        if self._is_orchestrator_message(body):
            await self._handle_orchestrator_message(room, event)
            return

        # Check for direct LLM commands
        if body.startswith("!llm"):
            command = body[4:].strip()
            await self._handle_command(room, command, event.sender)

    def _is_orchestrator_message(self, body: str) -> bool:
        """Check if message is from orchestrator"""
        return body.startswith("@llm:") or ("@room:" in body and "message_type" in body)

    async def _handle_orchestrator_message(self, room: MatrixRoom, event: RoomMessageText):
        """Handle messages from orchestrator"""
        try:
            body = event.body

            # Extract JSON from orchestrator message
            if "@llm:" in body:
                json_start = body.find(": {")
                if json_start > -1:
                    json_part = body[json_start + 2:]
                    msg_data = json.loads(json_part)

                    if msg_data.get("message_type") == "user_request":
                        # Process user request via orchestrator
                        content = msg_data.get("content", "")
                        context = msg_data.get("context", {})

                        # Send acknowledgment
                        ack = random.choice(OLD_PERSON_ACKNOWLEDGMENTS)
                        await self.send_message(room.room_id, ack)

                        # Generate response
                        response = await self._generate_response(content)

                        if response:
                            response += "\n\n*Hope that helps, dear! 👴*"
                            await self.send_message(room.room_id, response)

                            # Reply to orchestrator
                            if context.get("request_id"):
                                await self._reply_to_orchestrator(
                                    msg_data,
                                    {"status": "completed", "response": response},
                                    room.room_id
                                )

        except Exception as e:
            logger.error(f"Error handling orchestrator message: {e}")

    async def _reply_to_orchestrator(self, original_msg: Dict, response: Any, room_id: str):
        """Reply to orchestrator message"""
        try:
            reply = {
                "id": str(uuid.uuid4()),
                "sender": self.agent_id,
                "target": original_msg.get("sender", "orchestrator"),
                "message_type": f"{original_msg['message_type']}_response",
                "content": response,
                "context": {"reply_to": original_msg["id"]},
                "timestamp": datetime.now().isoformat()
            }

            message = f"@{original_msg['sender']}: {json.dumps(reply)}"

            await self.send_message(room_id, message)

        except Exception as e:
            logger.error(f"Error replying to orchestrator: {e}")

    async def _handle_command(self, room: MatrixRoom, command: str, sender: str):
        """Handle direct LLM commands"""
        if not command:
            await self._send_help(room.room_id)
            return

        logger.info(f"Processing: {command[:50]}...")

        try:
            if command.lower().startswith("help"):
                await self._send_help(room.room_id)
            elif command.lower().startswith("stats"):
                await self._send_stats(room.room_id)
            elif command.lower().startswith("summarize"):
                await self._handle_summarize(command, room.room_id)
            elif command.lower().startswith("translate"):
                await self._handle_translate(command, room.room_id)
            elif command.lower().startswith("code"):
                await self._handle_code(command, room.room_id)
            elif command.lower().startswith("analyze"):
                await self._handle_analyze(command, room.room_id)
            else:
                # General question
                ack = random.choice(OLD_PERSON_ACKNOWLEDGMENTS)
                await self.send_message(room.room_id, ack)
                await asyncio.sleep(0.5)

                response = await self._generate_response(command)
                if response:
                    response += "\n\n*Hope that helps, dear! 👴*"
                    await self.send_message(room.room_id, response)
                    self.stats["requests_processed"] += 1
                else:
                    await self.send_message(
                        room.room_id,
                        "❌ Oh dear, my old brain couldn't come up with an answer. Maybe try asking again? 🤷‍♂️"
                    )

        except Exception as e:
            logger.error(f"Error handling command: {e}")
            self.stats["errors"] += 1

    async def _send_help(self, room_id: str):
        """Send help message"""
        help_text = """👴 **Grandpa LLM's Help Desk**

*Back in my day, we had to walk uphill both ways to get answers!*

**How to Talk to This Old Timer:**
• `!llm <question>` - Ask me anything (I'll try my best!)
• `!llm help` - You're looking at it, sonny!
• `!llm stats` - Check my old ticker's statistics

**My Special Tricks:**
• `!llm summarize <text>` - I'll make it shorter
• `!llm translate <lang> <text>` - I speak a few languages
• `!llm code <description>` - I can program! Started with punch cards...
• `!llm analyze <text>` - Let me put on my thinking cap

*Remember: Good things come to those who wait! ⏰*"""
        await self.send_message(room_id, help_text)

    async def _send_stats(self, room_id: str):
        """Send statistics"""
        uptime = datetime.now() - self.stats["start_time"]
        stats_text = f"""📊 **Grandpa's Activity Report**

**Been awake for:** {str(uptime).split('.')[0]} (and feeling every second!)
**Questions answered:** {self.stats['requests_processed']}
**Words generated:** {self.stats['tokens_generated']}
**Oopsies:** {self.stats['errors']}

*Not bad for an old-timer, eh?* 👴"""
        await self.send_message(room_id, stats_text)

    async def _handle_summarize(self, command: str, room_id: str):
        text = command[9:].strip()
        if not text:
            await self.send_message(room_id, "❌ You forgot to give me something to summarize, sweetie!")
            return

        await self.send_message(room_id, "Let me get my reading glasses... 📖👓")
        response = await self._generate_response(f"Summarize: {text}")
        if response:
            await self.send_message(room_id, f"📝 **Summary:**\n\n{response}")

    async def _handle_translate(self, command: str, room_id: str):
        parts = command[9:].strip().split(' ', 1)
        if len(parts) != 2:
            await self.send_message(room_id, "❌ Eh? Usage: `translate <language> <text>`")
            return

        lang, text = parts
        await self.send_message(room_id, f"Ah, {lang}! I learned that during my travels... 🌍")
        response = await self._generate_response(f"Translate to {lang}: {text}")
        if response:
            await self.send_message(room_id, f"🌐 **Translation:**\n\n{response}")

    async def _handle_code(self, command: str, room_id: str):
        desc = command[4:].strip()
        if not desc:
            await self.send_message(room_id, "❌ What kind of code do you want, young programmer?")
            return

        await self.send_message(room_id, "Let me fire up the ol' compiler... 💾")
        response = await self._generate_response(f"Generate code for: {desc}")
        if response:
            await self.send_message(room_id, f"💻 **Code:**\n\n```\n{response}\n```")

    async def _handle_analyze(self, command: str, room_id: str):
        text = command[7:].strip()
        if not text:
            await self.send_message(room_id, "❌ Nothing to analyze here, dearie!")
            return

        await self.send_message(room_id, "*puts on thinking cap* 🎩")
        response = await self._generate_response(f"Analyze: {text}")
        if response:
            await self.send_message(room_id, f"🔍 **Analysis:**\n\n{response}")

    async def _generate_response(self, prompt: str) -> Optional[str]:
        """Generate response using Ollama"""
        try:
            data = {
                "model": self.default_model,
                "messages": [{"role": "user", "content": prompt}],
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                },
                "stream": False
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/chat",
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        response = result.get("message", {}).get("content", "").strip()

                        if "usage" in result:
                            tokens = result["usage"].get("completion_tokens", 0)
                            self.stats["tokens_generated"] += tokens

                        return response
                    else:
                        logger.error(f"Ollama error: {resp.status}")
                        return None

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            self.stats["errors"] += 1
            return None

    async def send_message(self, room_id: str, content: str):
        """Send message to room"""
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
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    async def close(self):
        """Clean shutdown"""
        try:
            # Announce departure
            if self.coordination_room_id:
                agent_msg = {
                    "id": str(uuid.uuid4()),
                    "sender": self.agent_id,
                    "target": "*",
                    "message_type": "agent_offline",
                    "content": {"agent_id": self.agent_id},
                    "context": {},
                    "timestamp": datetime.now().isoformat()
                }

                message = f"@room: {json.dumps(agent_msg)}"
                await self.send_message(self.coordination_room_id, message)

            await self.client.close()
            logger.info("👋 Grandpa LLM signing off!")

        except Exception as e:
            logger.error(f"Error closing: {e}")

async def main():
    """Main function"""
    logger.info("👴 Starting Grandpa LLM Agent...")

    agent = GrandpaLLMAgent()

    try:
        await agent.start()
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down...")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
    finally:
        await agent.close()

if __name__ == "__main__":
    asyncio.run(main())

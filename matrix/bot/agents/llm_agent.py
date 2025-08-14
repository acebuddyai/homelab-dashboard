#!/usr/bin/env python3
"""
LLM Agent - Specialized agent for Large Language Model interactions
Integrates with existing Ollama setup and provides text generation capabilities
"""

import asyncio
import logging
import json
import os
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime

from nio import MatrixRoom, RoomMessageText

from .base_agent import BaseMatrixAgent, AgentMessage, parse_mention, format_agent_response

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

class LLMAgent(BaseMatrixAgent):
    """
    LLM Agent for text generation, summarization, and Q&A

    Capabilities:
    - Text generation
    - Summarization
    - Question answering
    - Code generation
    - Language translation
    - Content analysis
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
            display_name="👴 Grandpa LLM",
            capabilities=[
                "text_generation",
                "summarization",
                "question_answering",
                "code_generation",
                "translation",
                "content_analysis",
                "conversation"
            ],
            store_path=store_path
        )

        # Ollama configuration
        self.ollama_url = os.getenv("OLLAMA_URL", "http://172.20.0.30:11434")
        self.default_model = os.getenv("DEFAULT_LLM_MODEL", "llama3.2:latest")

        # Model configuration
        self.available_models = []
        self.model_capabilities = {
            "llama3.2:latest": ["general", "code", "analysis"],
            "llama3.2:3b": ["fast", "general"],
            "codellama:latest": ["code", "programming"],
            "mistral:latest": ["general", "creative"]
        }

        # Response settings
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "2048"))
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))

        # Conversation context
        self.conversation_history = {}  # room_id -> list of messages
        self.max_history_length = 10

        # Processing stats
        self.stats = {
            "requests_processed": 0,
            "tokens_generated": 0,
            "errors": 0,
            "start_time": datetime.now()
        }

        # Register message handlers
        self._register_handlers()

        logger.info("LLM Agent initialized with Ollama integration")

    def _get_random_acknowledgment(self) -> str:
        """Get a random old person acknowledgment message"""
        import random
        return random.choice(OLD_PERSON_ACKNOWLEDGMENTS)

    async def _send_quick_acknowledgment(self, room_id: str):
        """Send a quick acknowledgment before processing"""
        ack_message = self._get_random_acknowledgment()
        await self.send_message(room_id, ack_message)
        # Small delay for effect
        await asyncio.sleep(0.5)

    def _register_handlers(self):
        """Register handlers for different message types"""
        self.register_message_handler("user_request", self._handle_user_request)
        self.register_message_handler("generate_text", self._handle_generate_text)
        self.register_message_handler("summarize", self._handle_summarize)
        self.register_message_handler("analyze", self._handle_analyze)
        self.register_message_handler("translate", self._handle_translate)
        self.register_message_handler("code_gen", self._handle_code_generation)
        self.register_message_handler("workflow_step", self._handle_workflow_step)

    async def start(self) -> bool:
        """Start the LLM agent and check Ollama connection"""
        success = await super().start()
        if success:
            # Test Ollama connection and load available models
            await self._initialize_ollama()
        return success

    async def _initialize_ollama(self):
        """Initialize Ollama connection and load available models"""
        try:
            # Test connection and get available models
            models = await self._get_available_models()
            if models:
                self.available_models = models
                logger.info(f"Connected to Ollama with {len(models)} models available")
            else:
                logger.warning("No models available in Ollama")

            # Pull default model if not available
            if self.default_model not in [m['name'] for m in models]:
                logger.info(f"Pulling default model: {self.default_model}")
                await self._pull_model(self.default_model)

        except Exception as e:
            logger.error(f"Failed to initialize Ollama: {e}")

    async def process_user_message(self, room: MatrixRoom, event: RoomMessageText):
        """Process messages from human users"""
        body = event.body.strip()
        sender = event.sender

        # Check if message mentions LLM agent
        command = parse_mention(body, self.agent_id)
        if not command and not body.startswith("!llm"):
            return

        # Extract command
        if body.startswith("!llm"):
            command = body[4:].strip()

        if not command:
            await self._send_help(room.room_id)
            return

        logger.info(f"Processing LLM request from {sender}: {command[:50]}...")

        try:
            # Update conversation history
            self._update_conversation_history(room.room_id, sender, command)

            # Process different command types
            if command.lower().startswith("help"):
                await self._send_help(room.room_id)
            elif command.lower().startswith("models"):
                await self._send_available_models(room.room_id)
            elif command.lower().startswith("stats"):
                await self._send_stats(room.room_id)
            elif command.lower().startswith("summarize"):
                await self._handle_summarize_command(command, room.room_id)
            elif command.lower().startswith("translate"):
                await self._handle_translate_command(command, room.room_id)
            elif command.lower().startswith("code"):
                await self._handle_code_command(command, room.room_id)
            elif command.lower().startswith("analyze"):
                await self._handle_analyze_command(command, room.room_id)
            else:
                # Default to general text generation
                await self._handle_general_request(command, room.room_id, sender)

        except Exception as e:
            logger.error(f"Error processing LLM request: {e}")
            await self.send_message(
                room.room_id,
                f"❌ Error processing request: {str(e)}"
            )

    async def _send_help(self, room_id: str):
        """Send help message"""
        help_text = """👴 **Grandpa LLM's Help Desk**

*Back in my day, we had to walk uphill both ways to get answers!*

**How to Talk to This Old Timer:**
• `!llm <question>` - Ask me anything (I'll try my best!)
• `!llm help` - You're looking at it, sonny!
• `!llm models` - See what's in my dusty toolkit
• `!llm stats` - Check my old ticker's statistics

**My Special Tricks (learned these before the internet!):**
• `!llm summarize <text>` - I'll make it shorter (attention span ain't what it was)
• `!llm translate <lang> <text>` - I speak a few languages from my travels
• `!llm code <description>` - I can program! Started with punch cards...
• `!llm analyze <text>` - Let me put on my thinking cap

**Examples for You Young'uns:**
• `!llm What is quantum computing?` (It's complicated, like my TV remote)
• `!llm summarize [long text]` (I'll get to the point eventually)
• `!llm translate spanish Hello world` (¡Hola mundo! See, still got it!)
• `!llm code Python function to sort a list` (Python? In my day it was COBOL!)

*Remember: Good things come to those who wait! ⏰*
"""
        await self.send_message(room_id, help_text)

    async def _send_available_models(self, room_id: str):
        """Send list of available models"""
        if not self.available_models:
            await self.send_message(room_id, "❌ No models available")
            return

        models_text = "🤖 **Available Models:**\n\n"
        for model in self.available_models:
            name = model.get('name', 'Unknown')
            size = model.get('size', 0)
            size_mb = round(size / 1024 / 1024, 1) if size > 0 else 0

            # Get capabilities if known
            capabilities = self.model_capabilities.get(name, ["general"])
            caps_text = ", ".join(capabilities)

            default_marker = " ⭐" if name == self.default_model else ""
            models_text += f"• **{name}**{default_marker}\n"
            models_text += f"  📦 Size: {size_mb} MB\n"
            models_text += f"  ⚡ Capabilities: {caps_text}\n\n"

        await self.send_message(room_id, models_text)

    async def _send_stats(self, room_id: str):
        """Send usage statistics"""
        uptime = datetime.now() - self.stats["start_time"]

        stats_text = f"""📊 **Grandpa's Activity Report**

**Been awake for:** {str(uptime).split('.')[0]} (and feeling every second!)
**Questions answered:** {self.stats['requests_processed']} (my memory's still sharp!)
**Words generated:** {self.stats['tokens_generated']} (that's a lot of typing with these arthritic joints!)
**Oopsies:** {self.stats['errors']} (nobody's perfect at my age!)
**Ongoing chats:** {len(self.conversation_history)} (I'm popular!)

**Current brain model:** {self.default_model} (vintage but reliable!)
**Word limit:** {self.max_tokens} (I can be long-winded...)
**Creativity level:** {self.temperature} (still got some spunk!)
**Connected to:** {self.ollama_url} (the newfangled computer thingy)

*Not bad for an old-timer, eh?* 👴
"""
        await self.send_message(room_id, stats_text)

    async def _handle_general_request(self, prompt: str, room_id: str, sender: str):
        """Handle general text generation request"""
        try:
            # Send quick acknowledgment first
            await self._send_quick_acknowledgment(room_id)

            # Get conversation context
            context = self._get_conversation_context(room_id)

            # Generate response
            response = await self._generate_response(prompt, context)

            if response:
                # Update conversation history
                self._update_conversation_history(room_id, self.agent_id, response)

                # Add a bit of personality to the response
                if response and not response.startswith("❌"):
                    response = f"{response}\n\n*Hope that helps, dear! 👴*"

                # Send response
                await self.send_message(room_id, response)

                self.stats["requests_processed"] += 1
            else:
                await self.send_message(room_id, "❌ Oh dear, my old brain couldn't come up with an answer. Maybe try asking again? Sometimes I need a second attempt... 🤷‍♂️")

        except Exception as e:
            logger.error(f"Error handling general request: {e}")
            self.stats["errors"] += 1
            await self.send_message(room_id, f"❌ Error: {str(e)}")

    # Command handlers
    async def _handle_summarize_command(self, command: str, room_id: str):
        """Handle summarize command"""
        text_to_summarize = command[9:].strip()  # Remove "summarize"

        if not text_to_summarize:
            await self.send_message(room_id, "❌ You forgot to give me something to summarize, sweetie! My mind-reading days are behind me... 🔮")
            return

        # Send acknowledgment
        await self.send_message(room_id, "Let me get my reading glasses and make this shorter for you... 📖👓")

        prompt = f"Please provide a concise summary of the following text:\n\n{text_to_summarize}"
        response = await self._generate_response(prompt)

        if response:
            formatted_response = f"📝 **Summary:**\n\n{response}"
            await self.send_message(room_id, formatted_response)
        else:
            await self.send_message(room_id, "❌ Failed to generate summary")

    async def _handle_translate_command(self, command: str, room_id: str):
        """Handle translate command"""
        parts = command[9:].strip().split(' ', 1)  # Remove "translate"

        if len(parts) != 2:
            await self.send_message(room_id, "❌ Eh? Speak up! Usage: `translate <language> <text>` - My hearing aid needs clear instructions! 🦻")
            return

        # Send acknowledgment
        await self.send_message(room_id, f"Ah, {parts[0]}! I learned that during my travels in '72... or was it '73? Anyway, translating... 🌍")

        target_language, text = parts
        prompt = f"Translate the following text to {target_language}:\n\n{text}"

        response = await self._generate_response(prompt)

        if response:
            formatted_response = f"🌐 **Translation to {target_language}:**\n\n{response}"
            await self.send_message(room_id, formatted_response)
        else:
            await self.send_message(room_id, "❌ Failed to translate text")

    async def _handle_code_command(self, command: str, room_id: str):
        """Handle code generation command"""
        description = command[4:].strip()  # Remove "code"

        if not description:
            await self.send_message(room_id, "❌ What kind of code do you want, young programmer? In my day we used punch cards! 💳")
            return

        # Send acknowledgment
        await self.send_message(room_id, "Let me fire up the ol' compiler... Started coding in FORTRAN back in '69! 💾")

        prompt = f"Generate clean, well-commented code for: {description}"
        response = await self._generate_response(prompt, model="codellama:latest")

        if response:
            # Format as code block
            formatted_response = f"💻 **Generated Code:**\n\n```\n{response}\n```"
            await self.send_message(room_id, formatted_response)
        else:
            await self.send_message(room_id, "❌ Failed to generate code")

    async def _handle_analyze_command(self, command: str, room_id: str):
        """Handle content analysis command"""
        text_to_analyze = command[7:].strip()  # Remove "analyze"

        if not text_to_analyze:
            await self.send_message(room_id, "❌ Nothing to analyze here, dearie! Give this old brain something to chew on! 🧠")
            return

        # Send acknowledgment
        await self.send_message(room_id, "*puts on thinking cap and spectacles* Let me analyze this like we did in the old days... 🎩")

        prompt = f"Analyze the following text for sentiment, tone, key themes, and insights:\n\n{text_to_analyze}"
        response = await self._generate_response(prompt)

        if response:
            formatted_response = f"🔍 **Analysis:**\n\n{response}"
            await self.send_message(room_id, formatted_response)
        else:
            await self.send_message(room_id, "❌ Failed to analyze text")

    # Agent message handlers
    async def _handle_user_request(self, agent_msg: AgentMessage, room: MatrixRoom):
        """Handle user request from orchestrator"""
        try:
            content = agent_msg.content
            context = agent_msg.context

            response = await self._generate_response(content)

            if response:
                # Send response back to room
                await self.send_message(room.room_id, response)

                # Reply to orchestrator if needed
                if context.get("request_id"):
                    await self.reply_to_agent(
                        agent_msg,
                        {"status": "completed", "response": response},
                        room.room_id
                    )
            else:
                await self.reply_to_agent(
                    agent_msg,
                    {"status": "failed", "error": "Failed to generate response"},
                    room.room_id
                )

        except Exception as e:
            logger.error(f"Error handling user request from agent: {e}")

    async def _handle_generate_text(self, agent_msg: AgentMessage, room: MatrixRoom):
        """Handle text generation request from another agent"""
        try:
            prompt = agent_msg.content.get("prompt", "")
            options = agent_msg.content.get("options", {})

            response = await self._generate_response(prompt, **options)

            await self.reply_to_agent(
                agent_msg,
                {"generated_text": response} if response else {"error": "Generation failed"},
                room.room_id
            )

        except Exception as e:
            logger.error(f"Error handling generate_text request: {e}")

    async def _handle_summarize(self, agent_msg: AgentMessage, room: MatrixRoom):
        """Handle summarization request from another agent"""
        try:
            text = agent_msg.content.get("text", "")
            max_length = agent_msg.content.get("max_length", "brief")

            prompt = f"Provide a {max_length} summary of: {text}"
            response = await self._generate_response(prompt)

            await self.reply_to_agent(
                agent_msg,
                {"summary": response} if response else {"error": "Summarization failed"},
                room.room_id
            )

        except Exception as e:
            logger.error(f"Error handling summarize request: {e}")

    async def _handle_analyze(self, agent_msg: AgentMessage, room: MatrixRoom):
        """Handle analysis request from another agent"""
        try:
            text = agent_msg.content.get("text", "")
            analysis_type = agent_msg.content.get("type", "general")

            prompt = f"Perform {analysis_type} analysis on: {text}"
            response = await self._generate_response(prompt)

            await self.reply_to_agent(
                agent_msg,
                {"analysis": response} if response else {"error": "Analysis failed"},
                room.room_id
            )

        except Exception as e:
            logger.error(f"Error handling analyze request: {e}")

    async def _handle_translate(self, agent_msg: AgentMessage, room: MatrixRoom):
        """Handle translation request from another agent"""
        try:
            text = agent_msg.content.get("text", "")
            target_language = agent_msg.content.get("target_language", "English")

            prompt = f"Translate to {target_language}: {text}"
            response = await self._generate_response(prompt)

            await self.reply_to_agent(
                agent_msg,
                {"translation": response} if response else {"error": "Translation failed"},
                room.room_id
            )

        except Exception as e:
            logger.error(f"Error handling translate request: {e}")

    async def _handle_code_generation(self, agent_msg: AgentMessage, room: MatrixRoom):
        """Handle code generation request from another agent"""
        try:
            description = agent_msg.content.get("description", "")
            language = agent_msg.content.get("language", "")

            prompt = f"Generate {language} code for: {description}"
            response = await self._generate_response(prompt, model="codellama:latest")

            await self.reply_to_agent(
                agent_msg,
                {"code": response} if response else {"error": "Code generation failed"},
                room.room_id
            )

        except Exception as e:
            logger.error(f"Error handling code generation request: {e}")

    async def _handle_workflow_step(self, agent_msg: AgentMessage, room: MatrixRoom):
        """Handle workflow step from orchestrator"""
        try:
            input_data = agent_msg.content
            context = agent_msg.context

            # Process the input data
            response = await self._generate_response(str(input_data))

            # Send response back to orchestrator
            await self.reply_to_agent(
                agent_msg,
                {"output": response, "status": "completed"},
                room.room_id
            )

        except Exception as e:
            logger.error(f"Error handling workflow step: {e}")

    # Ollama integration
    async def _generate_response(self,
                                prompt: str,
                                context: Optional[List[Dict]] = None,
                                model: Optional[str] = None,
                                **options) -> Optional[str]:
        """Generate response using Ollama"""
        try:
            model = model or self.default_model

            # Prepare messages
            messages = []

            # Add context if provided
            if context:
                messages.extend(context)

            # Add current prompt
            messages.append({"role": "user", "content": prompt})

            # Prepare request
            data = {
                "model": model,
                "messages": messages,
                "options": {
                    "temperature": options.get("temperature", self.temperature),
                    "num_predict": options.get("max_tokens", self.max_tokens)
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
                        response_text = result.get("message", {}).get("content", "")

                        # Update stats
                        if "usage" in result:
                            tokens = result["usage"].get("completion_tokens", 0)
                            self.stats["tokens_generated"] += tokens

                        return response_text.strip()
                    else:
                        logger.error(f"Ollama request failed: {resp.status}")
                        return None

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            self.stats["errors"] += 1
            return None

    async def _get_available_models(self) -> List[Dict]:
        """Get list of available models from Ollama"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_url}/api/tags") as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result.get("models", [])
                    return []

        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return []

    async def _pull_model(self, model_name: str) -> bool:
        """Pull a model in Ollama"""
        try:
            data = {"name": model_name}

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/pull",
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=600)  # 10 minutes for model download
                ) as resp:
                    return resp.status == 200

        except Exception as e:
            logger.error(f"Error pulling model {model_name}: {e}")
            return False

    # Conversation management
    def _update_conversation_history(self, room_id: str, sender: str, message: str):
        """Update conversation history for context"""
        if room_id not in self.conversation_history:
            self.conversation_history[room_id] = []

        history = self.conversation_history[room_id]
        history.append({
            "role": "user" if sender != self.agent_id else "assistant",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })

        # Keep only recent messages
        if len(history) > self.max_history_length:
            self.conversation_history[room_id] = history[-self.max_history_length:]

    def _get_conversation_context(self, room_id: str) -> List[Dict]:
        """Get conversation context for room"""
        return self.conversation_history.get(room_id, [])

    async def get_status(self) -> Dict[str, Any]:
        """Return agent status"""
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "capabilities": self.capabilities,
            "model": self.default_model,
            "available_models": len(self.available_models),
            "stats": self.stats,
            "active_conversations": len(self.conversation_history)
        }

    async def handle_health_check(self) -> Dict[str, Any]:
        """Handle health check requests"""
        # Test Ollama connection
        try:
            models = await self._get_available_models()
            ollama_healthy = len(models) > 0
        except:
            ollama_healthy = False

        return {
            "status": "healthy" if ollama_healthy else "degraded",
            "timestamp": datetime.now().isoformat(),
            "agent_id": self.agent_id,
            "ollama_connection": ollama_healthy,
            "available_models": len(self.available_models),
            "stats": self.stats
        }

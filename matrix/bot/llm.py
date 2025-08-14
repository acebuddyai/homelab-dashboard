#!/usr/bin/env python3
"""
Matrix LLM Agent Launcher
Main entry point for the LLM agent in the multi-agent system
"""

import asyncio
import logging
import os
import sys
import signal
from pathlib import Path

# Add the agents directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents'))

from agents.llm_agent import LLMAgent

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/store/llm_agent.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

class LLMAgentLauncher:
    """Launcher and lifecycle manager for the LLM agent"""

    def __init__(self):
        self.agent = None
        self.running = False

    async def start(self):
        """Start the LLM agent"""
        try:
            # Validate environment variables
            required_vars = [
                "MATRIX_HOMESERVER_URL",
                "MATRIX_BOT_USERNAME",
                "MATRIX_BOT_PASSWORD"
            ]

            missing_vars = [var for var in required_vars if not os.getenv(var)]
            if missing_vars:
                logger.error(f"Missing required environment variables: {missing_vars}")
                return False

            # Create store directory
            store_path = os.getenv("BOT_STORE_DIR", "/app/store")
            Path(store_path).mkdir(parents=True, exist_ok=True)

            logger.info("🧠 Starting Matrix LLM Agent...")

            # Check Ollama connection
            ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
            logger.info(f"🔗 Connecting to Ollama at: {ollama_url}")

            # Initialize agent
            self.agent = LLMAgent(
                homeserver_url=os.getenv("MATRIX_HOMESERVER_URL"),
                username=os.getenv("MATRIX_BOT_USERNAME"),
                password=os.getenv("MATRIX_BOT_PASSWORD"),
                store_path=store_path
            )

            # Start agent
            success = await self.agent.start()
            if success:
                self.running = True
                logger.info("✅ LLM Agent started successfully")

                # Log configuration
                logger.info(f"🎯 Default model: {self.agent.default_model}")
                logger.info(f"📊 Max tokens: {self.agent.max_tokens}")
                logger.info(f"🌡️ Temperature: {self.agent.temperature}")
                logger.info(f"🤖 Available models: {len(self.agent.available_models)}")

                return True
            else:
                logger.error("❌ Failed to start LLM agent")
                return False

        except Exception as e:
            logger.error(f"💥 Error starting LLM agent: {e}")
            return False

    async def stop(self):
        """Stop the LLM agent"""
        if self.agent and self.running:
            logger.info("🛑 Stopping LLM agent...")
            await self.agent.stop()
            self.running = False
            logger.info("👋 LLM agent stopped")

    async def run(self):
        """Main run loop"""
        if not await self.start():
            return

        try:
            # Keep running until interrupted
            while self.running:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("⏹️ Received interrupt signal")
        except Exception as e:
            logger.error(f"💥 Unexpected error in run loop: {e}")
        finally:
            await self.stop()

def setup_signal_handlers(launcher):
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        logger.info(f"📶 Received signal {signum}")
        launcher.running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

async def health_check():
    """Perform health check for the LLM agent"""
    try:
        import aiohttp

        # Check Ollama connection
        ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{ollama_url}/api/tags", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    logger.info("✅ Ollama connection healthy")
                    return True
                else:
                    logger.warning(f"⚠️ Ollama connection issue: {resp.status}")
                    return False

    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return False

async def main():
    """Main function"""
    logger.info("🚀 Matrix LLM Agent Launcher")
    logger.info("============================")

    # Perform initial health check
    logger.info("🔍 Performing health check...")
    if not await health_check():
        logger.warning("⚠️ Health check failed, but continuing anyway...")

    launcher = LLMAgentLauncher()
    setup_signal_handlers(launcher)

    try:
        await launcher.run()
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)

    logger.info("✨ LLM agent launcher exited")

if __name__ == "__main__":
    asyncio.run(main())

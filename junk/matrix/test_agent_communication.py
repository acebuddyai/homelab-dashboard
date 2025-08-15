#!/usr/bin/env python3
"""
Test script to verify Matrix multi-agent communication
Tests agent discovery, registration, and inter-agent messaging
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from nio import AsyncClient, LoginResponse, RoomMessageText
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AgentCommunicationTester:
    def __init__(self):
        self.homeserver = "http://matrix-synapse:8008"
        self.coordination_room = "!jmBxWMDJcwdoMnXGJE:acebuddy.quest"

        # Test client credentials (using orchestrator account)
        self.username = "@unmolded8581:acebuddy.quest"
        self.password = "evacuate-gambling2-penniless"

        self.client = None
        self.test_results = {
            "agent_discovery": False,
            "llm_response": False,
            "orchestrator_coordination": False,
            "inter_agent_messaging": False,
            "workflow_execution": False
        }

        self.discovered_agents = {}
        self.message_log = []

    async def setup(self):
        """Initialize the test client and join coordination room"""
        self.client = AsyncClient(self.homeserver, self.username)

        # Add message callback
        self.client.add_event_callback(self.message_callback, RoomMessageText)

        # Login
        response = await self.client.login(self.password)
        if not isinstance(response, LoginResponse):
            logger.error(f"Failed to login: {response}")
            return False

        logger.info("✅ Test client logged in successfully")

        # Join coordination room
        await self.client.join(self.coordination_room)
        logger.info(f"✅ Joined coordination room: {self.coordination_room}")

        # Start sync in background
        asyncio.create_task(self.client.sync_forever(timeout=30000))

        return True

    async def message_callback(self, room, event):
        """Handle incoming messages"""
        if event.sender == self.username:
            return  # Ignore our own messages

        self.message_log.append({
            "sender": event.sender,
            "body": event.body,
            "timestamp": datetime.now().isoformat()
        })

        # Check for agent announcement
        if "@room:" in event.body:
            try:
                # Parse agent message
                json_str = event.body.replace("@room: ", "")
                agent_msg = json.loads(json_str)

                if agent_msg.get("message_type") == "agent_online":
                    agent_id = agent_msg["content"]["agent_id"]
                    self.discovered_agents[agent_id] = agent_msg["content"]
                    logger.info(f"🤖 Discovered agent: {agent_id} - {agent_msg['content'].get('display_name')}")
                    self.test_results["agent_discovery"] = True

            except json.JSONDecodeError:
                pass

        # Check for LLM responses
        if "@subatomic6140" in event.sender and "👴" in event.body:
            logger.info(f"💬 LLM Response received: {event.body[:100]}...")
            self.test_results["llm_response"] = True

    async def test_agent_discovery(self):
        """Test 1: Check if agents announce themselves"""
        logger.info("\n📋 Test 1: Agent Discovery")
        logger.info("=" * 50)

        # Request agent status
        status_request = {
            "id": f"test_{int(time.time())}",
            "sender": "tester",
            "target": "*",
            "message_type": "discover_agents",
            "content": {},
            "context": {},
            "timestamp": datetime.now().isoformat()
        }

        await self.client.room_send(
            room_id=self.coordination_room,
            message_type="m.room.message",
            content={
                "msgtype": "m.text",
                "body": f"@room: {json.dumps(status_request)}"
            },
            ignore_unverified_devices=True
        )

        # Wait for responses
        await asyncio.sleep(5)

        if self.discovered_agents:
            logger.info(f"✅ Discovered {len(self.discovered_agents)} agents:")
            for agent_id, info in self.discovered_agents.items():
                logger.info(f"   - {info['display_name']} ({agent_id})")
                logger.info(f"     Capabilities: {', '.join(info['capabilities'][:3])}...")
        else:
            logger.warning("❌ No agents discovered")

    async def test_llm_agent(self):
        """Test 2: Direct communication with LLM agent"""
        logger.info("\n📋 Test 2: LLM Agent Communication")
        logger.info("=" * 50)

        # Send a direct message to trigger LLM response
        test_prompts = [
            "Hello Grandpa LLM! Can you tell me a joke?",
            "@subatomic6140 What's the weather like?",
            "!help"
        ]

        for prompt in test_prompts:
            logger.info(f"📤 Sending: {prompt}")
            await self.client.room_send(
                room_id=self.coordination_room,
                message_type="m.room.message",
                content={
                    "msgtype": "m.text",
                    "body": prompt
                },
                ignore_unverified_devices=True
            )
            await asyncio.sleep(3)

        # Check for responses
        await asyncio.sleep(5)

        if self.test_results["llm_response"]:
            logger.info("✅ LLM agent is responding")
        else:
            logger.warning("❌ No LLM responses received")

    async def test_orchestrator_coordination(self):
        """Test 3: Orchestrator coordination capabilities"""
        logger.info("\n📋 Test 3: Orchestrator Coordination")
        logger.info("=" * 50)

        # Send a workflow request
        workflow_request = {
            "id": f"workflow_{int(time.time())}",
            "sender": "tester",
            "target": "orchestrator",
            "message_type": "execute_workflow",
            "content": {
                "workflow": "simple_query",
                "steps": [
                    {
                        "agent": "llm",
                        "action": "generate_text",
                        "params": {
                            "prompt": "What is 2+2?"
                        }
                    }
                ]
            },
            "context": {},
            "timestamp": datetime.now().isoformat()
        }

        logger.info("📤 Sending workflow request to orchestrator...")
        await self.client.room_send(
            room_id=self.coordination_room,
            message_type="m.room.message",
            content={
                "msgtype": "m.text",
                "body": f"@room: {json.dumps(workflow_request)}"
            },
            ignore_unverified_devices=True
        )

        # Wait for orchestrator to process
        await asyncio.sleep(8)

        # Check if orchestrator responded
        orchestrator_responded = any(
            "@unmolded8581" in msg["sender"] or "orchestrator" in msg["body"].lower()
            for msg in self.message_log[-10:]
        )

        if orchestrator_responded:
            logger.info("✅ Orchestrator is coordinating")
            self.test_results["orchestrator_coordination"] = True
        else:
            logger.warning("❌ No orchestrator coordination detected")

    async def test_inter_agent_messaging(self):
        """Test 4: Inter-agent message passing"""
        logger.info("\n📋 Test 4: Inter-Agent Messaging")
        logger.info("=" * 50)

        # Send a message that requires agent cooperation
        cooperation_request = {
            "id": f"coop_{int(time.time())}",
            "sender": "tester",
            "target": "orchestrator",
            "message_type": "multi_agent_task",
            "content": {
                "task": "Generate a summary about AI",
                "agents_required": ["llm"],
                "coordination_needed": True
            },
            "context": {},
            "timestamp": datetime.now().isoformat()
        }

        logger.info("📤 Sending multi-agent task...")
        await self.client.room_send(
            room_id=self.coordination_room,
            message_type="m.room.message",
            content={
                "msgtype": "m.text",
                "body": f"@room: {json.dumps(cooperation_request)}"
            },
            ignore_unverified_devices=True
        )

        # Wait for agents to collaborate
        await asyncio.sleep(10)

        # Check for inter-agent messages
        recent_messages = self.message_log[-20:]
        agent_messages = [
            msg for msg in recent_messages
            if any(agent in msg["sender"] for agent in ["@subatomic6140", "@unmolded8581"])
        ]

        if len(agent_messages) >= 2:
            logger.info(f"✅ Detected {len(agent_messages)} inter-agent messages")
            self.test_results["inter_agent_messaging"] = True
        else:
            logger.warning("❌ Limited inter-agent messaging detected")

    async def run_tests(self):
        """Run all communication tests"""
        logger.info("🚀 Starting Matrix Multi-Agent Communication Tests")
        logger.info("=" * 60)
        logger.info(f"Coordination Room: {self.coordination_room}")
        logger.info(f"Test Client: {self.username}")
        logger.info("=" * 60)

        # Setup test client
        if not await self.setup():
            logger.error("Failed to setup test client")
            return

        # Allow time for initial sync
        await asyncio.sleep(3)

        # Run tests
        await self.test_agent_discovery()
        await self.test_llm_agent()
        await self.test_orchestrator_coordination()
        await self.test_inter_agent_messaging()

        # Generate report
        await self.generate_report()

        # Cleanup
        await self.cleanup()

    async def generate_report(self):
        """Generate test report"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 TEST RESULTS SUMMARY")
        logger.info("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)

        for test_name, passed in self.test_results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"{status} - {test_name.replace('_', ' ').title()}")

        logger.info("-" * 60)
        logger.info(f"Overall: {passed_tests}/{total_tests} tests passed")

        if passed_tests == total_tests:
            logger.info("🎉 All tests passed! Agents are communicating properly.")
        elif passed_tests > 0:
            logger.info("⚠️  Some tests failed. Check agent configurations.")
        else:
            logger.info("❌ All tests failed. Agents may not be running or configured correctly.")

        # Show discovered agents
        if self.discovered_agents:
            logger.info("\n📋 Discovered Agents:")
            for agent_id, info in self.discovered_agents.items():
                logger.info(f"  • {info['display_name']} ({agent_id})")
                logger.info(f"    Status: {info['status']}")
                logger.info(f"    Capabilities: {', '.join(info['capabilities'][:5])}")

        # Show recent message activity
        logger.info(f"\n📨 Message Activity: {len(self.message_log)} messages logged")
        if self.message_log:
            unique_senders = set(msg["sender"] for msg in self.message_log)
            logger.info(f"  Unique senders: {', '.join(unique_senders)}")

    async def cleanup(self):
        """Clean up test client"""
        if self.client:
            await self.client.close()
            logger.info("\n✅ Test client disconnected")

async def main():
    """Main test runner"""
    tester = AgentCommunicationTester()

    try:
        await tester.run_tests()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Tests interrupted by user")
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())

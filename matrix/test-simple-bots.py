#!/usr/bin/env python3
"""
Test script for simple Matrix buddy bots
Verifies that the bot code can be imported and basic functionality works
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Add the bot directory to Python path
bot_dir = Path(__file__).parent / "bot"
sys.path.insert(0, str(bot_dir))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def test_imports():
    """Test that bot modules can be imported"""
    print("🧪 Testing imports...")

    try:
        from agents.simple_orchestrator import SimpleOrchestratorAgent
        print("✅ SimpleOrchestratorAgent imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import SimpleOrchestratorAgent: {e}")
        return False

    try:
        from agents.simple_llm import SimpleLLMAgent
        print("✅ SimpleLLMAgent imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import SimpleLLMAgent: {e}")
        return False

    return True

def test_bot_initialization():
    """Test bot initialization without connecting"""
    print("\n🧪 Testing bot initialization...")

    try:
        from agents.simple_orchestrator import SimpleOrchestratorAgent
        from agents.simple_llm import SimpleLLMAgent

        # Test orchestrator initialization
        orchestrator = SimpleOrchestratorAgent(
            homeserver_url="https://test.example.com",
            username="@test:example.com",
            password="test_password",
            store_path="/tmp/test_store"
        )
        print("✅ Orchestrator initialized successfully")

        # Test LLM agent initialization
        llm_agent = SimpleLLMAgent(
            homeserver_url="https://test.example.com",
            username="@test_llm:example.com",
            password="test_password",
            store_path="/tmp/test_store"
        )
        print("✅ LLM agent initialized successfully")

        return True

    except Exception as e:
        print(f"❌ Failed to initialize bots: {e}")
        return False

def test_environment_setup():
    """Test environment variable requirements"""
    print("\n🧪 Testing environment setup...")

    required_vars = [
        "UNMOLDED_PASSWORD",
        "SUBATOMIC_PASSWORD"
    ]

    optional_vars = [
        "MATRIX_DOMAIN",
        "MATRIX_HOMESERVER_URL"
    ]

    missing_required = []
    missing_optional = []

    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
        else:
            print(f"✅ {var} is set")

    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append(var)
        else:
            print(f"✅ {var} is set")

    if missing_required:
        print(f"❌ Missing required environment variables: {missing_required}")
        print("\nAdd these to your .env file:")
        for var in missing_required:
            print(f"  {var}=your_password_here")
        return False

    if missing_optional:
        print(f"⚠️  Missing optional environment variables: {missing_optional}")
        print("These will use defaults if not set")

    return True

def test_docker_files():
    """Test that Docker files exist"""
    print("\n🧪 Testing Docker setup...")

    bot_dir = Path(__file__).parent / "bot"
    required_files = [
        "Dockerfile.simple-orchestrator",
        "Dockerfile.simple-llm"
    ]

    compose_file = Path(__file__).parent / "simple-bots-compose.yml"

    all_good = True

    for file_name in required_files:
        file_path = bot_dir / file_name
        if file_path.exists():
            print(f"✅ {file_name} exists")
        else:
            print(f"❌ {file_name} missing")
            all_good = False

    if compose_file.exists():
        print("✅ simple-bots-compose.yml exists")
    else:
        print("❌ simple-bots-compose.yml missing")
        all_good = False

    return all_good

def test_network_connectivity():
    """Test basic network connectivity requirements"""
    print("\n🧪 Testing network connectivity...")

    import socket

    # Test if we can resolve the Matrix domain
    try:
        socket.gethostbyname("acebuddy.quest")
        print("✅ Can resolve acebuddy.quest")
    except socket.gaierror:
        print("❌ Cannot resolve acebuddy.quest")
        return False

    return True

def main():
    """Run all tests"""
    print("🤖 Simple Matrix Buddy Bots Test Suite")
    print("======================================")

    tests = [
        ("Import Test", test_imports),
        ("Initialization Test", test_bot_initialization),
        ("Environment Test", test_environment_setup),
        ("Docker Files Test", test_docker_files),
        ("Network Test", test_network_connectivity)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)

        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"💥 {test_name} ERROR: {e}")

    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} tests passed")
    print('='*50)

    if passed == total:
        print("🎉 All tests passed! Bots are ready to deploy.")
        print("\nNext steps:")
        print("1. Add required environment variables to .env")
        print("2. Run: ./matrix/deploy-simple-bots.sh")
        print("3. Test by typing 'das' in your Matrix rooms!")
        return True
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

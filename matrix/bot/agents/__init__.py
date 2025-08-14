#!/usr/bin/env python3
"""
Matrix Bot Agents Package
Provides various specialized bot agents for the Matrix homelab system
"""

__version__ = "1.0.0"
__author__ = "Homelab Bot System"

# Import base classes
from .base_agent import BaseMatrixAgent, AgentMessage, parse_mention, format_agent_response

# Import agent implementations
try:
    from .orchestrator_agent import OrchestratorAgent
except ImportError:
    pass

try:
    from .llm_agent import LLMAgent
except ImportError:
    pass

try:
    from .simple_orchestrator import SimpleOrchestratorAgent
except ImportError:
    pass

try:
    from .simple_llm import SimpleLLMAgent
except ImportError:
    pass

__all__ = [
    'BaseMatrixAgent',
    'AgentMessage',
    'parse_mention',
    'format_agent_response',
    'OrchestratorAgent',
    'LLMAgent',
    'SimpleOrchestratorAgent',
    'SimpleLLMAgent'
]

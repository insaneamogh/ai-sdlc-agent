"""
Agents Package

This package contains the AI agents that perform specific SDLC tasks:
- RequirementAgent: Analyzes and extracts requirements from Jira tickets
- CodeAgent: Generates code based on requirements
- TestAgent: Creates test cases for generated code

Now using STRICT versions with:
- Deterministic outputs (temperature=0)
- Structured validation (Pydantic)
- Fail-fast behavior (no mock fallbacks)
- Prompt logging
"""

# Use STRICT agents by default
from app.agents.requirement_agent_strict import RequirementAgentStrict as RequirementAgent
from app.agents.code_agent_strict import CodeAgentStrict as CodeAgent
from app.agents.test_agent_strict import TestAgentStrict as TestAgent

# Also export strict versions explicitly
from app.agents.requirement_agent_strict import RequirementAgentStrict
from app.agents.code_agent_strict import CodeAgentStrict
from app.agents.test_agent_strict import TestAgentStrict

__all__ = [
    "RequirementAgent", 
    "CodeAgent", 
    "TestAgent",
    "RequirementAgentStrict",
    "CodeAgentStrict", 
    "TestAgentStrict"
]

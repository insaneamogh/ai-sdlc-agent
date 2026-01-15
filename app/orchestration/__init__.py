"""
Orchestration Package

This package contains the workflow orchestration for
coordinating multiple AI agents in the SDLC pipeline.

Now using STRICT version that:
- ACTUALLY fetches GitHub repo content
- Passes real codebase context to agents
- Uses structured data between agents
- Fails fast on errors
"""

# Use STRICT orchestrator by default
from app.orchestration.graph_strict import SDLCOrchestratorStrict as SDLCOrchestrator

# Also export strict version explicitly
from app.orchestration.graph_strict import SDLCOrchestratorStrict

__all__ = ["SDLCOrchestrator", "SDLCOrchestratorStrict"]

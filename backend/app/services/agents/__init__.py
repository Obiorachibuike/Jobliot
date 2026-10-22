"""Multi-agent drafter-reviewer system.

Four distinct agents with separate responsibilities, prompts,
and structured outputs.  A single model may play several roles,
but the stages never collapse into one call.
"""

from app.services.agents.drafter import DrafterAgent
from app.services.agents.orchestrator import ApplicationWorkflow
from app.services.agents.reviewer import ReviewerAgent
from app.services.agents.reviser import ReviserAgent
from app.services.agents.strategist import StrategistAgent

__all__ = [
    "StrategistAgent",
    "DrafterAgent",
    "ReviewerAgent",
    "ReviserAgent",
    "ApplicationWorkflow",
]

"""对弈智能体包。"""

from .base import Agent
from .random_agent import RandomAgent
from .tactical_agent import TacticalAgent

__all__ = ["Agent", "RandomAgent", "TacticalAgent"]

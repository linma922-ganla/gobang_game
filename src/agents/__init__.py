"""对弈智能体包。"""

from .base import Agent
from .random_agent import RandomAgent
from .tactical_agent import TacticalAgent
from .alphabeta_agent import AlphaBetaAgent

__all__ = ["Agent", "RandomAgent", "TacticalAgent", "AlphaBetaAgent"]

"""随机智能体：在所有合法落子中随机选择。

主要用于：
- 环境自测与对局逻辑验证。
- 作为评测竞技场中的最弱基线对手。
"""

from __future__ import annotations

import random
from typing import List

from environment import Game
from .base import Agent


class RandomAgent(Agent):
    """随机落子智能体。"""

    def __init__(self, seed: int = None, name: str = "RandomAgent"):
        super().__init__(name)
        self._rng = random.Random(seed)

    def choose_action(self, game: Game) -> int:
        legal = game.legal_actions()
        if not legal:
            raise ValueError("没有可用的合法落子位置")
        return self._rng.choice(legal)

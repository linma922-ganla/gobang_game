"""Alpha-Beta 搜索智能体。

将 Alpha-Beta 搜索引擎封装为统一的 Agent 接口，供游戏界面、
自动对局和评测竞技场调用。

特点：
- 兼容 Agent 统一接口（choose_action(game) -> int）。
- 支持配置最大深度与时间限制。
- 暴露搜索统计信息（深度、节点数、NPS、用时、最优落子、评分、VCF 结果）。
- 通过复用 Game/Board 复用现有规则，不另起炉灶。
"""

from __future__ import annotations

from typing import Optional

from environment import Game
from engine.alphabeta import AlphaBetaSearch, SearchConfig, SearchStats
from .base import Agent


class AlphaBetaAgent(Agent):
    """基于 Negamax + Alpha-Beta 搜索的对弈智能体。"""

    def __init__(self, config: Optional[SearchConfig] = None,
                 name: str = "AlphaBetaAgent"):
        super().__init__(name)
        self._search = AlphaBetaSearch(config)
        self.last_stats: Optional[SearchStats] = None

    @property
    def config(self) -> SearchConfig:
        return self._search.config

    def choose_action(self, game: Game) -> int:
        """在当前局面执行搜索，返回最优落子的动作索引。"""
        board = game.board
        player = game.current_player
        stats = self._search.search(board, player)
        self.last_stats = stats

        if stats.best_move is None:
            # 兜底：返回第一个合法动作
            legal = game.legal_actions()
            if not legal:
                raise ValueError("没有可用的合法落子位置")
            return legal[0]

        r, c = stats.best_move
        return r * game.size + c

    def reset(self) -> None:
        """新对局开始前清空置换表，避免跨局缓存污染。"""
        self._search.tt.clear()
        self.last_stats = None

    def stats(self) -> Optional[SearchStats]:
        """返回最近一次搜索的统计信息（无则 None）。"""
        return self.last_stats

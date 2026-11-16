"""战术智能体：基于战术搜索 + 传统局面评分的确定性 AI。

落子策略（按优先级）：
1. 己方直接获胜点（立即五连）。
2. 对手直接获胜点（必须防守）。
3. 己方必胜点（活四 / 双冲四 / 冲四+活三）。
4. 必防点（对手存在必胜威胁）。
5. 候选动作中局面评分最高的一手（用 evaluate_board 做 1 层前瞻）。

这是 Alpha-Beta 搜索 Agent 尚未完成前的过渡棋力 Agent，用于人机对战
与后续竞技场评测。
"""

from __future__ import annotations

from typing import List, Tuple

from environment import Game, Board, other, row_col_to_action
from .base import Agent


class TacticalAgent(Agent):
    """基于战术与静态评分的智能体。"""

    def __init__(self, name: str = "TacticalAgent", seed: int = None):
        super().__init__(name)
        self._seed = seed

    def choose_action(self, game: Game) -> int:
        from engine import (
            find_immediate_wins,
            find_opponent_immediate_wins,
            find_winning_moves,
            find_forced_defense_moves,
            candidate_moves,
            evaluate_board,
        )

        board = game.board
        player = game.current_player
        size = game.size

        # 1) 己方直接获胜点
        my_wins = find_immediate_wins(board, player)
        if my_wins:
            return self._pick(my_wins, size)

        # 2) 对手直接获胜点（必须防守）
        opp_wins = find_opponent_immediate_wins(board, player)
        if opp_wins:
            return self._pick(opp_wins, size)

        # 3) 己方必胜点
        my_winning = find_winning_moves(board, player)
        if my_winning:
            return self._pick(my_winning, size)

        # 4) 必防点
        defense = find_forced_defense_moves(board, player)
        if defense:
            return self._pick(defense, size)

        # 5) 候选动作中评分最高的一手
        candidates = candidate_moves(board, player, max_candidates=12)
        if not candidates:
            # 兜底：任意合法位置
            candidates = board.empty_points()

        best = None
        best_score = float("-inf")
        for (r, c) in candidates:
            board.make_move(r, c, player)
            score = evaluate_board(board, player)
            board.undo_move(r, c)
            if score > best_score:
                best_score = score
                best = (r, c)
        if best is None:
            best = candidates[0]
        return row_col_to_action(best[0], best[1], size)

    def _pick(self, moves: List[Tuple[int, int]], size: int) -> int:
        """从关键点列表中选择一个（默认取第一个，后续可加启发式）。"""
        r, c = moves[0]
        return row_col_to_action(r, c, size)

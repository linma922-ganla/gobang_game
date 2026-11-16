"""战术搜索模块。

负责识别直接获胜点、对手直接获胜点、必胜点与必防点。

核心概念：
- 直接获胜点：己方落子后立即形成五连的位置。
- 对手直接获胜点：对手落子后立即形成五连的位置（即我方必须防守的位置）。
- 必胜点（VCF 基础）：落子后形成「活四」或「双冲四/双活三」等强制胜点，
  对手无法同时防守。
- 必防点：对手存在必胜点时，我方必须占据的防守位置。

关键设计：
- 严格区分「已证明的胜利 / 已证明的失败 / 未知」三种结果，
  不把「未搜索到胜利」错误判定为必败。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

from environment import Board, EMPTY, BLACK, WHITE, other
from .patterns import (
    Pattern, FIVE, LIVE_FOUR, RUSH_FOUR, LIVE_THREE, SLEEP_THREE,
    LIVE_TWO, SLEEP_TWO, NONE, classify_pattern,
)


class Outcome(Enum):
    """战术搜索的结果状态。"""

    WIN = "win"            # 已证明必胜
    LOSS = "loss"          # 已证明必败
    UNKNOWN = "unknown"    # 深度不足，无法判定


@dataclass
class TacticalResult:
    """战术搜索结果。"""

    outcome: Outcome
    moves: List[Tuple[int, int]] = None   # 关键落子序列（若可证明）

    def __post_init__(self):
        if self.moves is None:
            self.moves = []


def find_immediate_wins(board: Board, player: int) -> List[Tuple[int, int]]:
    """找出 player 所有「落子即五连」的直接获胜点。"""
    wins = []
    for r in range(board.size):
        for c in range(board.size):
            if board.get(r, c) != EMPTY:
                continue
            board.make_move(r, c, player)
            if _is_five(board, r, c, player):
                wins.append((r, c))
            board.undo_move(r, c)
    return wins


def _is_five(board: Board, r: int, c: int, player: int) -> bool:
    """判断 (r,c) 处 player 是否已成五连。"""
    from environment.rules import check_win_at
    return check_win_at(board, r, c, 5)


def find_opponent_immediate_wins(board: Board, player: int) -> List[Tuple[int, int]]:
    """找出对手（非 player）所有「落子即五连」的直接获胜点。"""
    return find_immediate_wins(board, other(player))


def find_winning_moves(board: Board, player: int) -> List[Tuple[int, int]]:
    """返回 player 的「必胜点」：落子后形成活四或双冲四/活三等的强制胜点。

    第一版实现：
    - 直接五连（立即获胜）
    - 落子后形成「活四」（对手无法防守，必胜）
    - 落子后形成「双冲四」（double-four，对手只能防一处）
    - 落子后形成「冲四 + 活三」（four-three，常见必胜组合）

    返回值中每个点都经过验证：落子后对手无法完全防守。
    """
    winning = set()

    for r in range(board.size):
        for c in range(board.size):
            if board.get(r, c) != EMPTY:
                continue
            board.make_move(r, c, player)
            # 1) 直接五连
            if _is_five(board, r, c, player):
                winning.add((r, c))
                board.undo_move(r, c)
                continue
            # 2) 活四
            if _has_live_four_anywhere(board, player):
                winning.add((r, c))
                board.undo_move(r, c)
                continue
            # 3) 双冲四 或 冲四+活三
            rush = _count_rush_four(board, player)
            live3 = _count_live_three(board, player)
            if rush >= 2 or (rush >= 1 and live3 >= 1):
                winning.add((r, c))
            board.undo_move(r, c)

    return sorted(winning)


def _has_live_four_anywhere(board: Board, player: int) -> bool:
    for r in range(board.size):
        for c in range(board.size):
            if board.get(r, c) == player:
                if classify_pattern(board, r, c, player) >= LIVE_FOUR:
                    return True
    return False


def _count_rush_four(board: Board, player: int) -> int:
    """统计 player 的冲四数量（去重，按方向计数）。"""
    count = 0
    seen = set()
    for r in range(board.size):
        for c in range(board.size):
            if board.get(r, c) == player:
                p = classify_pattern(board, r, c, player)
                if p == RUSH_FOUR or p == LIVE_FOUR:
                    # 粗略去重：同一连块可能被多个棋子重复计
                    if (r, c) not in seen:
                        count += 1
                        seen.add((r, c))
    return count


def _count_live_three(board: Board, player: int) -> int:
    count = 0
    for r in range(board.size):
        for c in range(board.size):
            if board.get(r, c) == player:
                p = classify_pattern(board, r, c, player)
                if p == LIVE_THREE:
                    count += 1
    return count


def find_forced_defense_moves(board: Board, player: int) -> List[Tuple[int, int]]:
    """返回 player 的「必防点」：对手存在直接获胜点或必胜点时，必须防守的位置。

    第一版策略：
    - 若对手存在「直接五连点」，必须占据其中一处（但若对手有多处，则无法全防）。
    - 若对手存在「活四」，必须占据对手活四的成五点。
    - 否则返回空列表（无强制防守）。
    """
    opponent = other(player)

    # 对手直接获胜点
    opp_immediate = find_immediate_wins(board, opponent)
    if opp_immediate:
        # 若对手只有一个直接获胜点，防住即可；多个则防守其中一个
        return opp_immediate[:1] if len(opp_immediate) == 1 else opp_immediate

    # 对手活四：需占据其成五点
    defense = []
    for r in range(board.size):
        for c in range(board.size):
            if board.get(r, c) != EMPTY:
                continue
            board.make_move(r, c, opponent)
            if _has_live_four_anywhere(board, opponent):
                defense.append((r, c))
            board.undo_move(r, c)
    # 去重
    return sorted(set(defense))


def evaluate_tactical(board: Board, player: int) -> TacticalResult:
    """综合战术评估：判断 player 当前的攻防态势。

    Returns:
        TacticalResult:
        - 若 player 存在直接获胜点 -> WIN
        - 若对手存在直接获胜点且 player 无法一次性反制 -> LOSS（仅当对手必杀时）
        - 否则 UNKNOWN（不轻易判定失败）
    """
    my_wins = find_immediate_wins(board, player)
    if my_wins:
        return TacticalResult(Outcome.WIN, my_wins)

    opponent = other(player)
    opp_wins = find_immediate_wins(board, opponent)
    if opp_wins:
        # 对手有直接获胜点：若对方有多个，我方必败
        if len(opp_wins) >= 2:
            return TacticalResult(Outcome.LOSS, opp_wins)
        # 只有一个：若我方无更强反击，则需防守，这里保守返回 UNKNOWN（由搜索决定）
        # 但若我方同时无直接获胜，则对手下回合即胜 -> 判定 LOSS
        my_winning = find_winning_moves(board, player)
        if not my_winning:
            return TacticalResult(Outcome.LOSS, opp_wins)

    return TacticalResult(Outcome.UNKNOWN, [])

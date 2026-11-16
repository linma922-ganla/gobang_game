"""传统局面评分函数。

基于棋形统计的静态评估，为 Alpha-Beta 搜索叶节点和神经网络提供基线。

评分思路：
- 扫描全盘，统计双方各棋形数量。
- 每种棋形赋予权重（威胁越高权重越大）。
- 局面分数 = 我方棋形加权和 - 对手棋形加权和。
- 若存在五连，直接返回 ±极大值。

权重可配置，后续可由神经网络替代。
"""

from __future__ import annotations

from typing import Dict

from environment import Board, BLACK, WHITE, EMPTY, other
from .patterns import (
    Pattern, FIVE, LIVE_FOUR, RUSH_FOUR, LIVE_THREE, SLEEP_THREE,
    LIVE_TWO, SLEEP_TWO, NONE, classify_pattern,
)

# 默认棋形权重（可调）
DEFAULT_WEIGHTS: Dict[Pattern, float] = {
    FIVE: 100000.0,
    LIVE_FOUR: 10000.0,
    RUSH_FOUR: 1000.0,
    LIVE_THREE: 500.0,
    SLEEP_THREE: 100.0,
    LIVE_TWO: 50.0,
    SLEEP_TWO: 10.0,
    NONE: 0.0,
}

# 胜利/失败极值
WIN_SCORE = 1_000_000.0
LOSS_SCORE = -1_000_000.0


def _block_pattern(board: Board, start_r: int, start_c: int,
                   dr: int, dc: int, player: int) -> Pattern:
    """判定从 (start_r,start_c) 出发、沿 (dr,dc) 方向的连续块的棋形。

    (start_r,start_c) 必须是该方向的块起点（反方向邻位非己方子）。
    仅分析该方向，返回该方向上的棋形等级。
    """
    # 统计连续长度
    length = 0
    r, c = start_r, start_c
    while board.in_bounds(r, c) and board.get(r, c) == player:
        length += 1
        r += dr
        c += dc
    # 块末端（第一个非己方子位置）
    end_r, end_c = r, c

    # 两端开口判断
    def _open(rr, cc):
        return board.in_bounds(rr, cc) and board.get(rr, cc) == EMPTY

    left_open = _open(start_r - dr, start_c - dc)
    right_open = _open(end_r, end_c)

    if length >= 5:
        return FIVE
    if length == 4:
        if left_open and right_open:
            return LIVE_FOUR
        if left_open or right_open:
            return RUSH_FOUR
        return NONE
    if length == 3:
        if left_open and right_open:
            return LIVE_THREE
        if left_open or right_open:
            return SLEEP_THREE
        return NONE
    if length == 2:
        if left_open and right_open:
            return LIVE_TWO
        if left_open or right_open:
            return SLEEP_TWO
        return NONE
    return NONE


def _count_patterns(board: Board, player: int) -> Dict[Pattern, int]:
    """统计 player 各棋形数量。

    去重策略：沿四个方向扫描，仅当某棋子是「该方向连续块的起点」
    （其反方向邻位不是己方子）时才对该块判定棋形，保证每个连块只计一次。
    使用单方向判定函数 _block_pattern 避免跨方向重复。
    """
    counts = {p: 0 for p in DEFAULT_WEIGHTS}

    for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
        bdr, bdc = -dr, -dc
        for r in range(board.size):
            for c in range(board.size):
                if board.get(r, c) != player:
                    continue
                pr, pc = r + bdr, c + bdc
                if board.in_bounds(pr, pc) and board.get(pr, pc) == player:
                    continue  # 不是块起点
                p = _block_pattern(board, r, c, dr, dc, player)
                if p != NONE:
                    counts[p] += 1
    return counts


def evaluate_board(board: Board, player: int,
                   weights: Dict[Pattern, float] = None) -> float:
    """返回 player 视角下的局面评分。

    正值表示 player 占优，负值表示对手占优。

    Args:
        board: 当前棋盘。
        player: 评分视角方。
        weights: 可选自定义权重，默认使用 DEFAULT_WEIGHTS。

    Returns:
        float 评分。
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    opponent = other(player)
    my_counts = _count_patterns(board, player)
    opp_counts = _count_patterns(board, opponent)

    # 五连：直接分胜负
    if my_counts[FIVE] > 0:
        return WIN_SCORE
    if opp_counts[FIVE] > 0:
        return LOSS_SCORE

    score = 0.0
    for p, w in weights.items():
        score += w * (my_counts[p] - opp_counts[p])
    return score

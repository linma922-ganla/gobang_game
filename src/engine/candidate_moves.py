"""候选动作筛选模块。

为 Alpha-Beta 搜索提供候选落子点，减少搜索分支：

1. 己方直接获胜点（最高优先级，必须包含）。
2. 对手直接获胜点（必须防守，必须包含）。
3. 己方/对手的「活四、冲四、活三」等关键棋形延伸点。
4. 已有棋子周围的空位（按距离/威胁排序）。
5. 空棋盘时返回中心开局点。

保证：所有直接获胜与强制防守动作一定被保留。
"""

from __future__ import annotations

from typing import List, Tuple

from environment import Board, EMPTY
from .tactical_search import (
    find_immediate_wins,
    find_opponent_immediate_wins,
    find_winning_moves,
    find_forced_defense_moves,
)


def _neighbor_empty(board: Board, radius: int = 2) -> List[Tuple[int, int]]:
    """返回已有棋子周围 radius 范围内的空位（去重）。"""
    result = set()
    occupied = []
    for r in range(board.size):
        for c in range(board.size):
            if board.get(r, c) != EMPTY:
                occupied.append((r, c))

    for (r, c) in occupied:
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                if dr == 0 and dc == 0:
                    continue
                rr, cc = r + dr, c + dc
                if board.in_bounds(rr, cc) and board.get(rr, cc) == EMPTY:
                    result.add((rr, cc))
    return sorted(result)


def center_opening(board: Board) -> List[Tuple[int, int]]:
    """空棋盘的中心开局策略：返回天元及邻近点。"""
    s = board.size
    mid = s // 2
    # 天元优先，其次按到中心距离排序
    points = []
    for r in range(s):
        for c in range(s):
            d = (r - mid) ** 2 + (c - mid) ** 2
            points.append((d, r, c))
    points.sort()
    return [(r, c) for (_, r, c) in points[:5]]


def candidate_moves(board: Board, player: int, max_candidates: int = 12,
                    radius: int = 2) -> List[Tuple[int, int]]:
    """生成候选落子点，保证包含关键攻防点。

    Args:
        board: 当前棋盘。
        player: 当前行动方。
        max_candidates: 最多返回的候选数量。
        radius: 邻居搜索半径。

    Returns:
        候选坐标列表（按优先级排序，去重）。
    """
    ordered: List[Tuple[int, int]] = []
    seen = set()

    def add(pt):
        if pt not in seen:
            seen.add(pt)
            ordered.append(pt)

    # 空棋盘 -> 中心开局
    if not any(board.get(r, c) != EMPTY for r in range(board.size) for c in range(board.size)):
        for pt in center_opening(board):
            add(pt)
        return ordered[:max_candidates]

    # 1) 己方直接获胜点（最高优先级）
    for pt in find_immediate_wins(board, player):
        add(pt)

    # 2) 对手直接获胜点（必须防守）
    for pt in find_opponent_immediate_wins(board, player):
        add(pt)

    # 3) 己方必胜点
    for pt in find_winning_moves(board, player):
        add(pt)

    # 4) 必防点
    for pt in find_forced_defense_moves(board, player):
        add(pt)

    # 5) 邻居空位（补充）
    for pt in _neighbor_empty(board, radius):
        add(pt)

    return ordered[:max_candidates]

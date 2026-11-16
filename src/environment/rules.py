"""五子棋规则判定。

本模块实现胜负判断与合法落子判断，并将规则抽象为可扩展接口，
以便将来增加标准规则、连珠禁手规则。

自由规则：任一方在横、竖、两条对角线上形成五子或以上连续连线即获胜。
"""

from __future__ import annotations

from typing import List, Optional

from .board import Board, EMPTY, Point

# 四个方向：横、竖、主对角、副对角
_DIRECTIONS = ((0, 1), (1, 0), (1, 1), (1, -1))


def check_win_at(board: Board, row: int, col: int, win_length: int = 5) -> bool:
    """判断最近落下的 (row, col) 一子是否形成 win_length 连子。

    仅需检查经过该点的四条线，复杂度 O(win_length)，远优于全盘扫描。
    """
    player = board.get(row, col)
    if player == EMPTY:
        return False

    for dr, dc in _DIRECTIONS:
        count = 1
        # 正方向延伸
        r, c = row + dr, col + dc
        while board.in_bounds(r, c) and board.get(r, c) == player:
            count += 1
            r += dr
            c += dc
        # 反方向延伸
        r, c = row - dr, col - dc
        while board.in_bounds(r, c) and board.get(r, c) == player:
            count += 1
            r -= dr
            c -= dc
        if count >= win_length:
            return True
    return False


def check_win(board: Board, win_length: int = 5) -> int:
    """扫描全盘，返回获胜方颜色（BLACK/WHITE），无人获胜返回 EMPTY。

    该函数用于规则接口与测试；引擎中通常使用增量式的 check_win_at。
    """
    for r in range(board.size):
        for c in range(board.size):
            p = board.get(r, c)
            if p != EMPTY and check_win_at(board, r, c, win_length):
                return p
    return EMPTY


def get_winner(board: Board, last_move: Optional[Point], win_length: int = 5) -> int:
    """返回当前局面获胜方。

    若提供 last_move，则只检查该点，性能更优。
    """
    if last_move is not None:
        r, c = last_move
        if check_win_at(board, r, c, win_length):
            return board.get(r, c)
        return EMPTY
    return check_win(board, win_length)


def get_win_line(board: Board, last_move: Optional[Point],
                 win_length: int = 5) -> List[Point]:
    """返回获胜连线的坐标列表（用于界面高亮）。

    若 last_move 提供，只检查经过该点的四条线；返回第一个构成 win_length
    连线的连续坐标序列。无获胜时返回空列表。
    """
    if last_move is None:
        return []
    row, col = last_move
    player = board.get(row, col)
    if player == EMPTY:
        return []

    for dr, dc in _DIRECTIONS:
        line = [(row, col)]
        # 正方向
        r, c = row + dr, col + dc
        while board.in_bounds(r, c) and board.get(r, c) == player:
            line.append((r, c))
            r += dr
            c += dc
        # 反方向
        r, c = row - dr, col - dc
        while board.in_bounds(r, c) and board.get(r, c) == player:
            line.insert(0, (r, c))
            r -= dr
            c -= dc
        if len(line) >= win_length:
            return line
    return []


class Rules:
    """规则引擎，抽象胜负与合法落子判断，便于扩展禁手规则。

    当前实现自由规则（无禁手）。
    """

    def __init__(self, size: int = 15, win_length: int = 5, forbidden: bool = False):
        self.size = size
        self.win_length = win_length
        self.forbidden = forbidden

    def is_legal(self, board: Board, row: int, col: int) -> bool:
        """判断 (row, col) 是否可落子。

        预留 forbidden 禁手判断接口，当前仅检查越界与占位。
        """
        if not board.in_bounds(row, col):
            return False
        if board.get(row, col) != EMPTY:
            return False
        # 预留：若启用禁手规则，可在此加入 forbidden_move 检测
        return True

    def legal_actions(self, board: Board):
        """返回所有合法落子位置列表。"""
        return [pt for pt in board.empty_points() if self.is_legal(board, *pt)]

    def is_terminal(self, board: Board, last_move: Optional[Point]) -> bool:
        """局面是否结束：有人获胜或棋盘已满。"""
        return get_winner(board, last_move, self.win_length) != EMPTY or board.is_full()

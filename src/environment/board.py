"""五子棋棋盘表示。

使用二维列表（list of list）表示 15×15 棋盘：
- 0 表示空位
- 1 表示黑子（先手）
- -1 表示白子（后手）

棋盘操作保持纯函数风格，便于引擎与训练复用。
"""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

# 棋盘常量
# 采用与导师一致的三值编码：黑 = +1，白 = -1，空 = 0。
# 该编码使得「一行之和」可直接用于胜负判断（如井字棋中 +3 / -3），
# 也便于零和博弈的价值符号转换。
EMPTY = 0
BLACK = 1
WHITE = -1

# 落子方视角下的"我/对手"等价转换
# 用于零和博弈中价值符号转换
OPPONENT = {BLACK: WHITE, WHITE: BLACK}

Point = Tuple[int, int]


class Board:
    """五子棋棋盘。

    Attributes:
        size: 棋盘边长（默认 15）。
        grid: 二维整数列表，grid[row][col] 取值 EMPTY/BLACK/WHITE。
    """

    def __init__(self, size: int = 15, grid: Optional[Sequence[Sequence[int]]] = None):
        self.size = size
        if grid is None:
            self.grid = [[EMPTY] * size for _ in range(size)]
        else:
            # 拷贝输入，避免外部引用
            self.grid = [list(row) for row in grid]

    # ------------------------------------------------------------------
    # 基础查询
    # ------------------------------------------------------------------
    def in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.size and 0 <= col < self.size

    def get(self, row: int, col: int) -> int:
        return self.grid[row][col]

    def is_empty(self, row: int, col: int) -> bool:
        return self.in_bounds(row, col) and self.grid[row][col] == EMPTY

    def empty_points(self) -> List[Point]:
        """返回所有空位坐标列表。"""
        pts: List[Point] = []
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] == EMPTY:
                    pts.append((r, c))
        return pts

    def is_full(self) -> bool:
        return not any(EMPTY in row for row in self.grid)

    # ------------------------------------------------------------------
    # 落子
    # ------------------------------------------------------------------
    def place(self, row: int, col: int, player: int) -> bool:
        """在 (row, col) 落下 player 棋子。

        Returns:
            落子成功返回 True；位置非法或已被占据返回 False。
        """
        return self.make_move(row, col, player)

    def copy(self) -> "Board":
        """返回深拷贝，用于搜索回溯。"""
        return Board(self.size, grid=self.grid)

    # ------------------------------------------------------------------
    # 搜索优化：就地落子 / 撤销
    # ------------------------------------------------------------------
    def make_move(self, row: int, col: int, player: int) -> bool:
        """就地落子（不产生拷贝），供 Alpha-Beta 搜索高效使用。

        Returns:
            落子成功返回 True；否则 False。
        """
        if not self.in_bounds(row, col) or self.grid[row][col] != EMPTY:
            return False
        self.grid[row][col] = player
        return True

    def undo_move(self, row: int, col: int) -> None:
        """撤销 (row, col) 处的落子，将其置回空位。

        调用方需保证该位置确实刚被落下；本方法不校验颜色。
        """
        self.grid[row][col] = EMPTY

    # ------------------------------------------------------------------
    # 序列化 / 比较
    # ------------------------------------------------------------------
    def to_numpy(self):
        """转为 numpy 数组（shape: (size, size)），便于编码与网络输入。"""
        import numpy as np

        return np.asarray(self.grid, dtype=np.int8)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Board):
            return NotImplemented
        return self.size == other.size and self.grid == other.grid

    def __repr__(self) -> str:
        return f"Board(size={self.size})"


def other(player: int) -> int:
    """返回对手棋子颜色。"""
    return OPPONENT[player]


def row_col_to_action(row: int, col: int, size: int = 15) -> int:
    """将 (row, col) 映射为一维动作索引：action = row * size + col。"""
    return row * size + col


def action_to_row_col(action: int, size: int = 15) -> Point:
    """将一维动作索引还原为 (row, col)。"""
    return divmod(action, size)

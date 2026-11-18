"""Zobrist 哈希。

用于五子棋棋盘状态的增量哈希，供置换表（Transposition Table）快速查找。

原理：
- 对每个 (位置, 棋子颜色) 组合预生成一个随机整数，黑棋落子异或黑棋表，
  白棋落子异或白棋表。
- 额外对「当前行动方」异或一个随机数，使「同一棋盘但轮到不同方」哈希不同。
- 落子/撤销通过异或实现 O(1) 增量更新，撤销即再次异或（异或自反）。

哈希表用固定种子生成，保证跨进程、跨机器可复现，便于对局复现与测试。
"""

from __future__ import annotations

import random
from typing import Optional

from environment import Board, EMPTY, BLACK, WHITE

# 固定种子，保证哈希表可复现
_SEED = 20261116
_BITS = 64
_MASK = (1 << _BITS) - 1


class Zobrist:
    """五子棋 Zobrist 哈希器。

    用法::

        z = Zobrist(size=15)
        h = z.compute(board, current_player)      # 全量计算
        h2 = z.update(h, row, col, BLACK)         # 落子增量更新
        h3 = z.update(h2, row, col, BLACK)        # 再次异或 = 撤销
    """

    def __init__(self, size: int = 15, seed: int = _SEED):
        self.size = size
        rng = random.Random(seed)
        # 每个 (位置, 颜色) 一个随机数。颜色用 BLACK=1 / WHITE=-1 索引。
        # 用 dict 以 (row, col, player) 为键，简单清晰。
        self._table: dict = {}
        for r in range(size):
            for c in range(size):
                self._table[(r, c, BLACK)] = rng.getrandbits(_BITS)
                self._table[(r, c, WHITE)] = rng.getrandbits(_BITS)
        # 行动方随机数（黑/白各自一个，落在「轮到谁」时异或对应值）
        self._side_black = rng.getrandbits(_BITS)
        self._side_white = rng.getrandbits(_BITS)

    def compute(self, board: Board, current_player: int) -> int:
        """全量计算给定棋盘与行动方的 Zobrist 哈希。"""
        h = 0
        for r in range(self.size):
            for c in range(self.size):
                v = board.get(r, c)
                if v != EMPTY:
                    h ^= self._table[(r, c, v)]
        return h ^ self._side(current_player)

    def _side(self, player: int) -> int:
        return self._side_black if player == BLACK else self._side_white

    def update(self, h: int, row: int, col: int, player: int) -> int:
        """落子（或撤销）后增量更新哈希。

        由于异或自反，落子和撤销都调用本方法：落子传入 player，
        撤销同样传入 player 再异或一次即可恢复。
        """
        return h ^ self._table[(row, col, player)]

    def toggle_side(self, h: int, player: int) -> int:
        """切换/设置当前行动方的哈希分量（异或对应 side 随机数）。"""
        return h ^ self._side(player)

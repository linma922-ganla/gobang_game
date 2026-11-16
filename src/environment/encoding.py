"""棋盘状态编码。

将棋盘转换为神经网络输入张量。

第一版使用三个通道（3×15×15）：
- 通道 0：当前行动方棋子位置（1 表示有子）
- 通道 1：对手棋子位置
- 通道 2：最近一次落子位置（仅一个位置为 1）

输出为 numpy 数组，shape: (3, size, size)，后续可转为 torch 张量。
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from .board import Board, BLACK, EMPTY, other


def encode_board(board: Board, current_player: int, last_move=None) -> np.ndarray:
    """将棋盘编码为 (3, size, size) 的 numpy 数组。

    Args:
        board: 当前棋盘。
        current_player: 当前行动方（编码视角）。
        last_move: 最近一次落子坐标 (row, col)，可为 None。

    Returns:
        np.ndarray, shape (3, size, size)，dtype float32。
    """
    size = board.size
    channels = np.zeros((3, size, size), dtype=np.float32)

    opponent = other(current_player)
    for r in range(size):
        for c in range(size):
            v = board.get(r, c)
            if v == current_player:
                channels[0, r, c] = 1.0
            elif v == opponent:
                channels[1, r, c] = 1.0

    if last_move is not None:
        r, c = last_move
        if board.in_bounds(r, c):
            channels[2, r, c] = 1.0

    return channels


def encode_board_black_perspective(board: Board, last_move=None) -> np.ndarray:
    """固定以黑方视角编码（黑=通道0，白=通道1）。

    用于以黑方视角统一存储训练数据；价值标签需配合视角符号转换。
    """
    return encode_board(board, BLACK, last_move)

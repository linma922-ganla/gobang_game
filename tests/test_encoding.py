"""状态编码（encoding）单元测试。"""

import numpy as np

from environment import Board, BLACK, WHITE
from environment.encoding import encode_board, encode_board_black_perspective


def test_encode_shape():
    b = Board()
    arr = encode_board(b, BLACK, None)
    assert arr.shape == (3, 15, 15)
    assert arr.dtype == np.float32


def test_encode_current_and_opponent_channels():
    b = Board()
    b.place(0, 0, BLACK)
    b.place(1, 1, WHITE)
    # 黑方视角
    arr = encode_board(b, BLACK, None)
    assert arr[0, 0, 0] == 1.0  # 黑子在通道0（自己）
    assert arr[1, 1, 1] == 1.0  # 白子在通道1（对手）
    # 白方视角应互换
    arr_w = encode_board(b, WHITE, None)
    assert arr_w[0, 1, 1] == 1.0  # 白子(自己)在通道0
    assert arr_w[1, 0, 0] == 1.0  # 黑子(对手)在通道1


def test_encode_last_move_channel():
    b = Board()
    b.place(3, 4, BLACK)
    arr = encode_board(b, BLACK, (3, 4))
    assert arr[2, 3, 4] == 1.0
    assert arr[2].sum() == 1.0  # 仅一个位置为 1


def test_encode_black_perspective():
    b = Board()
    b.place(5, 5, WHITE)
    arr = encode_board_black_perspective(b, None)
    # 白子作为对手应在通道1
    assert arr[1, 5, 5] == 1.0
    assert arr[0, 5, 5] == 0.0

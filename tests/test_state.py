"""状态（State）单元测试。"""

import numpy as np

from environment import Game, State, BLACK, WHITE, EMPTY


def test_state_from_game_snapshot():
    g = Game()
    g.play(7, 7)
    g.play(7, 8)
    s = State.from_game(g)
    assert s.current_player == BLACK
    assert s.last_move == (7, 8)
    assert s.done is False
    assert s.move_history == [7 * 15 + 7, 7 * 15 + 8]
    assert s.board.get(7, 7) == BLACK
    assert s.board.get(7, 8) == WHITE


def test_state_is_independent_snapshot():
    """State 是快照，后续对 Game 的修改不影响已创建的 State。"""
    g = Game()
    g.play(7, 7)
    s = g.get_state()
    g.play(7, 8)  # 继续下
    # 快照里的棋盘不应包含 (7,8)
    assert s.board.get(7, 8) == EMPTY
    assert len(s.move_history) == 1


def test_board_array_shape_and_values():
    g = Game()
    g.play(3, 4)
    s = g.get_state()
    arr = s.board_array()
    assert arr.shape == (15, 15)
    assert arr.dtype == np.int8
    assert arr[3, 4] == BLACK
    assert arr[0, 0] == EMPTY


def test_encode_default_perspective():
    g = Game()
    g.play(0, 0)  # 黑
    g.play(1, 1)  # 白
    s = g.get_state()  # 当前行动方为黑
    enc = s.encode()
    assert enc.shape == (3, 15, 15)
    assert enc.dtype == np.float32
    # 黑方视角：黑子(0,0)在通道0，白子(1,1)在通道1
    assert enc[0, 0, 0] == 1.0
    assert enc[1, 1, 1] == 1.0
    # 最近落子 (1,1) 在通道2
    assert enc[2, 1, 1] == 1.0


def test_encode_explicit_perspective():
    g = Game()
    g.play(0, 0)  # 黑
    g.play(1, 1)  # 白
    s = g.get_state()
    # 以白方视角编码：白子(1,1)在通道0，黑子(0,0)在通道1
    enc_white = s.encode(perspective=WHITE)
    assert enc_white[0, 1, 1] == 1.0
    assert enc_white[1, 0, 0] == 1.0


def test_legal_actions():
    g = Game()
    s = g.get_state()
    assert len(s.legal_actions()) == 225
    g.play(7, 7)
    s2 = g.get_state()
    assert len(s2.legal_actions()) == 224
    assert (7 * 15 + 7) not in s2.legal_actions()


def test_legal_action_mask():
    g = Game()
    g.play(7, 7)
    s = g.get_state()
    mask = s.legal_action_mask()
    assert mask.shape == (225,)
    assert mask.sum() == 224  # 只剩 224 个合法点
    assert mask[7 * 15 + 7] == 0.0  # 已占位为非法
    assert mask[0] == 1.0


def test_opponent_property():
    g = Game()
    s = g.get_state()
    assert s.opponent == WHITE


def test_observation_dict():
    g = Game()
    g.play(7, 7)
    s = g.get_state()
    obs = s.observation()
    assert "board" in obs
    assert "encoded" in obs
    assert "legal_actions" in obs
    assert "legal_action_mask" in obs
    assert obs["current_player"] == WHITE
    assert obs["done"] is False
    assert obs["winner"] == EMPTY


def test_done_state_winner():
    g = Game()
    for c in range(5):
        g.play(0, c)
        if c < 4:
            g.play(1, c)
    s = g.get_state()
    assert s.done is True
    assert s.winner == BLACK


def test_piece_encoding_aligns_with_mentor():
    """棋子编码与导师一致：黑=1，白=-1，空=0。"""
    from environment import Board, BLACK, WHITE, EMPTY
    assert BLACK == 1
    assert WHITE == -1
    assert EMPTY == 0
    b = Board()
    b.place(0, 0, BLACK)
    b.place(1, 1, WHITE)
    arr = b.to_numpy()
    assert arr[0, 0] == 1
    assert arr[1, 1] == -1
    assert arr[2, 2] == 0


def test_hash_key_unique_and_distinguishes_player():
    """hash_key 对齐导师的 tuple 展平思想，且额外区分行动方。"""
    g = Game()
    g.play(7, 7)  # 黑落子
    s1 = g.get_state()
    key1 = s1.hash_key()

    # 同一棋盘，不同行动方 -> 不同 hash_key
    g2 = Game()
    g2.play(7, 7)
    g2.play(7, 8)  # 白落子
    s2 = g2.get_state()
    key2 = s2.hash_key()

    # key1 是黑落子后轮到白；key2 是白落子后轮到黑，棋盘也不同
    assert key1 != key2

    # 展平棋盘 tuple 长度 = size*size
    assert len(key1[0]) == 225
    # 行动方是元组第二个元素
    assert key1[1] == WHITE  # 黑落子后轮到白


def test_hash_key_same_board_same_key():
    """相同棋盘 + 相同行动方 -> 相同 hash_key。"""
    g1 = Game()
    g1.play(7, 7)
    g1.play(7, 8)
    g2 = Game()
    g2.play(7, 7)
    g2.play(7, 8)
    assert g1.get_state().hash_key() == g2.get_state().hash_key()


def test_zobrist_hash_consistent():
    """zobrist_hash 对相同状态返回相同值。"""
    g1 = Game()
    g1.play(7, 7)
    g2 = Game()
    g2.play(7, 7)
    assert g1.get_state().zobrist_hash() == g2.get_state().zobrist_hash()

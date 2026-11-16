"""候选动作筛选与局面评分单元测试。"""

from environment import Board, BLACK, WHITE
from engine import candidate_moves, center_opening, evaluate_board


def _place(board, cells, player):
    for r, c in cells:
        board.place(r, c, player)


# ----------------------------------------------------------------------
# 候选动作
# ----------------------------------------------------------------------
def test_candidate_empty_board_center():
    """空棋盘应返回中心开局点。"""
    b = Board()
    cm = candidate_moves(b, BLACK)
    s = b.size
    mid = s // 2
    assert (mid, mid) in cm  # 天元优先


def test_candidate_preserves_immediate_win():
    """候选必须包含直接获胜点。"""
    b = Board()
    _place(b, [(7, 3), (7, 4), (7, 5), (7, 6)], BLACK)
    cm = candidate_moves(b, BLACK)
    assert (7, 2) in cm
    assert (7, 7) in cm


def test_candidate_preserves_defense():
    """候选必须包含对手直接获胜点（防守）。"""
    b = Board()
    _place(b, [(7, 3), (7, 4), (7, 5), (7, 6)], WHITE)
    cm = candidate_moves(b, BLACK)
    assert (7, 2) in cm
    assert (7, 7) in cm


def test_candidate_near_stones():
    """候选应集中在已有棋子附近。"""
    b = Board()
    b.place(7, 7, BLACK)
    cm = candidate_moves(b, WHITE)
    # 所有候选应离 (7,7) 不远
    for (r, c) in cm:
        assert abs(r - 7) <= 2 and abs(c - 7) <= 2


def test_candidate_unique_and_limited():
    b = Board()
    _place(b, [(7, 5), (7, 6), (7, 7)], BLACK)
    cm = candidate_moves(b, WHITE)
    assert len(cm) == len(set(cm))  # 无重复
    assert len(cm) <= 12


# ----------------------------------------------------------------------
# 中心开局
# ----------------------------------------------------------------------
def test_center_opening_returns_tianyuan():
    b = Board()
    pts = center_opening(b)
    mid = b.size // 2
    assert (mid, mid) in pts
    assert len(pts) == 5


# ----------------------------------------------------------------------
# 局面评分
# ----------------------------------------------------------------------
def test_evaluate_win_positive():
    b = Board()
    _place(b, [(7, 3), (7, 4), (7, 5), (7, 6), (7, 7)], BLACK)
    assert evaluate_board(b, BLACK) >= 1_000_000


def test_evaluate_loss_negative():
    b = Board()
    _place(b, [(7, 3), (7, 4), (7, 5), (7, 6), (7, 7)], WHITE)
    assert evaluate_board(b, BLACK) <= -1_000_000


def test_evaluate_zero_sum():
    """零和：双方视角评分应互为相反数（无五连时）。"""
    b = Board()
    _place(b, [(7, 4), (7, 5), (7, 6)], BLACK)
    _place(b, [(8, 4), (8, 5)], WHITE)
    s_black = evaluate_board(b, BLACK)
    s_white = evaluate_board(b, WHITE)
    assert abs(s_black + s_white) < 1e-6


def test_evaluate_advantage():
    """黑方活三，白方只有活二，黑方应占优。"""
    b = Board()
    _place(b, [(7, 4), (7, 5), (7, 6)], BLACK)  # 活三
    _place(b, [(8, 4), (8, 5)], WHITE)          # 活二
    assert evaluate_board(b, BLACK) > 0


def test_evaluate_empty_board_zero():
    b = Board()
    assert evaluate_board(b, BLACK) == 0.0

"""棋形识别（patterns）单元测试。

覆盖：
- 横、竖、双斜线四个方向
- 棋盘边缘与角落
- 连续棋子与跳跃棋形
- 单端封堵与双端封堵
- 黑棋白棋对称
"""

from environment import Board, BLACK, WHITE
from engine import (
    classify_pattern, find_patterns,
    FIVE, LIVE_FOUR, RUSH_FOUR, LIVE_THREE, SLEEP_THREE, LIVE_TWO, SLEEP_TWO,
)


def _place(board, cells, player):
    for r, c in cells:
        board.place(r, c, player)


def _center_of(board, cells, player):
    """取连块中间那颗子的坐标，用于 classify_pattern。"""
    r0 = sum(r for r, c in cells) / len(cells)
    c0 = sum(c for r, c in cells) / len(cells)
    return int(r0), int(c0)


# ----------------------------------------------------------------------
# 五连
# ----------------------------------------------------------------------
def test_five_horizontal():
    b = Board()
    _place(b, [(7, 3), (7, 4), (7, 5), (7, 6), (7, 7)], BLACK)
    assert classify_pattern(b, 7, 5, BLACK) == FIVE


def test_five_vertical():
    b = Board()
    _place(b, [(3, 7), (4, 7), (5, 7), (6, 7), (7, 7)], WHITE)
    assert classify_pattern(b, 5, 7, WHITE) == FIVE


def test_five_main_diagonal():
    b = Board()
    _place(b, [(3, 3), (4, 4), (5, 5), (6, 6), (7, 7)], BLACK)
    assert classify_pattern(b, 5, 5, BLACK) == FIVE


def test_five_anti_diagonal():
    b = Board()
    _place(b, [(3, 7), (4, 6), (5, 5), (6, 4), (7, 3)], BLACK)
    assert classify_pattern(b, 5, 5, BLACK) == FIVE


def test_five_at_edge():
    """棋盘边缘的五连。"""
    b = Board()
    _place(b, [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)], BLACK)
    assert classify_pattern(b, 0, 2, BLACK) == FIVE


def test_five_at_corner():
    """角落起点的五连。"""
    b = Board()
    _place(b, [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)], WHITE)
    assert classify_pattern(b, 2, 0, WHITE) == FIVE


# ----------------------------------------------------------------------
# 活四
# ----------------------------------------------------------------------
def test_live_four_horizontal():
    """两端都空的四连 = 活四。"""
    b = Board()
    _place(b, [(7, 4), (7, 5), (7, 6), (7, 7)], BLACK)
    assert classify_pattern(b, 7, 5, BLACK) == LIVE_FOUR


def test_live_four_vertical():
    b = Board()
    _place(b, [(4, 7), (5, 7), (6, 7), (7, 7)], WHITE)
    assert classify_pattern(b, 5, 7, WHITE) == LIVE_FOUR


def test_live_four_diagonal():
    b = Board()
    _place(b, [(4, 4), (5, 5), (6, 6), (7, 7)], BLACK)
    assert classify_pattern(b, 5, 5, BLACK) == LIVE_FOUR


def test_live_four_anti_diagonal():
    b = Board()
    _place(b, [(4, 6), (5, 5), (6, 4), (7, 3)], WHITE)
    assert classify_pattern(b, 5, 5, WHITE) == LIVE_FOUR


# ----------------------------------------------------------------------
# 冲四
# ----------------------------------------------------------------------
def test_rush_four_one_end_blocked():
    """一端被白子堵住的四连 = 冲四。"""
    b = Board()
    _place(b, [(7, 4), (7, 5), (7, 6), (7, 7)], BLACK)
    b.place(7, 3, WHITE)  # 左端堵
    assert classify_pattern(b, 7, 5, BLACK) == RUSH_FOUR


def test_rush_four_at_edge():
    """靠边的四连（边界视为堵）= 冲四。"""
    b = Board()
    _place(b, [(0, 0), (0, 1), (0, 2), (0, 3)], BLACK)
    assert classify_pattern(b, 0, 1, BLACK) == RUSH_FOUR


def test_rush_four_vertical_one_end_blocked():
    b = Board()
    _place(b, [(4, 7), (5, 7), (6, 7), (7, 7)], WHITE)
    b.place(3, 7, BLACK)  # 上端堵
    assert classify_pattern(b, 5, 7, WHITE) == RUSH_FOUR


def test_four_both_ends_blocked_is_none():
    """双端堵死的四连无威胁。"""
    b = Board()
    _place(b, [(7, 4), (7, 5), (7, 6), (7, 7)], BLACK)
    b.place(7, 3, WHITE)
    b.place(7, 8, WHITE)
    from engine import NONE
    assert classify_pattern(b, 7, 5, BLACK) == NONE


# ----------------------------------------------------------------------
# 活三
# ----------------------------------------------------------------------
def test_live_three_horizontal():
    b = Board()
    _place(b, [(7, 4), (7, 5), (7, 6)], BLACK)
    assert classify_pattern(b, 7, 5, BLACK) == LIVE_THREE


def test_live_three_vertical():
    b = Board()
    _place(b, [(4, 7), (5, 7), (6, 7)], WHITE)
    assert classify_pattern(b, 5, 7, WHITE) == LIVE_THREE


def test_live_three_diagonal():
    b = Board()
    _place(b, [(4, 4), (5, 5), (6, 6)], BLACK)
    assert classify_pattern(b, 5, 5, BLACK) == LIVE_THREE


# ----------------------------------------------------------------------
# 眠三
# ----------------------------------------------------------------------
def test_sleep_three_one_end_blocked():
    b = Board()
    _place(b, [(7, 4), (7, 5), (7, 6)], BLACK)
    b.place(7, 3, WHITE)
    assert classify_pattern(b, 7, 5, BLACK) == SLEEP_THREE


def test_sleep_three_at_edge():
    b = Board()
    _place(b, [(0, 0), (0, 1), (0, 2)], WHITE)
    assert classify_pattern(b, 0, 1, WHITE) == SLEEP_THREE


# ----------------------------------------------------------------------
# 活二 / 眠二
# ----------------------------------------------------------------------
def test_live_two_horizontal():
    b = Board()
    _place(b, [(7, 5), (7, 6)], BLACK)
    assert classify_pattern(b, 7, 5, BLACK) == LIVE_TWO


def test_sleep_two_one_end_blocked():
    b = Board()
    _place(b, [(7, 5), (7, 6)], WHITE)
    b.place(7, 4, BLACK)
    assert classify_pattern(b, 7, 5, WHITE) == SLEEP_TWO


# ----------------------------------------------------------------------
# 跳跃棋形
# ----------------------------------------------------------------------
def test_jump_rush_four():
    """XX_XX 跳跃冲四。"""
    b = Board()
    _place(b, [(7, 3), (7, 4), (7, 6), (7, 7)], BLACK)
    # 中间 (7,5) 为空，构成跳冲四
    p = classify_pattern(b, 7, 4, BLACK)
    assert p in (RUSH_FOUR, LIVE_FOUR, FIVE)


def test_jump_three():
    """XX_X 跳跃三。"""
    b = Board()
    _place(b, [(7, 3), (7, 4), (7, 6)], BLACK)
    p = classify_pattern(b, 7, 4, BLACK)
    assert p in (SLEEP_THREE, LIVE_THREE, RUSH_FOUR, LIVE_FOUR)


# ----------------------------------------------------------------------
# 黑白对称
# ----------------------------------------------------------------------
def test_black_white_symmetry_live_four():
    b1 = Board()
    _place(b1, [(7, 4), (7, 5), (7, 6), (7, 7)], BLACK)
    b2 = Board()
    _place(b2, [(7, 4), (7, 5), (7, 6), (7, 7)], WHITE)
    assert classify_pattern(b1, 7, 5, BLACK) == classify_pattern(b2, 7, 5, WHITE)


def test_black_white_symmetry_rush_four():
    b1 = Board()
    _place(b1, [(7, 4), (7, 5), (7, 6), (7, 7)], BLACK)
    b1.place(7, 3, WHITE)
    b2 = Board()
    _place(b2, [(7, 4), (7, 5), (7, 6), (7, 7)], WHITE)
    b2.place(7, 3, BLACK)
    assert classify_pattern(b1, 7, 5, BLACK) == classify_pattern(b2, 7, 5, WHITE)


# ----------------------------------------------------------------------
# find_patterns 全盘扫描
# ----------------------------------------------------------------------
def test_find_patterns_detects_live_four():
    b = Board()
    _place(b, [(7, 4), (7, 5), (7, 6), (7, 7)], BLACK)
    patterns = find_patterns(b, BLACK)
    assert len(patterns[LIVE_FOUR]) >= 1


def test_find_patterns_empty_board():
    b = Board()
    patterns = find_patterns(b, BLACK)
    assert patterns[FIVE] == []
    assert patterns[LIVE_FOUR] == []
    assert patterns[LIVE_THREE] == []

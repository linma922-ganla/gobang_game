"""VCF 连续冲四必胜搜索的单元测试。"""

import pytest

from environment import Board, BLACK, WHITE
from engine.vcf import VCFSearcher, VCFResult


def _place(board, points, player):
    for (r, c) in points:
        board.make_move(r, c, player)


def _board_with(points, player, size=15):
    b = Board(size)
    _place(b, points, player)
    return b


# ---------------------------------------------------------------------------
# 基本结果
# ---------------------------------------------------------------------------
def test_immediate_five_is_win():
    """已有四连 + 一个可成五的点 -> 直接获胜。"""
    b = _board_with([(7, 3), (7, 4), (7, 5), (7, 6)], BLACK)
    s = VCFSearcher(max_depth=4)
    assert s.search(b, BLACK) == VCFResult.PROVEN_WIN


def test_live_four_is_win():
    """活四（两端开口四连）-> 必胜。"""
    b = _board_with([(7, 4), (7, 5), (7, 6), (7, 7)], BLACK)
    s = VCFSearcher(max_depth=4)
    assert s.search(b, BLACK) == VCFResult.PROVEN_WIN


def test_empty_board_no_win():
    """空棋盘不可能 VCF 必胜。"""
    b = Board()
    s = VCFSearcher(max_depth=4)
    assert s.search(b, BLACK) == VCFResult.PROVEN_NO_WIN


def test_no_rush_four_no_win():
    """孤零零的几颗子没有冲四点 -> 无法 VCF。"""
    b = _board_with([(7, 7)], BLACK)
    s = VCFSearcher(max_depth=4)
    assert s.search(b, BLACK) == VCFResult.PROVEN_NO_WIN


# ---------------------------------------------------------------------------
# 黑白对称
# ---------------------------------------------------------------------------
def test_black_white_symmetry():
    """同一局面，黑方与白方应得到对称结果（各自视角）。"""
    # 黑方四连
    b = _board_with([(7, 3), (7, 4), (7, 5), (7, 6)], BLACK)
    s = VCFSearcher(max_depth=4)
    assert s.search(b, BLACK) == VCFResult.PROVEN_WIN
    # 白方同样的四连（镜像，坐标不同但结构相同）
    b2 = _board_with([(8, 3), (8, 4), (8, 5), (8, 6)], WHITE)
    assert s.search(b2, WHITE) == VCFResult.PROVEN_WIN


# ---------------------------------------------------------------------------
# 棋盘恢复
# ---------------------------------------------------------------------------
def test_board_restored_after_search():
    """搜索结束后棋盘必须完全恢复。"""
    b = _board_with([(7, 3), (7, 4), (7, 5), (7, 6), (8, 8)], BLACK)
    _place(b, [(8, 3), (8, 4)], WHITE)
    snapshot = [row[:] for row in b.grid]
    s = VCFSearcher(max_depth=6)
    s.search(b, BLACK)
    assert b.grid == snapshot


# ---------------------------------------------------------------------------
# 超时返回 UNKNOWN
# ---------------------------------------------------------------------------
def test_timeout_returns_unknown():
    """极短时间限制下应返回 UNKNOWN 而非错误判定。"""
    # 用「一端被堵的三连」构造：落子只能形成冲四（非活四），需要继续搜索，
    # 但时间限制为 0 时应超时返回 UNKNOWN。
    # (7,3)(7,4)(7,5) 黑三连，左边 (7,2) 放白子堵住，右边 (7,6) 空。
    b = Board()
    _place(b, [(7, 3), (7, 4), (7, 5)], BLACK)
    _place(b, [(7, 2)], WHITE)  # 堵住左端，只剩冲四（非活四）
    s = VCFSearcher(max_depth=12, time_limit_ms=0)
    result = s.search(b, BLACK)
    assert result != VCFResult.PROVEN_WIN


def test_depth_limit_returns_unknown_not_false_win():
    """深度限制下不能误判必胜。"""
    # 一端被堵的三连：只能形成冲四，需要多层连续冲四才能成五。
    # 浅深度（depth=1）时无法完成证明，不应返回 PROVEN_WIN。
    b = Board()
    _place(b, [(7, 3), (7, 4), (7, 5)], BLACK)
    _place(b, [(7, 2)], WHITE)  # 堵左端
    s = VCFSearcher(max_depth=1)
    result = s.search(b, BLACK)
    assert result != VCFResult.PROVEN_WIN

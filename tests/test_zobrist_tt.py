"""Zobrist 哈希与置换表的单元测试。"""

import pytest

from environment import Board, BLACK, WHITE
from engine.zobrist import Zobrist
from engine.transposition_table import TranspositionTable, NodeType, TTEntry


# ---------------------------------------------------------------------------
# Zobrist
# ---------------------------------------------------------------------------
def test_same_position_same_hash():
    z = Zobrist()
    b1 = Board()
    b2 = Board()
    b1.make_move(7, 7, BLACK)
    b2.make_move(7, 7, BLACK)
    assert z.compute(b1, BLACK) == z.compute(b2, BLACK)


def test_different_side_different_hash():
    z = Zobrist()
    b = Board()
    b.make_move(7, 7, BLACK)
    assert z.compute(b, BLACK) != z.compute(b, WHITE)


def test_incremental_matches_full_recompute():
    """落子后的增量哈希必须与全量重算一致。

    增量流程：每次落子后，行动方也切换。因此需：
    1. 撤销旧 side 分量（toggle_side）
    2. 异或新落子（update）
    3. 异或新 side 分量（toggle_side）
    """
    z = Zobrist()
    b = Board()
    h = z.compute(b, BLACK)          # 初始：黑方行动
    cur = BLACK
    moves = [(7, 7, BLACK), (7, 8, WHITE), (8, 8, BLACK), (6, 6, WHITE)]
    for r, c, p in moves:
        b.make_move(r, c, p)
        h = z.toggle_side(h, cur)     # 撤销旧行动方分量
        h = z.update(h, r, c, p)      # 落子
        cur = WHITE if cur == BLACK else BLACK
        h = z.toggle_side(h, cur)     # 加入新行动方分量
    assert h == z.compute(b, cur)    # 全量重算应一致
    assert h == z.compute(b, BLACK)  # 4 手后轮到黑方（黑/白/黑/白 落子，白下完轮到黑）


def test_undo_restores_hash():
    """撤销落子后哈希应恢复。"""
    z = Zobrist()
    b = Board()
    h0 = z.compute(b, BLACK)
    b.make_move(7, 7, BLACK)
    # 落子：撤旧side + 落子 + 加新side
    h1 = z.toggle_side(h0, BLACK)
    h1 = z.update(h1, 7, 7, BLACK)
    h1 = z.toggle_side(h1, WHITE)
    assert h1 == z.compute(b, WHITE)
    # 撤销：撤新side + 撤子 + 加旧side
    b.undo_move(7, 7)
    h2 = z.toggle_side(h1, WHITE)
    h2 = z.update(h2, 7, 7, BLACK)
    h2 = z.toggle_side(h2, BLACK)
    assert h2 == h0
    assert h2 == z.compute(b, BLACK)


def test_order_independent_hash():
    """哈希只取决于最终局面，不取决于落子顺序（同色集合相同则哈希同）。"""
    z = Zobrist()
    b1 = Board()
    for (r, c) in [(0, 0), (1, 1), (2, 2)]:
        b1.make_move(r, c, BLACK)
    b2 = Board()
    for (r, c) in [(2, 2), (0, 0), (1, 1)]:
        b2.make_move(r, c, BLACK)
    assert z.compute(b1, BLACK) == z.compute(b2, BLACK)


def test_deterministic_across_instances():
    """不同 Zobrist 实例（同 seed）产生相同哈希。"""
    b = Board()
    b.make_move(3, 4, WHITE)
    assert Zobrist().compute(b, WHITE) == Zobrist().compute(b, WHITE)


# ---------------------------------------------------------------------------
# TranspositionTable
# ---------------------------------------------------------------------------
def test_store_and_probe():
    tt = TranspositionTable()
    tt.store(key=123, depth=3, score=100.0, node_type=NodeType.EXACT,
             best_move=(7, 7))
    e = tt.probe(123)
    assert e is not None
    assert e.score == 100.0
    assert e.node_type == NodeType.EXACT
    assert e.best_move == (7, 7)


def test_deeper_entry_not_overwritten():
    tt = TranspositionTable()
    tt.store(key=1, depth=5, score=50.0, node_type=NodeType.EXACT)
    tt.store(key=1, depth=3, score=10.0, node_type=NodeType.EXACT)
    assert tt.probe(1).depth == 5
    assert tt.probe(1).score == 50.0


def test_shallower_entry_overwritten_by_deeper():
    tt = TranspositionTable()
    tt.store(key=1, depth=3, score=10.0, node_type=NodeType.EXACT)
    tt.store(key=1, depth=6, score=60.0, node_type=NodeType.EXACT)
    assert tt.probe(1).depth == 6
    assert tt.probe(1).score == 60.0


def test_bound_types_preserved():
    tt = TranspositionTable()
    tt.store(key=1, depth=3, score=0.5, node_type=NodeType.LOWER_BOUND)
    tt.store(key=2, depth=3, score=-0.5, node_type=NodeType.UPPER_BOUND)
    assert tt.probe(1).node_type == NodeType.LOWER_BOUND
    assert tt.probe(2).node_type == NodeType.UPPER_BOUND


def test_miss_returns_none():
    tt = TranspositionTable()
    assert tt.probe(999) is None


def test_hit_counter():
    tt = TranspositionTable()
    tt.store(key=5, depth=1, score=0.0, node_type=NodeType.EXACT)
    tt.probe(5)
    tt.probe(5)
    tt.probe(6)
    assert tt.hits == 2
    assert tt.probes == 3

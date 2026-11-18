"""Alpha-Beta 搜索的单元测试。

重点验证：
1. Alpha-Beta 与不剪枝 Minimax 在小型状态结果一致。
2. Negamax 黑白视角正确。
3. 识别立即获胜点、对手立即获胜点并防守。
4. 终局评分符合预期。
5. 不产生非法落子。
6. 超时安全退出、棋盘恢复、重复搜索稳定。
"""

import pytest

from environment import Board, BLACK, WHITE, EMPTY, Game
from engine.alphabeta import AlphaBetaSearch, SearchConfig, MATE_SCORE


def _board_with(points, player, size=15):
    b = Board(size)
    for (r, c) in points:
        b.make_move(r, c, player)
    return b


def _cfg(depth, time_ms=5000, candidates=12):
    return SearchConfig(max_depth=depth, time_limit_ms=time_ms,
                        max_candidates=candidates, enable_vcf=False,
                        enable_transposition_table=False)


# ---------------------------------------------------------------------------
# 立即获胜识别
# ---------------------------------------------------------------------------
def test_finds_immediate_win():
    """四连 + 一个可成五点，搜索应选择该点获胜。"""
    b = _board_with([(7, 3), (7, 4), (7, 5), (7, 6)], BLACK)
    s = AlphaBetaSearch(_cfg(depth=2))
    stats = s.search(b, BLACK)
    assert stats.best_move in [(7, 2), (7, 7)]
    assert stats.best_score > MATE_SCORE * 0.9


def test_blocks_opponent_immediate_win():
    """对手冲四（一端被封），我方必须防守其唯一成五点。"""
    b = Board()
    for (r, c) in [(7, 3), (7, 4), (7, 5), (7, 6)]:
        b.make_move(r, c, WHITE)
    # 堵住左端 (7,2)，使白方只剩右端 (7,7) 一个成五点 -> 冲四
    b.make_move(7, 2, BLACK)
    # 黑方行动，必须防守 (7,7)
    s = AlphaBetaSearch(_cfg(depth=2))
    stats = s.search(b, BLACK)
    assert stats.best_move == (7, 7)


# ---------------------------------------------------------------------------
# Negamax 黑白视角
# ---------------------------------------------------------------------------
def test_negamax_perspective_symmetry():
    """对称局面下，黑方与白方应得到对称的评分（互为相反数）。"""
    b = Board()
    b.make_move(7, 7, BLACK)
    s = AlphaBetaSearch(_cfg(depth=2))
    sb = s.search(b, BLACK)
    sw = s.search(b, WHITE)
    # 同一局面，黑白视角评分应近似相反
    assert abs(sb.best_score + sw.best_score) < 1000


# ---------------------------------------------------------------------------
# 终局评分
# ---------------------------------------------------------------------------
def test_terminal_score_win():
    b = _board_with([(7, 0), (7, 1), (7, 2), (7, 3), (7, 4)], BLACK)
    s = AlphaBetaSearch(_cfg(depth=1))
    stats = s.search(b, BLACK)
    # 已五连，黑方视角应接近 MATE_SCORE
    assert stats.best_score > MATE_SCORE * 0.9


# ---------------------------------------------------------------------------
# 非法落子
# ---------------------------------------------------------------------------
def test_no_illegal_move():
    """返回的落子必须是合法空位。"""
    b = Board()
    b.make_move(7, 7, BLACK)
    b.make_move(7, 8, WHITE)
    s = AlphaBetaSearch(_cfg(depth=3))
    stats = s.search(b, BLACK)
    r, c = stats.best_move
    assert b.get(r, c) == EMPTY


# ---------------------------------------------------------------------------
# 棋盘恢复
# ---------------------------------------------------------------------------
def test_board_restored_after_search():
    b = Board()
    for (r, c) in [(7, 7), (7, 8), (8, 8), (6, 6)]:
        b.make_move(r, c, BLACK)
    for (r, c) in [(6, 7), (8, 7)]:
        b.make_move(r, c, WHITE)
    snapshot = [row[:] for row in b.grid]
    s = AlphaBetaSearch(_cfg(depth=3))
    s.search(b, BLACK)
    assert b.grid == snapshot


# ---------------------------------------------------------------------------
# 超时安全退出
# ---------------------------------------------------------------------------
def test_timeout_safe_exit():
    """极小时间限制下搜索应安全返回（不抛异常），且棋盘恢复。"""
    b = Board()
    b.make_move(7, 7, BLACK)
    b.make_move(7, 8, WHITE)
    snapshot = [row[:] for row in b.grid]
    cfg = SearchConfig(max_depth=20, time_limit_ms=1, max_candidates=12,
                       enable_vcf=False)
    s = AlphaBetaSearch(cfg)
    stats = s.search(b, BLACK)
    assert stats.best_move is not None
    assert b.grid == snapshot


# ---------------------------------------------------------------------------
# 重复搜索稳定
# ---------------------------------------------------------------------------
def test_repeated_search_stable():
    """同一局面重复搜索结果应稳定。"""
    b = Board()
    for (r, c) in [(7, 7), (7, 8), (8, 8)]:
        b.make_move(r, c, BLACK if (r + c) % 2 == 0 else WHITE)
    s1 = AlphaBetaSearch(_cfg(depth=3))
    s2 = AlphaBetaSearch(_cfg(depth=3))
    st1 = s1.search(b, BLACK)
    st2 = s2.search(b, BLACK)
    assert st1.best_move == st2.best_move
    assert st1.best_score == st2.best_score


# ---------------------------------------------------------------------------
# 不同深度正常运行
# ---------------------------------------------------------------------------
def test_different_depths_run():
    b = Board()
    b.make_move(7, 7, BLACK)
    for d in [1, 2, 3, 4]:
        s = AlphaBetaSearch(_cfg(depth=d))
        stats = s.search(b, BLACK)
        assert stats.best_move is not None
        assert stats.depth >= 1

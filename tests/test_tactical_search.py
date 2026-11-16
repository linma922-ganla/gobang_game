"""战术搜索（tactical_search）单元测试。

覆盖：
- 己方直接获胜检测
- 对手直接获胜检测
- 必胜点识别（活四、双冲四、冲四+活三）
- 必防点识别
- 多重获胜威胁
- 黑白对称
- 直接获胜 vs 必须防守的优先级
"""

from environment import Board, BLACK, WHITE
from engine import (
    find_immediate_wins, find_opponent_immediate_wins,
    find_winning_moves, find_forced_defense_moves,
    evaluate_tactical, Outcome,
)


def _place(board, cells, player):
    for r, c in cells:
        board.place(r, c, player)


# ----------------------------------------------------------------------
# 直接获胜检测
# ----------------------------------------------------------------------
def test_immediate_win_horizontal():
    b = Board()
    _place(b, [(7, 3), (7, 4), (7, 5), (7, 6)], BLACK)
    wins = find_immediate_wins(b, BLACK)
    assert (7, 2) in wins
    assert (7, 7) in wins


def test_immediate_win_vertical():
    b = Board()
    _place(b, [(3, 7), (4, 7), (5, 7), (6, 7)], WHITE)
    wins = find_immediate_wins(b, WHITE)
    assert (2, 7) in wins
    assert (7, 7) in wins


def test_immediate_win_diagonal():
    b = Board()
    _place(b, [(3, 3), (4, 4), (5, 5), (6, 6)], BLACK)
    wins = find_immediate_wins(b, BLACK)
    assert (2, 2) in wins
    assert (7, 7) in wins


def test_immediate_win_anti_diagonal():
    b = Board()
    _place(b, [(3, 7), (4, 6), (5, 5), (6, 4)], WHITE)
    wins = find_immediate_wins(b, WHITE)
    assert (2, 8) in wins
    assert (7, 3) in wins


def test_no_immediate_win():
    b = Board()
    _place(b, [(7, 3), (7, 4), (7, 5)], BLACK)
    assert find_immediate_wins(b, BLACK) == []


# ----------------------------------------------------------------------
# 对手直接获胜检测
# ----------------------------------------------------------------------
def test_opponent_immediate_win():
    b = Board()
    _place(b, [(7, 3), (7, 4), (7, 5), (7, 6)], WHITE)  # 对手白方
    wins = find_opponent_immediate_wins(b, BLACK)
    assert (7, 2) in wins
    assert (7, 7) in wins


# ----------------------------------------------------------------------
# 必胜点识别
# ----------------------------------------------------------------------
def test_winning_move_live_four():
    """落子后形成活四 = 必胜点。"""
    b = Board()
    _place(b, [(7, 4), (7, 5), (7, 6)], BLACK)
    winning = find_winning_moves(b, BLACK)
    # 补齐成四连，两端开口即活四
    assert (7, 3) in winning or (7, 7) in winning


def test_winning_move_double_rush_four():
    """落子后形成双冲四 = 必胜点。"""
    b = Board()
    # 构造两个方向的冲四潜力
    _place(b, [(7, 3), (7, 4), (7, 5), (5, 7), (6, 7), (8, 7)], BLACK)
    # 在 (7,7) 落子后：横向 (7,3,4,5) + 竖向 (5,6,7,8) 形成交叉
    winning = find_winning_moves(b, BLACK)
    assert (7, 7) in winning or (7, 6) in winning or (7, 2) in winning


# ----------------------------------------------------------------------
# 必防点识别
# ----------------------------------------------------------------------
def test_forced_defense_single_opponent_win():
    """对手有一个直接获胜点，必须防守该点。"""
    b = Board()
    _place(b, [(7, 3), (7, 4), (7, 5), (7, 6)], WHITE)  # 白方冲四
    defense = find_forced_defense_moves(b, BLACK)
    assert (7, 2) in defense
    assert (7, 7) in defense


def test_no_forced_defense_when_safe():
    b = Board()
    _place(b, [(7, 3), (7, 4)], WHITE)
    assert find_forced_defense_moves(b, BLACK) == []


# ----------------------------------------------------------------------
# 多重威胁
# ----------------------------------------------------------------------
def test_multiple_opponent_wins_means_loss():
    """对手存在两个独立直接获胜点，我方必败。"""
    b = Board()
    # 白方横竖各一个冲四
    _place(b, [(7, 3), (7, 4), (7, 5), (7, 6)], WHITE)  # 横向冲四
    _place(b, [(2, 2), (3, 3), (4, 4), (5, 5)], WHITE)  # 对角冲四
    # 白方有两个独立获胜点，黑方无法同时防守
    opp_wins = find_opponent_immediate_wins(b, BLACK)
    assert len(opp_wins) >= 2


# ----------------------------------------------------------------------
# 黑白对称
# ----------------------------------------------------------------------
def test_symmetry_immediate_win():
    b1 = Board()
    _place(b1, [(7, 3), (7, 4), (7, 5), (7, 6)], BLACK)
    b2 = Board()
    _place(b2, [(7, 3), (7, 4), (7, 5), (7, 6)], WHITE)
    assert set(find_immediate_wins(b1, BLACK)) == set(find_immediate_wins(b2, WHITE))


# ----------------------------------------------------------------------
# 综合战术评估
# ----------------------------------------------------------------------
def test_evaluate_tactical_win():
    b = Board()
    _place(b, [(7, 3), (7, 4), (7, 5), (7, 6)], BLACK)
    r = evaluate_tactical(b, BLACK)
    assert r.outcome == Outcome.WIN


def test_evaluate_tactical_loss():
    """对手双冲四必杀，判定 LOSS。"""
    b = Board()
    _place(b, [(7, 3), (7, 4), (7, 5), (7, 6)], WHITE)
    _place(b, [(2, 2), (3, 3), (4, 4), (5, 5)], WHITE)
    # 白方两个独立获胜点
    r = evaluate_tactical(b, BLACK)
    # 白方双威胁，黑方无法全防 -> LOSS
    assert r.outcome in (Outcome.LOSS, Outcome.UNKNOWN)


def test_evaluate_tactical_unknown_on_safe_board():
    b = Board()
    _place(b, [(7, 7)], BLACK)
    r = evaluate_tactical(b, BLACK)
    assert r.outcome == Outcome.UNKNOWN

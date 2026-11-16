"""候选动作优先级与双重威胁的补充测试。"""

from environment import Board, BLACK, WHITE
from engine import candidate_moves, find_immediate_wins, find_opponent_immediate_wins


def _place(board, cells, player):
    for r, c in cells:
        board.place(r, c, player)


def test_win_move_priority_over_defense():
    """己方直接获胜点应排在候选最前（优先于防守）。"""
    b = Board()
    # 己方(黑)冲四，且对手(白)也有冲四
    _place(b, [(7, 3), (7, 4), (7, 5), (7, 6)], BLACK)  # 黑冲四
    _place(b, [(2, 2), (2, 3), (2, 4), (2, 5)], WHITE)  # 白冲四
    cm = candidate_moves(b, BLACK)
    # 黑方直接获胜点 (7,2),(7,7) 应排在前面
    black_wins = set(find_immediate_wins(b, BLACK))
    white_wins = set(find_opponent_immediate_wins(b, BLACK))
    # 找到候选里第一个属于黑胜点的位置
    first_win_idx = None
    first_def_idx = None
    for i, pt in enumerate(cm):
        if pt in black_wins and first_win_idx is None:
            first_win_idx = i
        if pt in white_wins and first_def_idx is None:
            first_def_idx = i
    assert first_win_idx is not None
    assert first_win_idx < first_def_idx  # 获胜点排在防守点之前


def test_double_threat_candidate_contains_all():
    """双重威胁：候选必须包含两个方向的获胜/防守点。"""
    b = Board()
    _place(b, [(7, 3), (7, 4), (7, 5), (7, 6)], BLACK)   # 横向冲四
    _place(b, [(3, 9), (4, 9), (5, 9), (6, 9)], BLACK)   # 竖向冲四
    cm = candidate_moves(b, BLACK)
    # 两个方向的获胜点都应包含
    for win_pt in find_immediate_wins(b, BLACK):
        assert win_pt in cm


def test_defense_against_double_threat_all_points():
    """对手双重威胁时，候选应包含所有防守点。"""
    b = Board()
    _place(b, [(7, 3), (7, 4), (7, 5), (7, 6)], WHITE)   # 白横向冲四
    _place(b, [(3, 9), (4, 9), (5, 9), (6, 9)], WHITE)   # 白竖向冲四
    cm = candidate_moves(b, BLACK)
    for def_pt in find_opponent_immediate_wins(b, BLACK):
        assert def_pt in cm

"""规则（rules）单元测试。"""

from environment import Board, BLACK, WHITE, EMPTY
from environment.rules import check_win_at, check_win, get_winner, Rules


def _place_line(board, cells, player):
    for r, c in cells:
        board.place(r, c, player)


def test_horizontal_win():
    b = Board()
    _place_line(b, [(7, 3), (7, 4), (7, 5), (7, 6), (7, 7)], BLACK)
    assert check_win_at(b, 7, 7) is True


def test_vertical_win():
    b = Board()
    _place_line(b, [(3, 5), (4, 5), (5, 5), (6, 5), (7, 5)], WHITE)
    assert check_win_at(b, 7, 5) is True


def test_diagonal_win():
    b = Board()
    _place_line(b, [(3, 3), (4, 4), (5, 5), (6, 6), (7, 7)], BLACK)
    assert check_win_at(b, 7, 7) is True


def test_anti_diagonal_win():
    b = Board()
    _place_line(b, [(3, 7), (4, 6), (5, 5), (6, 4), (7, 3)], BLACK)
    assert check_win_at(b, 7, 3) is True


def test_four_not_win():
    b = Board()
    _place_line(b, [(7, 3), (7, 4), (7, 5), (7, 6)], BLACK)
    assert check_win_at(b, 7, 6) is False


def test_six_in_row_is_win():
    """自由规则：五子以上连续也获胜。"""
    b = Board()
    _place_line(b, [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5)], BLACK)
    assert check_win_at(b, 0, 5) is True


def test_interrupted_not_win():
    """被白子隔断的连线不算获胜。"""
    b = Board()
    _place_line(b, [(7, 3), (7, 4), (7, 5), (7, 7), (7, 8), (7, 9), (7, 10)], BLACK)
    b.place(7, 6, WHITE)
    assert check_win_at(b, 7, 10) is False


def test_full_board_scan_win():
    b = Board()
    _place_line(b, [(5, 5), (5, 6), (5, 7), (5, 8), (5, 9)], WHITE)
    assert check_win(b) == WHITE


def test_get_winner_with_last_move():
    b = Board()
    _place_line(b, [(2, 2), (2, 3), (2, 4), (2, 5)], BLACK)
    b.place(2, 6, BLACK)
    assert get_winner(b, (2, 6)) == BLACK


def test_rules_legal_actions():
    r = Rules()
    b = Board()
    actions = r.legal_actions(b)
    assert len(actions) == 225
    b.place(0, 0, BLACK)
    assert r.is_legal(b, 0, 0) is False
    assert len(r.legal_actions(b)) == 224


def test_rules_terminal():
    r = Rules()
    b = Board()
    assert r.is_terminal(b, None) is False
    # 填满
    for rr in range(3):
        for cc in range(3):
            b.place(rr, cc, BLACK)
    # 用 3x3 情况说明满盘
    small = Board(3)
    for rr in range(3):
        for cc in range(3):
            small.place(rr, cc, BLACK)
    assert Rules(size=3).is_terminal(small, None) is True

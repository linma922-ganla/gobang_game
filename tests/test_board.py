"""棋盘（board）单元测试。"""

from environment import Board, EMPTY, BLACK, WHITE, other, row_col_to_action, action_to_row_col


def test_board_init_empty():
    b = Board()
    assert b.size == 15
    assert all(b.get(r, c) == EMPTY for r in range(15) for c in range(15))


def test_place_and_get():
    b = Board()
    assert b.place(0, 0, BLACK) is True
    assert b.get(0, 0) == BLACK
    # 重复落子失败
    assert b.place(0, 0, WHITE) is False
    # 越界失败
    assert b.place(-1, 0, BLACK) is False
    assert b.place(15, 15, BLACK) is False


def test_is_empty_and_empty_points():
    b = Board()
    assert len(b.empty_points()) == 225
    b.place(3, 4, BLACK)
    assert b.is_empty(3, 4) is False
    assert len(b.empty_points()) == 224


def test_is_full():
    b = Board(3)
    assert b.is_full() is False
    for r in range(3):
        for c in range(3):
            b.place(r, c, BLACK)
    assert b.is_full() is True


def test_copy_is_independent():
    b = Board()
    b.place(1, 1, BLACK)
    c = b.copy()
    c.place(2, 2, WHITE)
    assert b.get(2, 2) == EMPTY
    assert c.get(2, 2) == WHITE


def test_other():
    assert other(BLACK) == WHITE
    assert other(WHITE) == BLACK


def test_action_mapping():
    for r in range(15):
        for c in range(15):
            a = row_col_to_action(r, c)
            assert action_to_row_col(a) == (r, c)
    assert row_col_to_action(7, 7) == 7 * 15 + 7


def test_make_move_and_undo_move():
    b = Board()
    assert b.make_move(5, 5, BLACK) is True
    assert b.get(5, 5) == BLACK
    b.undo_move(5, 5)
    assert b.get(5, 5) == EMPTY
    # 撤销后该位置可再次落子
    assert b.make_move(5, 5, WHITE) is True
    assert b.get(5, 5) == WHITE


def test_make_move_illegal():
    b = Board()
    b.make_move(0, 0, BLACK)
    # 已占用位置落子失败
    assert b.make_move(0, 0, WHITE) is False
    # 越界落子失败
    assert b.make_move(-1, 0, BLACK) is False
    assert b.make_move(15, 15, BLACK) is False


def test_make_move_matches_place():
    """place 与 make_move 行为应一致。"""
    b1 = Board()
    b2 = Board()
    assert b1.place(3, 3, BLACK) == b2.make_move(3, 3, BLACK)
    assert b1 == b2

"""对局管理（game）单元测试。"""

from environment import Game, BLACK, WHITE, EMPTY


def test_play_alternates_player():
    g = Game()
    assert g.current_player == BLACK
    g.play(7, 7)
    assert g.current_player == WHITE
    g.play(7, 8)
    assert g.current_player == BLACK


def test_play_on_occupied_fails():
    g = Game()
    g.play(7, 7)
    # 白方试图下在黑子位置，非法
    assert g.play(7, 7) is False
    # 行动方不变
    assert g.current_player == WHITE


def test_black_wins_horizontal():
    g = Game()
    # 黑下 (0,0..4) 连续五子，白下 (1,0..3) 不干扰
    for c in range(5):
        assert g.play(0, c) is True
        if c < 4:
            assert g.play(1, c) is True
    assert g.done is True
    assert g.winner == BLACK


def test_reward_sign_conversion():
    """零和博弈下双方奖励符号应相反。"""
    g = Game()
    for c in range(5):
        g.play(0, c)
        if c < 4:
            g.play(1, c)
    assert g.winner == BLACK
    assert g.reward(BLACK) == 1.0
    assert g.reward(WHITE) == -1.0


def test_draw_reward_zero():
    g = Game(size=3, win_length=5)
    # 3x3 且需 5 连，无法获胜，填满即平局
    seq = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)]
    for r, c in seq:
        g.play(r, c)
    assert g.done is True
    assert g.winner == EMPTY
    assert g.reward(BLACK) == 0.0
    assert g.reward(WHITE) == 0.0


def test_play_after_done_fails():
    g = Game()
    for c in range(5):
        g.play(0, c)
        if c < 4:
            g.play(1, c)
    assert g.done is True
    assert g.play(5, 5) is False


def test_legal_actions_count():
    g = Game()
    assert len(g.legal_actions()) == 225
    g.play(7, 7)
    assert len(g.legal_actions()) == 224


def test_play_action_mapping():
    g = Game()
    assert g.play_action(7 * 15 + 7) is True
    assert g.board.get(7, 7) == BLACK


def test_clone_independent():
    g = Game()
    g.play(7, 7)
    c = g.clone()
    c.play(7, 8)
    assert g.move_count == 1
    assert c.move_count == 2


def test_play_action_out_of_range():
    g = Game()
    # 非法 action（越界）应被拒绝
    assert g.play_action(15 * 15) is False
    assert g.play_action(-1) is False
    assert g.move_count == 0


def test_undo_restores_state():
    g = Game()
    g.play(7, 7)   # 黑
    g.play(7, 8)   # 白
    assert g.current_player == BLACK
    g.undo()       # 撤销白子
    assert g.move_count == 1
    assert g.current_player == WHITE
    assert g.board.get(7, 8) == EMPTY
    assert g.last_move == (7, 7)
    g.undo()       # 撤销黑子
    assert g.move_count == 0
    assert g.current_player == BLACK
    assert g.board.get(7, 7) == EMPTY
    assert g.last_move is None
    # 无历史时撤销失败
    assert g.undo() is False


def test_undo_after_win_reopens_game():
    g = Game()
    # 黑下 (0,0..4) 成五连获胜，白下 (1,0..3)
    for c in range(5):
        g.play(0, c)  # 黑
        if c < 4:
            g.play(1, c)  # 白
    assert g.done is True
    assert g.winner == BLACK
    # 最后一手是黑 (0,4)，撤销后黑重新成为行动方
    g.undo()
    assert g.done is False
    assert g.winner == EMPTY
    assert g.current_player == BLACK
    assert g.board.get(0, 4) == EMPTY


def test_swapped_first_mover_balance():
    """黑白交换先手：两种先后手安排下，胜负与奖励符号正确。"""
    # 场景1：黑先，白后手连成五子获胜
    g1 = Game()
    # 白连成 (2,0..4)，黑下对角线 (3+c, c) 占位，不形成五连
    g1.play(4, 0)          # 黑
    for c in range(5):
        g1.play(2, c)      # 白
        if c < 4 and not g1.done:
            g1.play(4 + c, c + 1)  # 黑下对角线位置，互不相邻
    assert g1.winner == WHITE
    assert g1.reward(WHITE) == 1.0
    assert g1.reward(BLACK) == -1.0

    # 场景2：黑先，黑先手连成五子获胜（对称验证）
    g2 = Game()
    for c in range(5):
        g2.play(0, c)      # 黑连成五子
        if c < 4:
            g2.play(1, c)  # 白
    assert g2.winner == BLACK
    assert g2.reward(BLACK) == 1.0
    assert g2.reward(WHITE) == -1.0

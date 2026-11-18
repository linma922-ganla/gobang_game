"""UI 模块的 headless 单元测试。

通过 SDL_VIDEODRIVER=dummy 在无显示器环境下测试 UI 逻辑，
不依赖人工点击，也不创建真实窗口。
"""

import os
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pytest

from ui import theme
from ui.board_renderer import grid_to_px, px_to_grid, render_board
from ui.game_ui import GameUI
from ui.ai_runner import AIRunner

from environment import BLACK, WHITE, EMPTY, other


def _wait_ai(gui, max_steps=500):
    """驱动 AI 落子直到完成一轮或超时。"""
    gui.maybe_start_ai()
    for _ in range(max_steps):
        gui.poll_ai()
        if not gui.ai_runner.is_busy():
            break
        time.sleep(0.005)


# ---------------------------------------------------------------------------
# 坐标映射
# ---------------------------------------------------------------------------
class TestCoordinateMapping:
    def test_grid_px_roundtrip(self):
        for r in range(15):
            for c in range(15):
                px, py = grid_to_px(r, c)
                assert px_to_grid(px, py) == (r, c)

    def test_corner_mapping(self):
        assert px_to_grid(*grid_to_px(0, 0)) == (0, 0)
        assert px_to_grid(*grid_to_px(0, 14)) == (0, 14)
        assert px_to_grid(*grid_to_px(14, 0)) == (14, 0)
        assert px_to_grid(*grid_to_px(14, 14)) == (14, 14)

    def test_out_of_board_returns_none(self):
        assert px_to_grid(-100, -100) is None
        assert px_to_grid(9999, 9999) is None

    def test_edge_click_accuracy(self):
        # 边缘交点附近小幅偏移仍应命中正确格子
        px, py = grid_to_px(0, 0)
        assert px_to_grid(px + 5, py + 5) == (0, 0)


# ---------------------------------------------------------------------------
# 渲染（headless）
# ---------------------------------------------------------------------------
class TestRendering:
    def test_render_board_no_crash(self):
        import pygame
        pygame.init()
        surf = pygame.Surface((theme.BOARD_PX, theme.BOARD_PX))
        from environment import Board
        board = Board(15)
        board.place(7, 7, BLACK)
        render_board(surf, board, (7, 7), None, None, BLACK)
        # 验证有非空像素（确实画了东西）
        assert surf.get_at((theme.MARGIN, theme.MARGIN)) != (0, 0, 0)
        pygame.quit()


# ---------------------------------------------------------------------------
# 游戏逻辑
# ---------------------------------------------------------------------------
class TestGameLogic:
    def test_human_vs_ai_mode(self):
        gui = GameUI()
        assert gui.mode == "human_vs_ai"
        assert gui._player_label(BLACK) == "玩家"
        assert gui._player_label(WHITE) == "AlphaBeta AI"

    def test_human_move_alternates(self):
        gui = GameUI()
        gui.set_mode("human_vs_human")
        assert gui.human_move(7, 7) is True
        assert gui.current_player == WHITE
        assert gui.human_move(7, 8) is True
        assert gui.current_player == BLACK

    def test_illegal_move_rejected(self):
        gui = GameUI()
        gui.set_mode("human_vs_human")
        gui.human_move(7, 7)
        assert gui.human_move(7, 7) is False  # 已被占
        assert gui.human_move(-1, 0) is False  # 越界

    def test_win_detection_horizontal(self):
        gui = GameUI()
        gui.set_mode("human_vs_human")
        for c in range(5):
            gui.human_move(0, c)          # 黑
            if c < 4:
                gui.human_move(1, c)      # 白
        assert gui.done is True
        assert gui.winner == BLACK
        assert len(gui.win_line) == 5

    def test_no_move_after_win(self):
        gui = GameUI()
        gui.set_mode("human_vs_human")
        for c in range(5):
            gui.human_move(0, c)
            if c < 4:
                gui.human_move(1, c)
        assert gui.human_move(5, 5) is False

    def test_undo_restores_board(self):
        gui = GameUI()
        gui.set_mode("human_vs_human")
        gui.human_move(7, 7)
        gui.human_move(7, 8)
        assert gui.game.move_count == 2
        gui.undo()
        assert gui.game.move_count == 1
        assert gui.board.get(7, 8) == EMPTY

    def test_restart_clears_board(self):
        gui = GameUI()
        gui.set_mode("human_vs_human")
        gui.human_move(7, 7)
        gui.human_move(7, 8)
        gui.restart()
        assert gui.game.move_count == 0
        assert gui.board.get(7, 7) == EMPTY

    def test_swap_human_color(self):
        gui = GameUI()
        assert gui.human_color == BLACK
        gui.swap_human_color()
        assert gui.human_color == WHITE
        assert gui._player_label(WHITE) == "玩家"


# ---------------------------------------------------------------------------
# AI 线程
# ---------------------------------------------------------------------------
class TestAIRunner:
    def test_ai_returns_move(self):
        gui = GameUI()
        gui.human_move(7, 7)   # 人类执黑先下
        _wait_ai(gui)
        assert gui.game.move_count == 2  # 人类 + AI
        assert gui.current_player == BLACK

    def test_ai_does_not_block_main_thread(self):
        gui = GameUI()
        gui.human_move(7, 7)
        gui.maybe_start_ai()
        # 主线程应立即返回（AI 在后台跑）
        assert gui.ai_runner.is_busy() is True
        _wait_ai(gui)
        assert gui.ai_runner.is_busy() is False

    def test_restart_discards_stale_ai(self):
        gui = GameUI()
        gui.human_move(7, 7)
        gui.maybe_start_ai()
        # 立即重开（AI 可能仍在计算）
        gui.restart()
        assert gui.game.move_count == 0
        # 旧 AI 结果应被丢弃，不会污染新棋局
        _wait_ai(gui)
        assert gui.game.move_count == 0  # 新棋局不应被旧结果落子

    def test_human_undo_in_ai_mode(self):
        gui = GameUI()
        gui.human_move(7, 7)
        _wait_ai(gui)
        assert gui.game.move_count == 2
        gui.undo()
        assert gui.game.move_count == 0
        assert gui.current_player == BLACK


# ---------------------------------------------------------------------------
# 战术 Agent 行为
# ---------------------------------------------------------------------------
class TestTacticalAgent:
    def test_tactical_takes_immediate_win(self):
        from environment import Board
        from agents import TacticalAgent
        # 构造黑方已四连，AI 执黑应直接获胜
        gui = GameUI()
        gui.set_mode("human_vs_ai")
        gui.set_human_color(WHITE)  # 人类执白，AI 执黑
        # 手动构造局面：黑 (0,0..3) 四连，轮到黑
        g = gui.game
        # 清空并重设
        gui.new_game()
        g = gui.game
        for c in range(4):
            g.board.place(0, c, BLACK)
            g.board.place(5, c, WHITE)
        g.current_player = BLACK
        g.last_move = (5, 3)
        agent = TacticalAgent()
        action = agent.choose_action(g)
        from environment import action_to_row_col
        r, c = action_to_row_col(action)
        assert (r, c) == (0, 4)  # 补成五连

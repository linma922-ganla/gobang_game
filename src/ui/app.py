"""Pygame 应用入口与主循环。

职责：
- 初始化 Pygame、创建窗口。
- 主循环：事件处理 -> 更新 AI -> 绘制。
- 把鼠标事件分发给棋盘落子与侧边栏按钮。
"""

from __future__ import annotations

import sys
from typing import Optional

import pygame

from . import theme
from .board_renderer import render_board, px_to_grid
from .sidebar import Sidebar
from .game_ui import GameUI


class App:
    """五子棋应用。"""

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.game_ui = GameUI(theme.BOARD_SIZE)
        self.hover: Optional[tuple] = None
        self.running = False

        if not headless:
            pygame.init()
            pygame.display.set_caption("五子棋 Gomoku AI Agent")
            w = theme.BOARD_PX + theme.PANEL_WIDTH
            h = theme.WINDOW_HEIGHT
            self.screen = pygame.display.set_mode((w, h))
            self.clock = pygame.time.Clock()
            self.sidebar = Sidebar(theme.BOARD_PX, theme.PANEL_WIDTH)
            self.sidebar.layout({
                "new": self._on_new,
                "restart": self._on_restart,
                "undo": self._on_undo,
                "swap": self._on_swap,
            })
        else:
            self.screen = None
            self.sidebar = None

    # ------------------------------------------------------------------
    # 按钮回调
    # ------------------------------------------------------------------
    def _on_new(self):
        self.game_ui.new_game()

    def _on_restart(self):
        self.game_ui.restart()

    def _on_undo(self):
        self.game_ui.undo()

    def _on_swap(self):
        self.game_ui.swap_human_color()

    # ------------------------------------------------------------------
    # 事件
    # ------------------------------------------------------------------
    def handle_click(self, pos) -> None:
        """处理鼠标点击。"""
        if self.sidebar is not None and pos[0] >= theme.BOARD_PX:
            self.sidebar.handle_click(pos)
            return
        cell = px_to_grid(pos[0], pos[1])
        if cell is not None:
            self.game_ui.human_move(*cell)

    def handle_mouse_move(self, pos) -> None:
        if self.sidebar is not None:
            self.sidebar.handle_hover(pos)
        if pos[0] < theme.BOARD_PX:
            self.hover = px_to_grid(pos[0], pos[1])
        else:
            self.hover = None

    def _process_events(self) -> bool:
        """处理事件队列，返回是否继续运行。"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_click(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                self.handle_mouse_move(event.pos)
        return True

    # ------------------------------------------------------------------
    # 更新 / 绘制
    # ------------------------------------------------------------------
    def update(self) -> None:
        """推进游戏逻辑（AI 调度与结果落子）。"""
        self.game_ui.maybe_start_ai()
        self.game_ui.poll_ai()

    def draw(self) -> None:
        if self.headless:
            return
        self.screen.fill(theme.WOOD_EDGE)
        gui = self.game_ui
        render_board(
            self.screen, gui.board, gui.last_move, gui.win_line,
            self.hover, gui.current_player,
        )
        self.sidebar.draw(self.screen, gui.get_info())
        pygame.display.flip()

    # ------------------------------------------------------------------
    # 主循环
    # ------------------------------------------------------------------
    def run(self) -> None:
        if self.headless:
            raise RuntimeError("headless 模式不支持 run()")
        self.running = True
        while self.running:
            self.running = self._process_events()
            self.update()
            self.draw()
            self.clock.tick(60)
        pygame.quit()


def main() -> int:
    """命令行入口。"""
    app = App()
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())

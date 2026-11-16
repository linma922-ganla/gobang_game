"""自动对局的图形化查看器。

用 Pygame 实时渲染「两个 Agent 自动对弈」的过程，避免只有终端文字输出
的「黑盒子」问题。

- 每步落子之间有可调节的间隔，便于观察。
- 显示当前行动方、步数、双方 Agent 名称。
- 对局结束后显示结果，按任意键或关闭窗口结束。
- 支持逐步（按空格/点击前进）与自动播放两种模式。

复用 board_renderer 绘制棋盘，不重新实现棋盘逻辑。
"""

from __future__ import annotations

import time
from typing import Optional

import pygame

from environment import Game, BLACK, WHITE, EMPTY
from agents import Agent
from . import theme
from .board_renderer import render_board
from .sidebar import _load_cjk_font
from .game_ui import GameUI  # 复用 get_win_line 相关逻辑不直接依赖，仅用其类型提示


class AutoViewer:
    """自动对局可视化查看器。"""

    def __init__(self, black: Agent, white: Agent, delay: float = 0.5,
                 auto_play: bool = True):
        self.black = black
        self.white = white
        self.delay = delay
        self.auto_play = auto_play
        self.game = Game()
        self.running = False
        self.paused = False
        self._last_step_time = 0.0

        pygame.init()
        pygame.display.set_caption(f"五子棋自动对局 - {black.name} vs {white.name}")
        w = theme.BOARD_PX + theme.PANEL_WIDTH
        h = theme.WINDOW_HEIGHT
        self.screen = pygame.display.set_mode((w, h))
        self.clock = pygame.time.Clock()

    # ------------------------------------------------------------------
    # 对局推进
    # ------------------------------------------------------------------
    def _current_agent(self) -> Agent:
        return self.black if self.game.current_player == BLACK else self.white

    def step(self) -> bool:
        """推进一手，返回是否真的落了子。"""
        if self.game.done:
            return False
        agent = self._current_agent()
        action = agent.choose_action(self.game)
        self.game.play_action(action)
        return True

    # ------------------------------------------------------------------
    # 事件
    # ------------------------------------------------------------------
    def _process_events(self) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    return False
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_RETURN or event.key == pygame.K_RIGHT:
                    if self.paused:
                        self.step()
                elif event.key == pygame.K_p:
                    self.auto_play = not self.auto_play
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.paused:
                    self.step()
        return True

    # ------------------------------------------------------------------
    # 绘制
    # ------------------------------------------------------------------
    def _draw(self) -> None:
        self.screen.fill(theme.WOOD_EDGE)
        win_line = []
        if self.game.done and self.game.winner != EMPTY:
            from environment import get_win_line
            win_line = get_win_line(self.game.board, self.game.last_move,
                                    self.game.win_length)
        render_board(
            self.screen, self.game.board, self.game.last_move, win_line,
            None, self.game.current_player,
        )
        self._draw_panel(win_line)
        pygame.display.flip()

    def _draw_panel(self, win_line) -> None:
        x = theme.BOARD_PX
        w = theme.PANEL_WIDTH
        pygame.draw.rect(self.screen, theme.PANEL_BG, (x, 0, w, self.screen.get_height()))

        f_title = _load_cjk_font(22)
        f_body = _load_cjk_font(17)
        f_small = _load_cjk_font(14)

        def text(s, y, font, color=theme.TEXT_PRIMARY):
            self.screen.blit(font.render(s, True, color), (x + 16, y))

        text("自动对局", 16, f_title)
        text(f"黑方：{self.black.name}", 52, f_body)
        text(f"白方：{self.white.name}", 78, f_body)

        if self.game.done:
            if self.game.winner == BLACK:
                status, color = f"结果：黑胜（{self.black.name}）", theme.WIN_COLOR
            elif self.game.winner == WHITE:
                status, color = f"结果：白胜（{self.white.name}）", theme.WIN_COLOR
            else:
                status, color = "结果：平局", theme.DRAW_COLOR
        else:
            status = f"当前：{'黑方' if self.game.current_player == BLACK else '白方'}"
            color = theme.TEXT_ACCENT
        text(status, 110, f_body, color)

        text(f"步数：{self.game.move_count}", 140, f_body)
        if self.game.last_move:
            r, c = self.game.last_move
            text(f"最近落子：({r + 1},{c + 1})", 166, f_small, theme.TEXT_SECONDARY)

        # 操作提示
        y = 220
        text("操作：", y, f_body)
        y += 28
        text("空格  暂停/继续", y, f_small, theme.TEXT_SECONDARY)
        text("P     自动/手动", y + 22, f_small, theme.TEXT_SECONDARY)
        text("回车/点击  下一步(暂停时)", y + 44, f_small, theme.TEXT_SECONDARY)
        text("Esc/Q  退出", y + 66, f_small, theme.TEXT_SECONDARY)

        # 状态标记
        if self.paused:
            text("【已暂停】", y + 100, f_body, theme.WIN_COLOR)
        elif not self.auto_play:
            text("【手动模式】", y + 100, f_body, theme.TEXT_ACCENT)

    # ------------------------------------------------------------------
    # 主循环
    # ------------------------------------------------------------------
    def run(self) -> Game:
        self.running = True
        self._last_step_time = time.time()
        while self.running:
            self.running = self._process_events()

            # 自动推进
            if self.auto_play and not self.paused and not self.game.done:
                now = time.time()
                if now - self._last_step_time >= self.delay:
                    self.step()
                    self._last_step_time = now

            self._draw()
            self.clock.tick(60)

        pygame.quit()
        return self.game


def view_auto_game(black: Agent, white: Agent, delay: float = 0.5,
                   auto_play: bool = True) -> Game:
    """启动图形化查看器，运行一局自动对弈并返回结果。"""
    viewer = AutoViewer(black, white, delay=delay, auto_play=auto_play)
    return viewer.run()

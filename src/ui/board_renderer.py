"""棋盘与棋子渲染。

负责：
- 绘制木质棋盘背景、网格线、星位。
- 绘制黑白棋子（带高光立体效果）。
- 最近落子红圈高亮、悬停预落子提示、获胜连线高亮。
- 屏幕坐标 <-> 棋盘坐标 的双向映射（含边缘正确性）。

该模块只做「绘制」，不持有对局状态；需要绘制什么由调用方传入。
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import pygame

from . import theme


def _init_fonts() -> None:
    """确保 pygame 字体模块已初始化。"""
    if not pygame.font.get_init():
        pygame.font.init()


def grid_to_px(row: int, col: int) -> Tuple[int, int]:
    """棋盘坐标 -> 屏幕像素（交点）。"""
    x = theme.MARGIN + col * theme.CELL_SIZE
    y = theme.MARGIN + row * theme.CELL_SIZE
    return x, y


def px_to_grid(px: int, py: int) -> Optional[Tuple[int, int]]:
    """屏幕像素 -> 最近棋盘坐标；点击偏离过远返回 None。"""
    col = round((px - theme.MARGIN) / theme.CELL_SIZE)
    row = round((py - theme.MARGIN) / theme.CELL_SIZE)
    if 0 <= row < theme.BOARD_SIZE and 0 <= col < theme.BOARD_SIZE:
        # 校验距离：最近交点不能太远，避免棋盘空隙处误判
        cx, cy = grid_to_px(row, col)
        if (px - cx) ** 2 + (py - cy) ** 2 <= (theme.CELL_SIZE * 0.6) ** 2:
            return row, col
    return None


def draw_board(surface: pygame.Surface, offset: Tuple[int, int] = (0, 0)) -> None:
    """绘制棋盘底（木纹背景 + 网格线 + 星位）。"""
    ox, oy = offset
    n = theme.BOARD_SIZE
    cs = theme.CELL_SIZE
    m = theme.MARGIN
    total = m * 2 + cs * (n - 1)

    # 木质背景
    pygame.draw.rect(surface, theme.WOOD_LIGHT, (ox, oy, total, total))
    # 边框
    pygame.draw.rect(surface, theme.WOOD_EDGE, (ox, oy, total, total), 3)

    # 网格线
    for i in range(n):
        # 横线
        pygame.draw.line(
            surface, theme.GRID_LINE,
            (ox + m, oy + m + i * cs),
            (ox + m + cs * (n - 1), oy + m + i * cs), 1,
        )
        # 竖线
        pygame.draw.line(
            surface, theme.GRID_LINE,
            (ox + m + i * cs, oy + m),
            (ox + m + i * cs, oy + m + cs * (n - 1)), 1,
        )

    # 星位
    for (r, c) in theme.STAR_POINTS:
        x, y = grid_to_px(r, c)
        pygame.draw.circle(surface, theme.STAR_MARK, (ox + x, oy + y), 4)


def draw_stone(surface: pygame.Surface, row: int, col: int, player: int,
               offset: Tuple[int, int] = (0, 0)) -> None:
    """绘制一枚棋子（带立体高光）。player: BLACK(1)/WHITE(-1)。"""
    ox, oy = offset
    x, y = grid_to_px(row, col)
    x += ox
    y += oy
    r = int(theme.CELL_SIZE * 0.44)

    if player == 1:  # 黑
        base = theme.BLACK_STONE
        hi = theme.BLACK_STONE_HI
    else:            # 白
        base = theme.WHITE_STONE
        hi = theme.WHITE_STONE_HI

    # 阴影
    pygame.draw.circle(surface, (0, 0, 0), (x + 2, y + 3), r)
    # 主体
    pygame.draw.circle(surface, base, (x, y), r)
    # 高光
    pygame.draw.circle(surface, hi, (x - r // 3, y - r // 3), max(2, r // 3))


def draw_last_move_ring(surface: pygame.Surface, row: int, col: int,
                        offset: Tuple[int, int] = (0, 0)) -> None:
    """最近落子红圈高亮。"""
    ox, oy = offset
    x, y = grid_to_px(row, col)
    pygame.draw.circle(surface, theme.LAST_MOVE_RING, (x + ox, y + oy),
                       int(theme.CELL_SIZE * 0.18), 2)


def draw_hover_ghost(surface: pygame.Surface, row: int, col: int, player: int,
                     offset: Tuple[int, int] = (0, 0)) -> None:
    """鼠标悬停预落子提示（半透明）。"""
    ox, oy = offset
    x, y = grid_to_px(row, col)
    x += ox
    y += oy
    r = int(theme.CELL_SIZE * 0.44)
    ghost = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
    color = (30, 30, 30, 90) if player == 1 else (245, 245, 245, 110)
    pygame.draw.circle(ghost, color, (r, r), r)
    surface.blit(ghost, (x - r, y - r))


def draw_win_line(surface: pygame.Surface, line: List[Tuple[int, int]],
                  offset: Tuple[int, int] = (0, 0)) -> None:
    """高亮获胜连线（在连线上画金色粗线/圆点）。"""
    if not line:
        return
    ox, oy = offset
    pts = [grid_to_px(r, c) for (r, c) in line]
    pts = [(x + ox, y + oy) for (x, y) in pts]
    for (x, y) in pts:
        pygame.draw.circle(surface, theme.WIN_LINE, (x, y),
                           int(theme.CELL_SIZE * 0.18))
    if len(pts) >= 2:
        pygame.draw.lines(surface, theme.WIN_LINE, False, pts, 4)


def render_board(surface: pygame.Surface, board, last_move: Optional[Tuple[int, int]],
                 win_line: Optional[List[Tuple[int, int]]],
                 hover: Optional[Tuple[int, int]],
                 current_player: int,
                 offset: Tuple[int, int] = (0, 0)) -> None:
    """渲染完整棋盘（底 + 全部棋子 + 各种高亮）。

    Args:
        board: environment.Board 对象（提供 size 与 get(row,col)）。
        last_move: 最近落子 (row,col) 或 None。
        win_line: 获胜连线坐标列表或 None。
        hover: 鼠标悬停的合法落子 (row,col) 或 None。
        current_player: 当前行动方（用于悬停棋子颜色）。
        offset: 棋盘左上角相对 surface 的偏移。
    """
    draw_board(surface, offset)
    n = board.size
    for r in range(n):
        for c in range(n):
            v = board.get(r, c)
            if v != 0:
                draw_stone(surface, r, c, v, offset)

    if win_line:
        draw_win_line(surface, win_line, offset)
    elif last_move is not None:
        draw_last_move_ring(surface, last_move[0], last_move[1], offset)

    if hover is not None and last_move != hover:
        draw_hover_ghost(surface, hover[0], hover[1], current_player, offset)

"""侧边栏（信息面板 + 游戏控制按钮）。

展示玩家信息、对局状态、AI 信息，并提供按钮交互。
按钮通过回调触发，不直接操作游戏逻辑，保持 UI 与逻辑解耦。
"""

from __future__ import annotations

import os
from typing import Callable, List, Optional, Tuple

import pygame

from . import theme


def _load_cjk_font(size: int) -> pygame.font.Font:
    """加载支持中文的字体。

    1) 优先直接加载系统字体文件绝对路径（最可靠）。
    2) 其次用 SysFont 名称匹配。
    3) 最后回退 pygame 默认字体。
    """
    # 1) 直接加载字体文件
    for path in theme.CJK_FONT_FILES:
        try:
            if os.path.exists(path):
                return pygame.font.Font(path, size)
        except Exception:
            continue
    # 2) SysFont 名称匹配
    for name in theme.CJK_FONT_CANDIDATES:
        try:
            font = pygame.font.SysFont(name, size)
            probe = font.render("黑", True, (255, 255, 255))
            if probe.get_width() > 4:
                return font
        except Exception:
            continue
    # 3) 回退默认字体（中文会乱码，但不崩溃）
    return pygame.font.Font(None, size)


class Button:
    """可点击按钮。"""

    def __init__(self, label: str, rect: Tuple[int, int, int, int],
                 callback: Optional[Callable[[], None]] = None):
        self.label = label
        self.rect = rect
        self.callback = callback
        self.hovered = False
        self.active = False

    def contains(self, pos) -> bool:
        x, y, w, h = self.rect
        return x <= pos[0] <= x + w and y <= pos[1] <= y + h

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        x, y, w, h = self.rect
        if self.active:
            bg = theme.BTN_ACTIVE
        elif self.hovered:
            bg = theme.BTN_HOVER
        else:
            bg = theme.BTN_BG
        pygame.draw.rect(surface, bg, (x, y, w, h), border_radius=6)
        pygame.draw.rect(surface, theme.PANEL_BORDER, (x, y, w, h), 1, border_radius=6)
        txt = font.render(self.label, True, theme.BTN_TEXT)
        surface.blit(txt, (x + (w - txt.get_width()) // 2,
                           y + (h - txt.get_height()) // 2))


class Sidebar:
    """右侧信息面板。"""

    def __init__(self, panel_x: int, width: int):
        self.x = panel_x
        self.width = width
        self.buttons: List[Button] = []
        self._font_cache = {}

    # ------------------------------------------------------------------
    # 字体
    # ------------------------------------------------------------------
    def _font(self, size: int) -> pygame.font.Font:
        if size not in self._font_cache:
            self._font_cache[size] = _load_cjk_font(size)
        return self._font_cache[size]

    # ------------------------------------------------------------------
    # 布局
    # ------------------------------------------------------------------
    def _build_buttons(self, y_start: int, callbacks: dict) -> int:
        """创建按钮，返回下一个可用的 y。callbacks 键：new/restart/undo/swap。"""
        self.buttons = []
        pad = 12
        gap = 10
        btn_h = 34
        x = self.x + pad
        w = self.width - pad * 2

        rows = [
            ("新对局", callbacks.get("new")),
            ("重新开始", callbacks.get("restart")),
            ("悔棋", callbacks.get("undo")),
            ("交换先手", callbacks.get("swap")),
        ]
        y = y_start
        for label, cb in rows:
            self.buttons.append(Button(label, (x, y, w, btn_h), cb))
            y += btn_h + gap
        return y

    def layout(self, callbacks: dict, y_start: int = 210) -> None:
        self._build_buttons(y_start, callbacks)

    # ------------------------------------------------------------------
    # 绘制
    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface, info: dict) -> None:
        """绘制面板。info 包含展示字段（见 GameUI.get_info）。"""
        x, w = self.x, self.width
        pygame.draw.rect(surface, theme.PANEL_BG, (x, 0, w, surface.get_height()))

        f_title = self._font(22)
        f_body = self._font(16)
        f_small = self._font(14)

        # 标题
        title = f_title.render("五子棋", True, theme.TEXT_PRIMARY)
        surface.blit(title, (x + 16, 16))

        # 玩家信息
        self._text(surface, f_body, "黑方：" + info["black_label"], x + 16, 60)
        self._text(surface, f_body, "白方：" + info["white_label"], x + 16, 84)
        self._text(surface, f_body, "当前行动：" + info["turn_label"], x + 16, 108)

        # 对局状态
        status = info["status"]
        color = theme.TEXT_PRIMARY
        if status == "黑方获胜":
            color = theme.WIN_COLOR
        elif status == "白方获胜":
            color = theme.WIN_COLOR
        elif status == "平局":
            color = theme.DRAW_COLOR
        self._text(surface, f_body, "状态：" + status, x + 16, 132, color=color)
        self._text(surface, f_body, "步数：" + str(info["move_count"]), x + 16, 156)
        if info.get("last_move_label"):
            self._text(surface, f_small, "最近落子：" + info["last_move_label"],
                       x + 16, 180, color=theme.TEXT_SECONDARY)

        # 按钮
        for btn in self.buttons:
            btn.draw(surface, f_body)

        # AI 信息
        y = 360
        self._text(surface, f_title, "AI 信息", x + 16, y)
        y += 34
        self._text(surface, f_small, "AI 代理：" + info["ai_label"], x + 16, y)
        y += 22
        thinking = info.get("thinking", False)
        tlabel = "思考中..." if thinking else "空闲"
        self._text(surface, f_small, "状态：" + tlabel, x + 16, y,
                   color=theme.TEXT_ACCENT if thinking else theme.TEXT_SECONDARY)
        y += 22
        self._text(surface, f_small, "思考用时：" + info.get("think_time", "—"),
                   x + 16, y)
        y += 22
        self._text(surface, f_small, "搜索深度：" + info.get("depth", "暂不可用"),
                   x + 16, y)
        y += 22
        self._text(surface, f_small, "推荐落子：" + info.get("suggest", "暂不可用"),
                   x + 16, y)
        y += 22
        self._text(surface, f_small, "局面评分：" + info.get("score", "暂不可用"),
                   x + 16, y)
        y += 22
        self._text(surface, f_small, "VCF 必胜：" + info.get("vcf", "—"),
                   x + 16, y)
        y += 22
        self._text(surface, f_small, "搜索节点：" + info.get("nodes", "—"),
                   x + 16, y)
        y += 22
        self._text(surface, f_small, "NPS：" + info.get("nps", "—"),
                   x + 16, y)

        # 模式说明
        y += 30
        self._text(surface, f_small, "模式：" + info.get("mode_label", ""),
                   x + 16, y, color=theme.TEXT_SECONDARY)

    def _text(self, surface, font, txt, x, y, color=None):
        color = color or theme.TEXT_PRIMARY
        surface.blit(font.render(str(txt), True, color), (x, y))

    # ------------------------------------------------------------------
    # 事件
    # ------------------------------------------------------------------
    def handle_click(self, pos) -> bool:
        """处理点击，命中按钮则触发回调并返回 True。"""
        for btn in self.buttons:
            if btn.contains(pos):
                if btn.callback:
                    btn.callback()
                return True
        return False

    def handle_hover(self, pos) -> None:
        for btn in self.buttons:
            btn.hovered = btn.contains(pos)

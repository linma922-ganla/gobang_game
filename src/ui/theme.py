"""UI 主题与布局配置。

集中管理颜色、字体、尺寸等视觉参数，方便统一调整风格。
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# 颜色
# ---------------------------------------------------------------------------
# 棋盘木质背景
WOOD_LIGHT = (222, 184, 135)   # 亮木色
WOOD_DARK = (205, 161, 109)    # 稍深木色
WOOD_EDGE = (139, 101, 64)     # 边框

# 棋盘线
GRID_LINE = (90, 65, 40)
STAR_MARK = (70, 50, 30)

# 棋子
BLACK_STONE = (30, 30, 30)
BLACK_STONE_HI = (70, 70, 70)
WHITE_STONE = (245, 245, 245)
WHITE_STONE_HI = (255, 255, 255)

# 高亮
LAST_MOVE_RING = (220, 40, 40)       # 最近落子红圈
HOVER_GHOST = (0, 0, 0, 90)          # 悬停预览
WIN_LINE = (255, 200, 0)             # 获胜连线金色

# 面板
PANEL_BG = (40, 42, 48)
PANEL_CARD = (54, 57, 64)
PANEL_BORDER = (72, 75, 82)
TEXT_PRIMARY = (235, 235, 235)
TEXT_SECONDARY = (165, 168, 175)
TEXT_ACCENT = (120, 180, 255)

# 按钮
BTN_BG = (70, 74, 84)
BTN_HOVER = (88, 92, 104)
BTN_ACTIVE = (58, 110, 165)          # 选中态
BTN_TEXT = (235, 235, 235)

# 状态色
WIN_COLOR = (80, 200, 120)
DRAW_COLOR = (210, 180, 90)

# ---------------------------------------------------------------------------
# 字体
# ---------------------------------------------------------------------------
# 中文字体候选（按优先级），用于正确渲染中文。
# 优先使用 Windows 系统字体文件的绝对路径（最可靠），
# 其次用 SysFont 名称匹配，最后回退 pygame 默认字体（中文会乱码）。
import os

CJK_FONT_FILES = [
    os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts", "msyh.ttc"),
    os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts", "simhei.ttf"),
    os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts", "simsun.ttc"),
    os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts", "msyhbd.ttc"),
]

CJK_FONT_CANDIDATES = [
    "microsoftyahei", "msyh", "simhei", "simsun",
    "dengxian", "kaiti", "fangsong",
]

# ---------------------------------------------------------------------------
# 布局尺寸
# ---------------------------------------------------------------------------
BOARD_SIZE = 15
CELL_SIZE = 40          # 每格像素
MARGIN = 34             # 棋盘边缘留白
BOARD_PX = MARGIN * 2 + CELL_SIZE * (BOARD_SIZE - 1)  # 棋盘总像素宽

PANEL_WIDTH = 300       # 右侧信息面板宽度
WINDOW_HEIGHT = BOARD_PX + 40  # 底部留白放状态栏

STAR_POINTS = [(3, 3), (3, 11), (11, 3), (11, 11), (7, 7)]  # 星位

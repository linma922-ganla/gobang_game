"""UI 包：Pygame 五子棋游戏界面。

模块划分：
- theme.py          颜色 / 字体 / 布局配置
- board_renderer.py 棋盘与棋子绘制、坐标映射
- sidebar.py        侧边栏信息面板与按钮
- ai_runner.py      AI 后台线程调度（不阻塞主线程）
- game_ui.py        界面状态与游戏协调
- app.py            Pygame 应用入口与主循环
"""

from .app import App, main

__all__ = ["App", "main"]

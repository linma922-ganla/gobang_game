"""pytest 配置：将 src 目录加入 sys.path，使测试可直接 import environment/agents。

注意：pyproject.toml 中已配置 `pythonpath = ["src"]`（pytest 8+ 原生支持），
此处作为兜底，同时兼容从任意工作目录运行 pytest 的情况。
"""

import os
import sys

# tests/ 的上一级即项目根目录（gomoku_agent/），src 位于其下
_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
_SRC = os.path.normpath(_SRC)
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

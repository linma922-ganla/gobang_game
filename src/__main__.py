"""支持 ``python -m src`` 直接启动游戏界面。"""

import sys

from .ui.app import main

if __name__ == "__main__":
    sys.exit(main())

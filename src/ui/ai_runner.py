"""AI 调度器：在后台线程执行 AI 计算，避免阻塞 Pygame 主线程。

设计要点：
- 主线程只负责绘制与事件；AI 的 choose_action 在独立线程运行。
- 通过 queue 安全地回传结果。
- 支持 generation（代次）标记：重新开局后，旧对局尚未返回的结果会被丢弃，
  不会污染新棋局。
- 后台线程绝不直接调用任何 Pygame 绘制接口。
"""

from __future__ import annotations

import threading
import time
from typing import Optional

from environment import Game
from agents import Agent


class AIRequest:
    """一次 AI 落子请求。"""

    def __init__(self, agent: Agent, game: Game, generation: int):
        self.agent = agent
        self.game = game  # 传入克隆，避免与主线程棋盘竞争
        self.generation = generation
        self.result: Optional[int] = None
        self.done = False
        self.started_at = time.time()

    @property
    def elapsed(self) -> float:
        return time.time() - self.started_at


class AIRunner:
    """AI 后台调度器。"""

    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._request: Optional[AIRequest] = None
        self._lock = threading.Lock()
        self._generation = 0

    def new_generation(self) -> None:
        """开始新的一局时调用，使旧请求失效。"""
        with self._lock:
            self._generation += 1
            self._request = None
            self._thread = None

    @property
    def generation(self) -> int:
        return self._generation

    def is_busy(self) -> bool:
        with self._lock:
            return self._thread is not None and self._thread.is_alive()

    def start(self, agent: Agent, game: Game) -> bool:
        """发起一次 AI 落子请求（在后台线程执行）。

        Returns:
            是否成功发起（若已有线程在跑则返回 False）。
        """
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return False
            req = AIRequest(agent, game.clone(), self._generation)
            self._request = req
            self._thread = threading.Thread(
                target=self._run, args=(req,), daemon=True)
            self._thread.start()
            return True

    def _run(self, req: AIRequest) -> None:
        try:
            action = req.agent.choose_action(req.game)
        except Exception as exc:  # 不再静默吞掉，暴露真实错误便于定位
            import traceback
            traceback.print_exc()
            # 兜底：返回一个合法落子，避免对局卡死
            action = self._fallback_action(req.game)
        finally:
            req.result = action
            req.done = True

    @staticmethod
    def _fallback_action(game: Game) -> Optional[int]:
        """AI 异常时的兜底落子：返回第一个合法空位。"""
        try:
            legal = game.legal_actions()
            if legal:
                return legal[0]
        except Exception:
            pass
        return None

    def poll(self) -> Optional[int]:
        """若 AI 已完成且属于当前代次，返回动作；否则返回 None。"""
        with self._lock:
            req = self._request
            if req is None:
                return None
            if not req.done:
                return None
            if req.generation != self._generation:
                # 旧代次结果，丢弃
                self._request = None
                self._thread = None
                return None
            self._request = None
            self._thread = None
            return req.result

    def current_elapsed(self) -> float:
        """当前正在计算的请求已耗时（秒），无则返回 0。"""
        with self._lock:
            if self._request is not None and not self._request.done:
                return self._request.elapsed
            return 0.0

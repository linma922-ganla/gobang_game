"""游戏界面状态与协调层。

持有：
- 一个 Game 实例（后端环境）。
- 游戏模式（双人 / 人机 / AI 对战）。
- 双方的身份（人类 / RandomAgent / TacticalAgent）。
- AIRunner（后台 AI 调度）。

负责处理玩家落子、悔棋、重新开始、切换模式等交互，
并把「需要展示的信息」汇总成 dict 供侧边栏渲染。

本模块不直接接触 Pygame 绘图，便于 headless 测试。
"""

from __future__ import annotations

import time
from typing import Optional

from environment import Game, Board, BLACK, WHITE, EMPTY, other, get_win_line, action_to_row_col
from agents import Agent, RandomAgent, TacticalAgent
from .ai_runner import AIRunner


# 玩家身份标记
HUMAN = "human"


class GameUI:
    """界面层的游戏协调器。"""

    def __init__(self, size: int = 15):
        self.size = size
        self.game = Game(size)
        self.mode = "human_vs_ai"   # human_vs_ai | human_vs_human | ai_vs_ai
        self.human_color = BLACK    # 人类执黑或执白（人机模式）
        self._black: object = HUMAN
        self._white: object = HUMAN
        self.ai_runner = AIRunner()
        self._last_move: Optional[tuple] = None
        self._win_line = []
        self._ai_t0 = 0.0
        self._ai_elapsed = 0.0
        self._reset_ai_tracking()
        self._apply_mode("human_vs_ai")

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------
    def _reset_ai_tracking(self) -> None:
        self._ai_t0 = 0.0
        self._ai_elapsed = 0.0

    def _apply_mode(self, mode: str) -> None:
        """根据模式设置黑白双方身份。"""
        self.mode = mode
        if mode == "human_vs_human":
            self._black = HUMAN
            self._white = HUMAN
        elif mode == "human_vs_ai":
            # 人类执 human_color，另一方是 AI
            ai = TacticalAgent(name="战术AI")
            if self.human_color == BLACK:
                self._black = HUMAN
                self._white = ai
            else:
                self._black = ai
                self._white = HUMAN
        elif mode == "ai_vs_ai":
            self._black = RandomAgent(name="随机AI")
            self._white = TacticalAgent(name="战术AI")

    # ------------------------------------------------------------------
    # 对局控制
    # ------------------------------------------------------------------
    def new_game(self) -> None:
        self.game = Game(self.size)
        self._last_move = None
        self._win_line = []
        self._reset_ai_tracking()
        self.ai_runner.new_generation()
        self._apply_mode(self.mode)

    def restart(self) -> None:
        self.new_game()

    def set_mode(self, mode: str) -> None:
        self._apply_mode(mode)
        self.new_game()

    def set_human_color(self, color: int) -> None:
        self.human_color = color
        if self.mode == "human_vs_ai":
            self.new_game()

    def swap_human_color(self) -> None:
        self.set_human_color(other(self.human_color))

    def undo(self) -> bool:
        """悔棋。

        - 人机模式：撤销到「轮到人类」的状态，即撤销最近一轮（AI 手 + 人类手）。
        - 其他模式：撤销上一步。
        """
        if self.game.move_count == 0:
            return False

        if self.mode == "human_vs_ai":
            target = self.human_color
            # 若当前已轮到人类（说明刚撤销过或 AI 尚未落子），仍需再撤销两手
            # 以回到「人类尚未落这一手」之前；否则先撤销到轮到人类。
            # 统一策略：最多撤销 2 手，每手后检查是否已经「轮到人类且至少撤了一手」。
            # 更稳健：先撤 1 手；若仍不是人类回合，再撤 1 手。
            if not self.game.undo():
                self._refresh_after_undo()
                return False
            if self.game.current_player != target:
                self.game.undo()
            self._refresh_after_undo()
            return True
        else:
            if not self.game.undo():
                return False
            self._refresh_after_undo()
            return True

    def _refresh_after_undo(self) -> None:
        self._last_move = self.game.last_move
        self._win_line = []
        self.ai_runner.new_generation()

    # ------------------------------------------------------------------
    # 落子（玩家点击）
    # ------------------------------------------------------------------
    def human_move(self, row: int, col: int) -> bool:
        """玩家尝试在 (row,col) 落子。"""
        if self.game.done:
            return False
        # 仅人类回合才接受点击
        if not self._is_human_turn():
            return False
        ok = self.game.play(row, col)
        if not ok:
            return False
        self._after_move()
        return True

    def _after_move(self) -> None:
        self._last_move = self.game.last_move
        self._win_line = []
        if self.game.done and self.game.winner != EMPTY:
            self._win_line = get_win_line(self.game.board, self.game.last_move,
                                          self.game.win_length)

    # ------------------------------------------------------------------
    # AI 调度
    # ------------------------------------------------------------------
    def _is_human_turn(self) -> bool:
        if self.game.done:
            return False
        cur = self.game.current_player
        return self._player_is_human(cur)

    def _player_is_human(self, color: int) -> bool:
        return (self._black if color == BLACK else self._white) == HUMAN

    def _player_agent(self, color: int) -> Optional[Agent]:
        p = self._black if color == BLACK else self._white
        return p if isinstance(p, Agent) else None

    def maybe_start_ai(self) -> None:
        """若当前轮到 AI 且 AI 空闲，则发起后台计算。"""
        if self.game.done:
            return
        if self.ai_runner.is_busy():
            return
        agent = self._player_agent(self.game.current_player)
        if agent is None:
            return
        self._reset_ai_tracking()
        self._ai_t0 = time.time()
        self.ai_runner.start(agent, self.game)

    def poll_ai(self) -> None:
        """主循环每帧调用：检查 AI 是否完成并落子。"""
        if self.ai_runner.is_busy():
            self._ai_elapsed = time.time() - self._ai_t0
        action = self.ai_runner.poll()
        if action is None:
            return
        # AI 完成：落子（需校验代次由 poll 内部保证）
        if self.game.done:
            return
        self.game.play_action(action)
        self._after_move()
        self._ai_elapsed = 0.0

    # ------------------------------------------------------------------
    # 信息汇总（供侧边栏）
    # ------------------------------------------------------------------
    def get_info(self) -> dict:
        g = self.game
        black_label = self._player_label(BLACK)
        white_label = self._player_label(WHITE)
        turn = "黑方" if g.current_player == BLACK else "白方"

        if g.done:
            if g.winner == BLACK:
                status = "黑方获胜"
            elif g.winner == WHITE:
                status = "白方获胜"
            else:
                status = "平局"
        else:
            status = "进行中"

        last_label = ""
        if g.last_move is not None:
            r, c = g.last_move
            last_label = f"({r+1},{c+1})"

        # AI 信息
        cur_agent = self._player_agent(g.current_player) if not g.done else None
        ai_label = cur_agent.name if cur_agent else "—"
        thinking = self.ai_runner.is_busy()

        return {
            "black_label": black_label,
            "white_label": white_label,
            "turn_label": turn,
            "status": status,
            "move_count": g.move_count,
            "last_move_label": last_label,
            "ai_label": ai_label,
            "thinking": thinking,
            "think_time": f"{self._ai_elapsed:.2f}s" if thinking else "—",
            "depth": "暂不可用",       # Alpha-Beta 未接入
            "suggest": "暂不可用",     # 无搜索信息
            "score": "暂不可用",       # 无网络评估
            "mode_label": self._mode_label(),
        }

    def _player_label(self, color: int) -> str:
        p = self._black if color == BLACK else self._white
        if p == HUMAN:
            return "玩家"
        return p.name

    def _mode_label(self) -> str:
        return {
            "human_vs_human": "双人对战",
            "human_vs_ai": "人机对战",
            "ai_vs_ai": "AI 自动对战",
        }[self.mode]

    # ------------------------------------------------------------------
    # 供渲染层读取的状态
    # ------------------------------------------------------------------
    @property
    def board(self) -> Board:
        return self.game.board

    @property
    def current_player(self) -> int:
        return self.game.current_player

    @property
    def last_move(self) -> Optional[tuple]:
        return self._last_move

    @property
    def win_line(self):
        return self._win_line

    @property
    def done(self) -> bool:
        return self.game.done

    @property
    def winner(self) -> int:
        return self.game.winner

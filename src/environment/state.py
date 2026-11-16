"""状态（State）抽象。

将五子棋对局状态封装为独立对象，供强化学习与搜索引擎统一读取。

State 聚合三部分信息：
- 棋盘快照（Board 的二维网格）
- 对局元信息（当前行动方、最近落子、胜负状态、落子历史）
- 编码能力（生成神经网络输入张量）

设计目标：
- 与 Game 解耦：State 是不可变快照，Game 负责推进，State 负责「读取」。
- 统一观测接口：`board_array`（二维）、`encode`（3×15×15）、`legal_actions`。
- 视角无关：`from_perspective(player)` 可生成任意行动方视角的状态编码。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np

from .board import Board, EMPTY, BLACK, WHITE, other
from .encoding import encode_board
from .rules import Rules

Point = Tuple[int, int]


@dataclass
class State:
    """五子棋对局状态快照。

    Attributes:
        board: 棋盘快照（深拷贝，独立于原始 Game）。
        current_player: 当前行动方（BLACK 或 WHITE）。
        last_move: 最近一次落子坐标 (row, col)，无则 None。
        winner: 胜负状态（BLACK/WHITE/EMPTY）。
        done: 对局是否已结束。
        move_history: 落子历史（一维动作索引列表，按时间顺序）。
        size: 棋盘边长。
        win_length: 获胜所需连子数。
    """

    board: Board
    current_player: int = BLACK
    last_move: Optional[Point] = None
    winner: int = EMPTY
    done: bool = False
    move_history: List[int] = field(default_factory=list)
    size: int = 15
    win_length: int = 5

    # ------------------------------------------------------------------
    # 构造
    # ------------------------------------------------------------------
    @classmethod
    def from_game(cls, game: "Game") -> "State":
        """从 Game 对象构建不可变状态快照。"""
        return cls(
            board=game.board.copy(),
            current_player=game.current_player,
            last_move=game.last_move,
            winner=game.winner,
            done=game.done,
            move_history=[m.action for m in game.moves],
            size=game.size,
            win_length=game.win_length,
        )

    # ------------------------------------------------------------------
    # 棋盘观测
    # ------------------------------------------------------------------
    def board_array(self) -> np.ndarray:
        """返回二维棋盘数组（shape: (size, size)，dtype int8）。

        取值：0 空位 / 1 黑子 / 2 白子。
        """
        return self.board.to_numpy()

    # ------------------------------------------------------------------
    # 神经网络输入编码
    # ------------------------------------------------------------------
    def encode(self, perspective: Optional[int] = None) -> np.ndarray:
        """生成神经网络输入张量（shape: (3, size, size)，float32）。

        三通道：通道0 = 视角方棋子，通道1 = 对手棋子，通道2 = 最近落子。

        Args:
            perspective: 编码视角方。默认 None 表示使用 current_player 视角。

        Returns:
            np.ndarray, shape (3, size, size)。
        """
        player = self.current_player if perspective is None else perspective
        return encode_board(self.board, player, self.last_move)

    # ------------------------------------------------------------------
    # 动作空间
    # ------------------------------------------------------------------
    def legal_actions(self) -> List[int]:
        """返回当前行动方所有合法动作（一维索引），即非法动作屏蔽。"""
        rules = Rules(self.size, self.win_length)
        actions = []
        for (r, c) in rules.legal_actions(self.board):
            actions.append(r * self.size + c)
        return actions

    def legal_action_mask(self) -> np.ndarray:
        """返回合法动作掩码（shape: (size*size,)，1 合法 / 0 非法）。

        供神经网络 policy head 做非法动作屏蔽。
        """
        mask = np.zeros(self.size * self.size, dtype=np.float32)
        for a in self.legal_actions():
            mask[a] = 1.0
        return mask

    # ------------------------------------------------------------------
    # 状态唯一标识（对齐导师的 hash 思想）
    # ------------------------------------------------------------------
    def hash_key(self) -> tuple:
        """返回状态的唯一标识 tuple，供查表（置换表 / 经验表 / Replay Buffer）使用。

        与导师 TicTacToe 的 hash() 一致：把棋盘展平成一维 tuple 作为键。
        区别（我们做得更严谨）：额外把 current_player 纳入哈希，
        因为同一棋盘在「轮到我」和「轮到对手」时是不同的状态。

        Returns:
            (展平棋盘 tuple, current_player) —— 可直接作为 dict 的 key。
        """
        flat = tuple(self.board_array().reshape(-1).tolist())
        return (flat, self.current_player)

    def zobrist_hash(self) -> int:
        """预留：返回 Zobrist 哈希值（Phase 3 置换表使用）。

        当前以内置 hash 实现，Phase 3 将替换为增量式 Zobrist 哈希。
        """
        return hash(self.hash_key())

    # ------------------------------------------------------------------
    # 视角工具
    # ------------------------------------------------------------------
    def from_perspective(self, player: int) -> "State":
        """返回以 player 为「当前行动方视角」的编码，不改变棋盘。

        注意：本方法返回的是编码，而非新 State；如需完整视角镜像，
        可使用 encode(perspective=player)。
        """
        # 保持语义简单：直接返回 encode 结果由调用方使用。
        # 这里提供便捷入口。
        return self.encode(player)

    # ------------------------------------------------------------------
    # 观测打包（强化学习环境常用）
    # ------------------------------------------------------------------
    def observation(self) -> dict:
        """返回强化学习环境所需的完整观测字典。"""
        return {
            "board": self.board_array(),
            "encoded": self.encode(),
            "current_player": self.current_player,
            "last_move": self.last_move,
            "legal_actions": self.legal_actions(),
            "legal_action_mask": self.legal_action_mask(),
            "done": self.done,
            "winner": self.winner,
        }

    # ------------------------------------------------------------------
    # 辅助
    # ------------------------------------------------------------------
    @property
    def opponent(self) -> int:
        """返回对手颜色。"""
        return other(self.current_player)

    def __repr__(self) -> str:
        status = "done" if self.done else "playing"
        return (
            f"State(player={self.current_player}, moves={len(self.move_history)}, "
            f"winner={self.winner}, {status})"
        )

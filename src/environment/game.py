"""五子棋对局管理。

Game 类负责维护一盘棋的状态：当前棋盘、行动方、落子历史、
胜负结果等，并统一调用 Board 与 Rules 完成落子与判定。

同时实现奖励（稀疏奖励）与视角符号转换，供强化学习使用。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .board import Board, BLACK, EMPTY, WHITE, other, row_col_to_action
from .rules import Rules

Point = Tuple[int, int]


@dataclass
class MoveRecord:
    """单步落子记录。"""

    action: int            # 一维动作索引 row*size+col
    row: int
    col: int
    player: int            # BLACK 或 WHITE


@dataclass
class GameResult:
    """一局对局的最终结果。"""

    winner: int            # BLACK / WHITE / EMPTY(平局)
    moves: List[MoveRecord] = field(default_factory=list)
    reason: str = ""       # 结束原因描述


class Game:
    """五子棋对局。

    用法::

        game = Game()
        game.play(7, 7)   # 黑方落子
        game.play(7, 8)   # 白方落子
        ...
        game.winner  # 查询胜负
    """

    def __init__(self, size: int = 15, win_length: int = 5, forbidden: bool = False):
        self.size = size
        self.win_length = win_length
        self.board = Board(size)
        self.rules = Rules(size, win_length, forbidden)

        self.current_player: int = BLACK
        self.moves: List[MoveRecord] = []
        self.winner: int = EMPTY
        self.done: bool = False
        self.last_move: Optional[Point] = None

    # ------------------------------------------------------------------
    # 状态查询
    # ------------------------------------------------------------------
    @property
    def move_count(self) -> int:
        return len(self.moves)

    def legal_actions(self) -> List[int]:
        """返回当前行动方所有合法动作（一维索引）。"""
        actions = []
        for (r, c) in self.rules.legal_actions(self.board):
            actions.append(row_col_to_action(r, c, self.size))
        return actions

    def is_legal(self, row: int, col: int) -> bool:
        return self.rules.is_legal(self.board, row, col)

    # ------------------------------------------------------------------
    # 落子
    # ------------------------------------------------------------------
    def play(self, row: int, col: int) -> bool:
        """当前行动方在 (row, col) 落子。

        Returns:
            落子成功返回 True；对局已结束或位置非法返回 False。
        """
        if self.done:
            return False
        if not self.board.place(row, col, self.current_player):
            return False

        self.last_move = (row, col)
        self.moves.append(MoveRecord(
            action=row_col_to_action(row, col, self.size),
            row=row,
            col=col,
            player=self.current_player,
        ))

        # 胜负判定
        from .rules import get_winner

        winner = get_winner(self.board, self.last_move, self.win_length)
        if winner != EMPTY:
            self.winner = winner
            self.done = True
        elif self.board.is_full():
            self.winner = EMPTY
            self.done = True
        else:
            # 切换行动方
            self.current_player = other(self.current_player)

        return True

    def play_action(self, action: int) -> bool:
        """按一维动作索引落子。"""
        if not (0 <= action < self.size * self.size):
            return False
        r, c = divmod(action, self.size)
        return self.play(r, c)

    def undo(self) -> bool:
        """撤销上一步落子（配合搜索引擎回溯使用）。

        Returns:
            有可撤销的落子返回 True；无历史或已结束且需重置时返回 False。
        """
        if not self.moves:
            return False
        last = self.moves.pop()
        self.board.undo_move(last.row, last.col)
        # 恢复状态：上一步落子者重新成为当前行动方
        self.current_player = last.player
        self.done = False
        self.winner = EMPTY
        # 回退 last_move 到更早一步
        self.last_move = (self.moves[-1].row, self.moves[-1].col) if self.moves else None
        return True

    # ------------------------------------------------------------------
    # 奖励与视角符号
    # ------------------------------------------------------------------
    def reward(self, player: int) -> float:
        """返回 player 视角下的稀疏奖励。

        - 获胜 +1，失败 -1，平局 0，对局未结束 0。
        已正确处理零和博弈的符号转换。
        """
        if not self.done:
            return 0.0
        if self.winner == EMPTY:
            return 0.0
        return 1.0 if self.winner == player else -1.0

    def result(self) -> GameResult:
        """返回对局结果记录。"""
        reason = "win" if self.winner != EMPTY else "draw"
        return GameResult(winner=self.winner, moves=list(self.moves), reason=reason)

    def clone(self) -> "Game":
        """深拷贝当前对局状态，供搜索使用。"""
        g = Game(self.size, self.win_length)
        g.board = self.board.copy()
        g.current_player = self.current_player
        g.moves = list(self.moves)
        g.winner = self.winner
        g.done = self.done
        g.last_move = self.last_move
        return g

    def get_state(self) -> "State":
        """返回当前对局的不可变状态快照（State 对象）。"""
        from .state import State
        return State.from_game(self)

    # ------------------------------------------------------------------
    # 棋谱保存 / 加载
    # ------------------------------------------------------------------
    def save(self, path) -> "Path":
        """将当前对局保存为 JSON 棋谱文件。"""
        from .record import save_game
        return save_game(self, path)

    @classmethod
    def load(cls, path) -> "Game":
        """从 JSON 棋谱文件重建对局。"""
        from .record import load_game
        return load_game(path)

    def __repr__(self) -> str:
        status = "done" if self.done else "playing"
        return (
            f"Game(size={self.size}, moves={self.move_count}, "
            f"player={self.current_player}, winner={self.winner}, {status})"
        )

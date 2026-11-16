"""五子棋游戏环境包。"""

from .board import Board, EMPTY, BLACK, WHITE, other, Point, row_col_to_action, action_to_row_col
from .rules import Rules, check_win, check_win_at, get_winner
from .game import Game, GameResult, MoveRecord
from .encoding import encode_board, encode_board_black_perspective
from .state import State

__all__ = [
    "Board", "EMPTY", "BLACK", "WHITE", "other", "Point",
    "row_col_to_action", "action_to_row_col",
    "Rules", "check_win", "check_win_at", "get_winner",
    "Game", "GameResult", "MoveRecord",
    "encode_board", "encode_board_black_perspective",
    "State",
]

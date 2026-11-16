"""战术引擎与搜索引擎包。

包含：
- patterns.py         棋形识别
- tactical_search.py  战术搜索（必胜点/必防点）
- candidate_moves.py  候选动作筛选
- evaluation.py       传统局面评分
"""

from .patterns import (
    Pattern, FIVE, LIVE_FOUR, RUSH_FOUR, LIVE_THREE, SLEEP_THREE,
    LIVE_TWO, SLEEP_TWO, NONE, classify_pattern, find_patterns,
)
from .tactical_search import (
    Outcome, TacticalResult, find_immediate_wins,
    find_opponent_immediate_wins, find_winning_moves,
    find_forced_defense_moves, evaluate_tactical,
)
from .candidate_moves import candidate_moves, center_opening
from .evaluation import evaluate_board, DEFAULT_WEIGHTS, WIN_SCORE, LOSS_SCORE

__all__ = [
    "Pattern", "FIVE", "LIVE_FOUR", "RUSH_FOUR", "LIVE_THREE",
    "SLEEP_THREE", "LIVE_TWO", "SLEEP_TWO", "NONE",
    "classify_pattern", "find_patterns",
    "Outcome", "TacticalResult", "find_immediate_wins",
    "find_opponent_immediate_wins", "find_winning_moves",
    "find_forced_defense_moves", "evaluate_tactical",
    "candidate_moves", "center_opening",
    "evaluate_board", "DEFAULT_WEIGHTS", "WIN_SCORE", "LOSS_SCORE",
]

"""VCF（Victory by Continuous Fours）连续冲四必胜搜索。

VCF 是一种强制进攻序列：我方不断形成「冲四」（对手必须防守），
连续逼迫对手被动应对，最终在某一步形成「活四」或「双冲四」而必胜。

与普通 Alpha-Beta 不同，VCF 只探索满足强制进攻条件的着法序列，
因此可以在很深的层数上快速搜索。

关键语义（务必区分）：
- PROVEN_WIN：已证明存在强制获胜路线。
- PROVEN_NO_WIN：在当前定义的搜索范围内排除了必胜路线。
- UNKNOWN：搜索预算不足，无法判定。

不能因为「没找到必胜」就判定必败；也不能用不完整的防守枚举
错误地宣布必胜。

VCF 是独立模块，供 Alpha-Beta 搜索在根节点和关键战术节点调用。
"""

from __future__ import annotations

import time
from enum import Enum
from typing import List, Optional, Tuple

from environment import Board, EMPTY, BLACK, WHITE, other
from .patterns import classify_pattern, RUSH_FOUR, LIVE_FOUR, FIVE


class VCFResult(Enum):
    PROVEN_WIN = "proven_win"
    PROVEN_NO_WIN = "proven_no_win"
    UNKNOWN = "unknown"


# 冲四：一端被封的四连，落子后下一步必成五连，对手必须防守
# 活四：两端开口的四连，已成必胜（对手无法防守）
# 五连：直接获胜


def _is_five_after(board: Board, r: int, c: int, player: int) -> bool:
    """判断 player 在 (r,c) 落子后是否形成五连。"""
    from environment.rules import check_win_at
    return check_win_at(board, r, c, 5)


def _count_four_threats(board: Board, player: int) -> int:
    """统计 player 当前的「四威胁」数量（冲四 + 活四，按方向去重计数）。"""
    # 冲四与活四都属于「下一步成五」的威胁，但 VCF 的核心是冲四。
    # 这里统计冲四数量（活四已属必胜，单独处理）。
    threats = 0
    seen = set()
    for r in range(board.size):
        for c in range(board.size):
            if board.get(r, c) != player:
                continue
            p = classify_pattern(board, r, c, player)
            if p in (RUSH_FOUR, LIVE_FOUR):
                # 按 (方向起点) 去重：仅当反方向邻位非己方子时计一次
                # 简化：用坐标去重（近似）
                if (r, c) not in seen:
                    threats += 1
                    seen.add((r, c))
    return threats


def _find_rush_four_points(board: Board, player: int) -> List[Tuple[int, int]]:
    """找出 player 所有「落子即形成冲四」的位置（即冲四点）。

    这些点落子后形成冲四，对手必须防守该冲四的成五点。
    """
    points = []
    for r in range(board.size):
        for c in range(board.size):
            if board.get(r, c) != EMPTY:
                continue
            board.make_move(r, c, player)
            # 落子后是否形成冲四（但不形成五连——五连是直接获胜，另判）
            if _is_five_after(board, r, c, player):
                board.undo_move(r, c)
                continue
            if _count_four_threats(board, player) >= 1:
                points.append((r, c))
            board.undo_move(r, c)
    return points


def _has_winning_four(board: Board, player: int) -> bool:
    """判断 player 是否已有「必胜四」：活四（或已五连）。"""
    # 已五连
    for r in range(board.size):
        for c in range(board.size):
            if board.get(r, c) == player and _is_five_after(board, r, c, player):
                return True
    # 活四
    for r in range(board.size):
        for c in range(board.size):
            if board.get(r, c) == player and classify_pattern(board, r, c, player) == LIVE_FOUR:
                return True
    return False


def _find_five_points(board: Board, player: int) -> List[Tuple[int, int]]:
    """找出 player 所有「落子即五连」的直接获胜点。"""
    points = []
    for r in range(board.size):
        for c in range(board.size):
            if board.get(r, c) != EMPTY:
                continue
            if _is_five_after(board, r, c, player):
                points.append((r, c))
    return points


class VCFSearcher:
    """连续冲四必胜搜索器。"""

    def __init__(self, max_depth: int = 12, time_limit_ms: int = 200):
        self.max_depth = max_depth
        self.time_limit_ms = time_limit_ms
        self.nodes = 0

    def search(self, board: Board, player: int) -> VCFResult:
        """判断 player 是否存在 VCF 强制获胜路线。

        Args:
            board: 当前棋盘（会被临时修改，结束后恢复）。
            player: 进攻方。

        Returns:
            VCFResult.PROVEN_WIN / PROVEN_NO_WIN / UNKNOWN。
        """
        self.nodes = 0
        self._start = time.monotonic()
        # 若进攻方已有必胜四或直接五连点，直接获胜
        if _has_winning_four(board, player):
            return VCFResult.PROVEN_WIN
        result = self._attack(board, player, 0)
        return result

    def _timeout(self) -> bool:
        # time_limit_ms 恒表示时间上限；0 表示立即超时（不分配时间）。
        if self.time_limit_ms < 0:
            return False  # 负值表示无时间限制
        return (time.monotonic() - self._start) * 1000 >= self.time_limit_ms

    def _attack(self, board: Board, player: int, depth: int) -> VCFResult:
        """进攻方 player 的回合：寻找冲四/五连点，强制推进。"""
        self.nodes += 1
        if self._timeout():
            return VCFResult.UNKNOWN
        if depth > self.max_depth:
            return VCFResult.UNKNOWN

        opponent = other(player)

        # 1) 直接五连点 -> 立即获胜
        five_points = _find_five_points(board, player)
        if five_points:
            return VCFResult.PROVEN_WIN

        # 2) 已有活四 -> 必胜
        if _has_winning_four(board, player):
            return VCFResult.PROVEN_WIN

        # 3) 冲四点：落子形成冲四，对手必须防
        rush_points = _find_rush_four_points(board, player)
        if not rush_points:
            # 没有冲四点可走，VCF 无法继续（不是必胜，也不是必败）
            return VCFResult.PROVEN_NO_WIN

        # 对每个冲四点尝试
        found_unknown = False
        for (r, c) in rush_points:
            if self._timeout():
                return VCFResult.UNKNOWN
            board.make_move(r, c, player)
            # 落子后可能形成双冲四/活四（即必胜）——由 _has_winning_four 判断
            if _has_winning_four(board, player) and not _is_five_after(board, r, c, player):
                # 落子后形成活四或双冲四 -> 必胜
                board.undo_move(r, c)
                return VCFResult.PROVEN_WIN
            # 否则进入防守方回合
            result = self._defend(board, opponent, depth + 1)
            board.undo_move(r, c)
            if result == VCFResult.PROVEN_WIN:
                return VCFResult.PROVEN_WIN
            if result == VCFResult.UNKNOWN:
                found_unknown = True

        if found_unknown:
            return VCFResult.UNKNOWN
        return VCFResult.PROVEN_NO_WIN

    def _defend(self, board: Board, player: int, depth: int) -> VCFResult:
        """防守方 player 的回合：对手刚形成冲四，必须防守。

        防守方必须堵住对手冲四的成五点。若对手有多个冲四（双冲四），
        防守方无法全防 -> 返回 PROVEN_WIN（表示进攻方已胜）。

        若防守方自己能立即五连/活四，则可反杀（进攻方失败）。
        """
        self.nodes += 1
        if self._timeout():
            return VCFResult.UNKNOWN
        if depth > self.max_depth:
            return VCFResult.UNKNOWN

        opponent = other(player)

        # 防守方先检查自己能否立即获胜（反杀）
        if _find_five_points(board, player):
            return VCFResult.PROVEN_NO_WIN  # 防守方反杀，进攻方不能胜

        # 找出对手（进攻方）的所有冲四成五点，防守方必须全防
        # 这里简化：找出对手所有「落子即五连」的点，即冲四的成五点
        threat_points = _find_five_points(board, opponent)

        if not threat_points:
            # 对手没有立即成五的威胁点（可能只是普通冲四未到成五）
            # 但 VCF 中进攻方落冲四后必有成五点，这里保守返回 UNKNOWN
            return VCFResult.UNKNOWN

        # 若威胁点数量 > 1，防守方无法同时防守 -> 进攻方必胜
        if len(threat_points) >= 2:
            return VCFResult.PROVEN_WIN

        # 只有一个威胁点，防守方必须堵住它
        tr, tc = threat_points[0]
        # 防守方堵住该点
        if board.get(tr, tc) != EMPTY:
            # 该点已被占（异常），保守返回 UNKNOWN
            return VCFResult.UNKNOWN

        board.make_move(tr, tc, player)
        # 防守后，检查进攻方是否还有别的强制手段（回到进攻方回合）
        result = self._attack(board, opponent, depth + 1)
        board.undo_move(tr, tc)

        # 若进攻方在防守后依然能继续强制取胜 -> 进攻方胜
        if result == VCFResult.PROVEN_WIN:
            return VCFResult.PROVEN_WIN
        if result == VCFResult.UNKNOWN:
            return VCFResult.UNKNOWN
        return VCFResult.PROVEN_NO_WIN

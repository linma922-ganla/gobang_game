"""棋形识别模块。

识别五子棋中的基本棋形：
- FIVE     五连（已成五子，必胜）
- LIVE_FOUR 活四（两端开口的四连，下一手必成五连）
- RUSH_FOUR 冲四（一端被封的四连，下一手可成五连）
- LIVE_THREE 活三（两端开口的三连）
- SLEEP_THREE 眠三（一端被封的三连，但仍有成五的潜力）
- LIVE_TWO  活二（两端开口的二连）
- SLEEP_TWO 眠二（一端被封的二连）

设计要点：
- 对每个方向（横、竖、两条对角线）独立分析。
- 统计连续同色棋子长度与两端封堵情况。
- 支持跳跃棋形（中间隔空位的组合），例如 "XX_XX" 属于冲四（跳冲）。
- 黑棋与白棋对称，无颜色偏好。

本模块只做「静态棋形判定」，不涉及走子后是否真的能成五连的博弈推演；
真正的必胜/必败判定由 tactical_search.py 负责。
"""

from __future__ import annotations

from enum import IntEnum
from typing import Dict, List, Tuple

from environment import Board, EMPTY, BLACK, WHITE

# 四个方向：横(0,1)、竖(1,0)、主对角(1,1)、副对角(1,-1)
DIRECTIONS = ((0, 1), (1, 0), (1, 1), (1, -1))


class Pattern(IntEnum):
    """棋形枚举，数值越大威胁越高。"""

    NONE = 0
    SLEEP_TWO = 1     # 眠二
    LIVE_TWO = 2      # 活二
    SLEEP_THREE = 3   # 眠三
    LIVE_THREE = 4    # 活三
    RUSH_FOUR = 5     # 冲四
    LIVE_FOUR = 6     # 活四
    FIVE = 7          # 五连


# 供外部使用的别名
FIVE = Pattern.FIVE
LIVE_FOUR = Pattern.LIVE_FOUR
RUSH_FOUR = Pattern.RUSH_FOUR
LIVE_THREE = Pattern.LIVE_THREE
SLEEP_THREE = Pattern.SLEEP_THREE
LIVE_TWO = Pattern.LIVE_TWO
SLEEP_TWO = Pattern.SLEEP_TWO
NONE = Pattern.NONE


def analyze_direction(board: Board, r: int, c: int, dr: int, dc: int,
                      player: int) -> Pattern:
    """分析以 (r,c) 处 player 棋子为中心、沿 (dr,dc) 方向能形成的棋形。

    该函数分析「经过 (r,c) 这条线」上，player 棋子连续块及其两端开口，
    综合判定棋形等级。跳跃棋形（隔一空位）也被纳入考虑。
    """
    # 沿正反方向统计连续同色棋子
    def count_dir(dr2, dc2):
        cnt = 0
        rr, cc = r + dr2, c + dc2
        while board.in_bounds(rr, cc) and board.get(rr, cc) == player:
            cnt += 1
            rr += dr2
            cc += dc2
        # 返回连块末端后一格坐标
        return cnt, (rr, cc)

    pos_cnt, pos_end = count_dir(dr, dc)
    neg_cnt, neg_end = count_dir(-dr, -dc)

    total = pos_cnt + neg_cnt + 1  # 包含中心自身

    # 两端开口情况：末端后一格是否为「空位」（开口）还是对方/边界（堵）
    def open_at(pt):
        rr, cc = pt
        return board.in_bounds(rr, cc) and board.get(rr, cc) == EMPTY

    pos_open = open_at(pos_end)
    neg_open = open_at(neg_end)

    if total >= 5:
        return FIVE

    if total == 4:
        if pos_open and neg_open:
            return LIVE_FOUR
        elif pos_open or neg_open:
            return RUSH_FOUR
        else:
            return NONE  # 双端堵死的四连无威胁

    if total == 3:
        if pos_open and neg_open:
            return LIVE_THREE
        elif pos_open or neg_open:
            return SLEEP_THREE
        else:
            return NONE

    if total == 2:
        if pos_open and neg_open:
            return LIVE_TWO
        elif pos_open or neg_open:
            return SLEEP_TWO
        else:
            return NONE

    if total == 1:
        # 单子不单独成棋形，但跳跃棋形可能由单子参与，交由外部组合判断
        return NONE

    return NONE


def _scan_line_for_jump(board: Board, r: int, c: int, dr: int, dc: int,
                        player: int) -> Pattern:
    """检测包含 (r,c) 的跳跃棋形。

    跳跃棋形形如 "XX_XX"（隔一空位），在一端补齐后形成冲四/活三等。
    这里实现简化版：沿方向扫描，若发现两个连续块中间隔一个空位，
    合并其长度后重新判定。
    """
    # 收集该方向上所有「块」：连续的 player 子区间
    blocks = []  # (start_step, length, 左开口, 右开口)
    visited = set()
    for step in range(-9, 10):
        rr, cc = r + dr * step, c + dc * step
        if (rr, cc) in visited:
            continue
        if not board.in_bounds(rr, cc) or board.get(rr, cc) != player:
            continue
        # 找到块起点
        start = step
        while start - 1 >= -9:
            pr, pc = r + dr * (start - 1), c + dc * (start - 1)
            if board.in_bounds(pr, pc) and board.get(pr, pc) == player:
                start -= 1
            else:
                break
        # 找到块终点
        end = step
        while end + 1 <= 9:
            nr, nc = r + dr * (end + 1), c + dc * (end + 1)
            if board.in_bounds(nr, nc) and board.get(nr, nc) == player:
                end += 1
            else:
                break
        length = end - start + 1
        blocks.append((start, end, length))
        for s in range(start, end + 1):
            visited.add((r + dr * s, c + dc * s))

    if not blocks:
        return NONE

    # 检查相邻块之间是否只隔一个空位，合并后判定
    blocks.sort()
    best = NONE
    for i in range(len(blocks)):
        s1, e1, l1 = blocks[i]
        # 单块自身
        if l1 >= 5:
            best = max(best, FIVE)
        elif l1 == 4:
            # 判断开口
            left_open = _cell_open(board, r, c, dr, dc, s1 - 1)
            right_open = _cell_open(board, r, c, dr, dc, e1 + 1)
            if left_open and right_open:
                best = max(best, LIVE_FOUR)
            elif left_open or right_open:
                best = max(best, RUSH_FOUR)
        elif l1 == 3:
            left_open = _cell_open(board, r, c, dr, dc, s1 - 1)
            right_open = _cell_open(board, r, c, dr, dc, e1 + 1)
            if left_open and right_open:
                best = max(best, LIVE_THREE)
            elif left_open or right_open:
                best = max(best, SLEEP_THREE)
        elif l1 == 2:
            left_open = _cell_open(board, r, c, dr, dc, s1 - 1)
            right_open = _cell_open(board, r, c, dr, dc, e1 + 1)
            if left_open and right_open:
                best = max(best, LIVE_TWO)
            elif left_open or right_open:
                best = max(best, SLEEP_TWO)

        # 与下一块合并（中间隔一个空位）
        if i + 1 < len(blocks):
            s2, e2, l2 = blocks[i + 1]
            gap = s2 - e1 - 1
            if gap == 1:
                merged = l1 + l2
                # 中间空位记为 (e1+1)
                if merged >= 5:
                    # 检查合并后是否可能成五（跳冲/跳活）
                    # 若总长>=5 且中间空位可落子，则视为冲四（跳冲）
                    best = max(best, RUSH_FOUR)
                elif merged == 4:
                    best = max(best, RUSH_FOUR)
                elif merged == 3:
                    best = max(best, SLEEP_THREE)

    return best


def _cell_open(board: Board, r: int, c: int, dr: int, dc: int, step: int) -> bool:
    rr, cc = r + dr * step, c + dc * step
    return board.in_bounds(rr, cc) and board.get(rr, cc) == EMPTY


def classify_pattern(board: Board, r: int, c: int, player: int) -> Pattern:
    """综合四个方向，返回 (r,c) 处 player 棋子能形成的最高棋形。"""
    best = NONE
    for dr, dc in DIRECTIONS:
        p = analyze_direction(board, r, c, dr, dc, player)
        best = max(best, p)
        # 跳跃棋形总是扫描（基础分析可能只得到低等级棋形）
        jump = _scan_line_for_jump(board, r, c, dr, dc, player)
        best = max(best, jump)
    return best


def find_patterns(board: Board, player: int) -> Dict[Pattern, List[Tuple[int, int]]]:
    """扫描全盘，返回 player 各棋形的落子坐标列表。

    Returns:
        字典，键为 Pattern，值为该棋形对应的关键棋子坐标列表。
    """
    result: Dict[Pattern, List[Tuple[int, int]]] = {
        FIVE: [], LIVE_FOUR: [], RUSH_FOUR: [], LIVE_THREE: [],
        SLEEP_THREE: [], LIVE_TWO: [], SLEEP_TWO: [],
    }
    for r in range(board.size):
        for c in range(board.size):
            if board.get(r, c) == player:
                p = classify_pattern(board, r, c, player)
                if p != NONE and (r, c) not in result[p]:
                    result[p].append((r, c))
    return result


def has_pattern(board: Board, player: int, pattern: Pattern) -> bool:
    """判断 player 是否存在指定棋形（至少一个）。"""
    return bool(find_patterns(board, player)[pattern])

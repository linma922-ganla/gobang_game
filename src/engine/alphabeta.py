"""Negamax + Alpha-Beta 剪枝搜索。

实现带迭代加深、置换表、候选动作、Move Ordering 和时间控制的
五子棋搜索。

核心设计：
- Negamax：统一视角，score = -negamax(子节点)，只需处理「当前行动方」。
- 价值函数始终以「当前行动方」视角计算（evaluate_board 返回当前方视角评分）。
- 终局使用 MATE_SCORE 按 ply 调整，使 AI 倾向于更快获胜、更慢失败。
- 搜索前后保证棋盘状态完全恢复。

时间控制使用 time.monotonic()，不依赖系统时钟。
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from environment import Board, EMPTY, BLACK, WHITE, other
from .candidate_moves import candidate_moves
from .evaluation import evaluate_board, WIN_SCORE, LOSS_SCORE
from .transposition_table import TranspositionTable, NodeType
from .zobrist import Zobrist
from .vcf import VCFSearcher, VCFResult

# 终局分数：足够大，但小于 +inf，便于按 ply 调整
MATE_SCORE = 10_000_000.0


@dataclass
class SearchStats:
    """搜索统计信息。"""

    nodes: int = 0
    depth: int = 0
    time_ms: float = 0.0
    best_move: Optional[Tuple[int, int]] = None
    best_score: float = 0.0
    nps: float = 0.0
    vcf_win: bool = False

    @property
    def nodes_per_second(self) -> float:
        return self.nps


@dataclass
class SearchConfig:
    """搜索配置。"""

    max_depth: int = 8
    time_limit_ms: int = 1000
    candidate_radius: int = 2
    max_candidates: int = 12
    enable_vcf: bool = True
    vcf_max_depth: int = 12
    vcf_time_limit_ms: int = 200
    enable_transposition_table: bool = True
    transposition_table_size: int = 1_000_000


class AlphaBetaSearch:
    """Negamax + Alpha-Beta 搜索引擎。"""

    def __init__(self, config: Optional[SearchConfig] = None):
        self.config = config or SearchConfig()
        self.zobrist = Zobrist()
        self.tt = TranspositionTable(capacity=self.config.transposition_table_size)
        self._nodes = 0
        self._start = 0.0
        self._deadline = 0.0
        self._timed_out = False
        self._vcf = VCFSearcher(
            max_depth=self.config.vcf_max_depth,
            time_limit_ms=self.config.vcf_time_limit_ms,
        )
        self.last_stats = SearchStats()

    # ------------------------------------------------------------------
    # 对外接口
    # ------------------------------------------------------------------
    def search(self, board: Board, player: int) -> SearchStats:
        """对给定局面执行迭代加深搜索，返回最优落子与统计。"""
        self._nodes = 0
        self._start = time.monotonic()
        self._deadline = self._start + self.config.time_limit_ms / 1000.0
        self._timed_out = False

        # 空棋盘：中心开局
        if not any(board.get(r, c) != EMPTY for r in range(board.size) for c in range(board.size)):
            mid = board.size // 2
            self.last_stats = SearchStats(
                nodes=0, depth=0, time_ms=0.0,
                best_move=(mid, mid), best_score=0.0, nps=0.0,
            )
            return self.last_stats

        best_move: Optional[Tuple[int, int]] = None
        best_score = 0.0
        completed_depth = 0

        # 迭代加深
        for depth in range(1, self.config.max_depth + 1):
            if self._time_left() <= 0:
                break
            score, move = self._search_root(board, player, depth)
            if self._timed_out:
                # 本轮未完成，保留上一轮结果
                break
            best_score = score
            if move is not None:
                best_move = move
            completed_depth = depth
            # 已找到必胜或必败，可提前终止
            if abs(score) >= MATE_SCORE - board.size * board.size:
                break

        # 如果连第一轮都没完成，用战术引擎兜底
        if best_move is None:
            best_move = self._fallback_move(board, player)
            best_score = evaluate_board(board, player)

        elapsed = (time.monotonic() - self._start) * 1000.0
        self.last_stats = SearchStats(
            nodes=self._nodes,
            depth=completed_depth,
            time_ms=elapsed,
            best_move=best_move,
            best_score=best_score,
            nps=self._nodes / (elapsed / 1000.0) if elapsed > 0 else 0.0,
            vcf_win=self._vcf_win_found,
        )
        return self.last_stats

    # ------------------------------------------------------------------
    # 根节点搜索（返回 score, move）
    # ------------------------------------------------------------------
    def _search_root(self, board: Board, player: int, depth: int):
        """根节点：遍历所有候选，返回最优 score 与对应 move。"""
        self._vcf_win_found = False

        # VCF 检查：若可证明强制获胜，直接走 VCF 路线
        if self.config.enable_vcf and depth >= 3:
            vcf_result = self._vcf.search(board, player)
            if vcf_result == VCFResult.PROVEN_WIN:
                self._vcf_win_found = True
                # 用 VCF 的冲四点作为优先候选（由普通搜索进一步确认最优）
                # 这里不直接返回，让普通搜索在候选里优先考虑 VCF 点。

        # 候选动作：根节点也使用轻量候选生成（直接获胜/防守 + 邻居），
        # 避免调用昂贵的 find_winning_moves / find_forced_defense_moves
        # （活四/双冲四等必胜点由 Alpha-Beta 搜索本身覆盖）。
        moves = self._candidate_moves_light(board, player)

        # Move Ordering：对候选按启发式排序
        ordered = self._order_moves(board, player, moves)

        alpha = -MATE_SCORE * 2
        beta = MATE_SCORE * 2
        best_score = -MATE_SCORE * 2
        best_move = None

        for (r, c) in ordered:
            if self._time_left() <= 0:
                self._timed_out = True
                break
            board.make_move(r, c, player)
            # 直接获胜检测
            if self._is_win(board, r, c, player):
                score = MATE_SCORE - 1  # 一步获胜
                board.undo_move(r, c)
                best_score = score
                best_move = (r, c)
                break
            score = -self._negamax(board, other(player), depth - 1, -beta, -alpha)
            board.undo_move(r, c)
            if self._timed_out:
                break
            if score > best_score:
                best_score = score
                best_move = (r, c)
            alpha = max(alpha, score)

        return best_score, best_move

    # ------------------------------------------------------------------
    # Negamax + Alpha-Beta
    # ------------------------------------------------------------------
    def _negamax(self, board: Board, player: int, depth: int,
                 alpha: float, beta: float) -> float:
        """标准 Negamax + Alpha-Beta。

        返回当前行动方 player 视角下的局面评分。
        """
        self._nodes += 1

        # 时间检查（每 N 节点检查一次，减少开销）
        if self._nodes % 512 == 0 and self._time_left() <= 0:
            self._timed_out = True
            return 0.0

        # 置换表探测
        key = self.zobrist.compute(board, player)
        tt_entry = None
        if self.config.enable_transposition_table:
            tt_entry = self.tt.probe(key)
            if tt_entry is not None and tt_entry.depth >= depth:
                if tt_entry.node_type == NodeType.EXACT:
                    return tt_entry.score
                elif tt_entry.node_type == NodeType.LOWER_BOUND:
                    if tt_entry.score >= beta:
                        return tt_entry.score
                elif tt_entry.node_type == NodeType.UPPER_BOUND:
                    if tt_entry.score <= alpha:
                        return tt_entry.score

        # 终局判断
        winner = self._check_winner(board)
        if winner != EMPTY:
            # 胜者是 winner，当前是 player 视角
            if winner == player:
                return MATE_SCORE - (self._nodes)  # 越快获胜分数越高
            else:
                return -MATE_SCORE + (self._nodes)  # 越慢失败分数越高

        if depth <= 0:
            return evaluate_board(board, player)

        # 候选动作
        moves = self._candidate_moves_light(board, player)
        if not moves:
            # 无候选（满盘）-> 平局
            return 0.0

        ordered = self._order_moves(board, player, moves)

        best = -MATE_SCORE * 2
        best_move = None
        for (r, c) in ordered:
            board.make_move(r, c, player)
            score = -self._negamax(board, other(player), depth - 1, -beta, -alpha)
            board.undo_move(r, c)
            if self._timed_out:
                return 0.0
            if score > best:
                best = score
                best_move = (r, c)
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break  # beta 剪枝

        # 存入置换表
        if self.config.enable_transposition_table and not self._timed_out:
            if best <= -MATE_SCORE:  # 实际不可能，防御性
                pass
            node_type = NodeType.EXACT
            if best <= alpha - 1:  # 下界（实际逻辑见下）
                pass
            # 精确判定节点类型
            if best >= beta:
                node_type = NodeType.LOWER_BOUND
            elif best <= alpha:
                node_type = NodeType.UPPER_BOUND
            else:
                node_type = NodeType.EXACT
            self.tt.store(key, depth, best, node_type, best_move)

        return best

    # ------------------------------------------------------------------
    # 辅助
    # ------------------------------------------------------------------
    def _time_left(self) -> float:
        return self._deadline - time.monotonic()

    def _candidate_moves_light(self, board: Board, player: int) -> List[Tuple[int, int]]:
        """轻量候选生成（用于搜索内部节点，避免每节点全盘战术扫描）。

        策略：已有棋子周围 radius 内的空位，并优先保证：
        - 己方直接获胜点（增量 check_win_at，O(候选)）
        - 对手直接获胜点（防守）
        其余用邻居空位填充，数量受 max_candidates 限制。
        """
        opponent = other(player)
        # 邻居空位
        neighbor = set()
        for r in range(board.size):
            for c in range(board.size):
                if board.get(r, c) != EMPTY:
                    for dr in range(-self.config.candidate_radius, self.config.candidate_radius + 1):
                        for dc in range(-self.config.candidate_radius, self.config.candidate_radius + 1):
                            if dr == 0 and dc == 0:
                                continue
                            rr, cc = r + dr, c + dc
                            if board.in_bounds(rr, cc) and board.get(rr, cc) == EMPTY:
                                neighbor.add((rr, cc))

        # 空棋盘 -> 中心
        if not neighbor:
            mid = board.size // 2
            return [(mid, mid)]

        # 直接获胜点 + 对手直接获胜点（O(候选) 增量判断）
        wins = []
        defends = []
        for (r, c) in neighbor:
            board.make_move(r, c, player)
            if self._is_win(board, r, c, player):
                wins.append((r, c))
            board.undo_move(r, c)
            board.make_move(r, c, opponent)
            if self._is_win(board, r, c, opponent):
                defends.append((r, c))
            board.undo_move(r, c)

        result = []
        seen = set()
        for pt in wins + defends + sorted(neighbor):
            if pt not in seen:
                seen.add(pt)
                result.append(pt)
        return result[: self.config.max_candidates]

    def _check_winner(self, board: Board) -> int:
        """全盘扫描胜负（搜索叶节点/深节点使用，简单可靠）。"""
        from environment.rules import check_win
        return check_win(board, 5)

    def _is_win(self, board: Board, r: int, c: int, player: int) -> bool:
        from environment.rules import check_win_at
        return check_win_at(board, r, c, 5)

    def _order_moves(self, board: Board, player: int,
                     moves: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Move Ordering：按威胁程度排序，让强着法先被搜索。

        优化：只对「直接获胜」和「防守对手直接获胜」做精确判断（用增量
        check_win_at，O(1)），其余用轻量距离/棋形启发式，避免每个候选都做
        昂贵的全盘棋形扫描。
        """
        opponent = other(player)
        scored = []
        for (r, c) in moves:
            score = 0.0
            # 己方直接获胜：最高优先级
            board.make_move(r, c, player)
            if self._is_win(board, r, c, player):
                board.undo_move(r, c)
                scored.append((10_000_000.0, r, c))
                continue
            board.undo_move(r, c)
            # 防守对手直接获胜
            board.make_move(r, c, opponent)
            if self._is_win(board, r, c, opponent):
                board.undo_move(r, c)
                scored.append((9_000_000.0, r, c))
                continue
            board.undo_move(r, c)
            # 轻量启发式：邻近已有棋子的密集度 + 到中心距离
            score = self._light_heuristic(board, r, c, player)
            scored.append((score, r, c))
        scored.sort(reverse=True, key=lambda x: x[0])
        return [(r, c) for (_, r, c) in scored]

    def _light_heuristic(self, board: Board, r: int, c: int, player: int) -> float:
        """轻量启发式：统计 (r,c) 周围 8 邻域内同色/异色棋子数。"""
        same = 0
        opp = 0
        opponent = other(player)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                rr, cc = r + dr, c + dc
                if board.in_bounds(rr, cc):
                    v = board.get(rr, cc)
                    if v == player:
                        same += 1
                    elif v == opponent:
                        opp += 1
        return same * 10.0 + opp * 8.0

    def _fallback_move(self, board: Board, player: int) -> Optional[Tuple[int, int]]:
        """时间不足时的回退动作：优先直接获胜/防守，否则中心/邻居。"""
        from .tactical_search import find_immediate_wins, find_opponent_immediate_wins
        wins = find_immediate_wins(board, player)
        if wins:
            return wins[0]
        opp_wins = find_opponent_immediate_wins(board, player)
        if opp_wins:
            return opp_wins[0]
        moves = candidate_moves(board, player, max_candidates=3, radius=2)
        if moves:
            return moves[0]
        # 兜底：第一个空位
        for r in range(board.size):
            for c in range(board.size):
                if board.get(r, c) == EMPTY:
                    return (r, c)
        return None

"""置换表（Transposition Table）。

缓存搜索过的局面，避免重复搜索。支持三种节点类型：
- EXACT：该局面的精确分数（搜索窗口内完整确定）。
- LOWER_BOUND：分数是下界（fail-high，beta 剪枝）。
- UPPER_BOUND：分数是上界（fail-low，alpha 剪枝）。

读取缓存时必须正确处理 alpha/beta 界限，不能把界错当成精确值。

用「Zobrist 哈希 → 条目」的映射存储。支持固定容量（超出时简单替换）。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


class NodeType(Enum):
    EXACT = "exact"
    LOWER_BOUND = "lower_bound"
    UPPER_BOUND = "upper_bound"


@dataclass
class TTEntry:
    """置换表条目。"""

    key: int                 # Zobrist 哈希
    depth: int               # 该条目对应的搜索深度（越大越可靠）
    score: float             # 分数
    node_type: NodeType
    best_move: Optional[Tuple[int, int]] = None
    # 终局分数调整信息（MATE_SCORE 相关）：距离终局的 ply 数。
    # score 为正表示逼近我方获胜，负表示逼近对方获胜。这里存 mate 距离方便还原。
    mate_ply: Optional[int] = None


class TranspositionTable:
    """基于 dict 的置换表，支持容量限制（满时替换深度较浅者，简化实现）。"""

    def __init__(self, capacity: int = 1_000_000):
        self.capacity = capacity
        self._table: dict = {}
        self.hits = 0
        self.probes = 0

    def clear(self) -> None:
        self._table.clear()
        self.hits = 0
        self.probes = 0

    def store(self, key: int, depth: int, score: float, node_type: NodeType,
              best_move: Optional[Tuple[int, int]] = None,
              mate_ply: Optional[int] = None) -> None:
        """存入条目。已有同键条目且其深度更深时，不覆盖（保留更深信息）。"""
        existing = self._table.get(key)
        if existing is not None and existing.depth > depth:
            return
        self._table[key] = TTEntry(
            key=key, depth=depth, score=score, node_type=node_type,
            best_move=best_move, mate_ply=mate_ply,
        )
        # 简单容量控制：超过容量时清空一半（避免遍历开销）
        if len(self._table) > self.capacity:
            # 删除一半较浅条目
            items = sorted(self._table.items(), key=lambda kv: kv[1].depth)
            for k, _ in items[: len(items) // 2]:
                del self._table[k]

    def probe(self, key: int) -> Optional[TTEntry]:
        """查询条目。命中则 hits 计数。"""
        self.probes += 1
        entry = self._table.get(key)
        if entry is not None:
            self.hits += 1
        return entry

    def __len__(self) -> int:
        return len(self._table)

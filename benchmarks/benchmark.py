"""五子棋性能基准测试工具。

测量以下指标（网络部分等模型存在后再跑，见 docstring 中的说明）：
- 搜索：不同局面（开局/中盘/威胁）下的节点数、NPS、耗时、TT 命中率。
- 环境：落子 make_move/undo_move、状态编码 encode、平局判断。
- （未来）网络：CPU/GPU 单状态、Batch 推理、端到端延迟。

用法：
    PYTHONPATH=src python benchmarks/benchmark.py

注意：不要用随机初始化模型的推理速度冒充实际 AI 棋力/性能。
"""

from __future__ import annotations

import time
from typing import List, Tuple

from environment import Game, Board
from engine.alphabeta import AlphaBetaSearch, SearchConfig


# ----------------------------------------------------------------------
# 测试局面构造
# ----------------------------------------------------------------------
def _opening() -> Game:
    """开局：只下一手天元。"""
    g = Game()
    g.play(7, 7)
    return g


def _midgame() -> Game:
    """中盘：12 手。"""
    moves = [(7, 7), (6, 6), (7, 6), (6, 7), (8, 6), (8, 8),
             (6, 5), (7, 5), (5, 7), (9, 7), (5, 6), (4, 5)]
    g = Game()
    for (r, c) in moves:
        g.play(r, c)
    return g


def _threat() -> Game:
    """威胁局面：黑方即将成四。"""
    moves = [(7, 7), (7, 8), (8, 7), (8, 8), (9, 7), (9, 8),
             (6, 7), (6, 8), (5, 7), (5, 8)]
    g = Game()
    for (r, c) in moves:
        g.play(r, c)
    return g


# ----------------------------------------------------------------------
# 搜索基准
# ----------------------------------------------------------------------
def bench_search(cfg: SearchConfig, label: str) -> None:
    print(f"\n=== 搜索基准：{label} ===")
    for name, make in [("开局", _opening), ("中盘", _midgame), ("威胁", _threat)]:
        g = make()
        s = AlphaBetaSearch(cfg)
        t0 = time.time()
        stats = s.search(g.board, g.current_player)
        dt = (time.time() - t0) * 1000
        print(f"  {name:<4} {stats.summary()}  (wall {dt:.1f}ms)")


# ----------------------------------------------------------------------
# 环境基准
# ----------------------------------------------------------------------
def bench_environment(n: int = 50_000) -> None:
    print("\n=== 环境基准 ===")
    b = Board(15)
    t0 = time.time()
    for i in range(n):
        r, c = (i % 15), (i // 15) % 15
        b.make_move(r, c, 1)
        b.undo_move(r, c)
    dt = (time.time() - t0) * 1000
    print(f"  make_move/undo_move: {n} 次 {dt:.1f}ms ({dt/n*1000:.2f}μs/次)")

    # 状态编码
    g = _midgame()
    t0 = time.time()
    for _ in range(1000):
        g.get_state().encode()
    dt = (time.time() - t0) * 1000
    print(f"  State.encode(): 1000 次 {dt:.1f}ms ({dt/1000*1000:.2f}μs/次)")


# ----------------------------------------------------------------------
# 主入口
# ----------------------------------------------------------------------
def main() -> None:
    # 搜索基准：多档配置
    for depth, budget in [(4, 500), (6, 1000), (8, 3000)]:
        cfg = SearchConfig(max_depth=depth, time_limit_ms=budget,
                           max_candidates=12, enable_vcf=True)
        bench_search(cfg, f"depth={depth} budget={budget}ms")

    bench_environment()

    print("\n[提示] 网络基准（CPU/GPU/Batch 推理）待 Policy-Value 模型存在后再执行。")


if __name__ == "__main__":
    main()

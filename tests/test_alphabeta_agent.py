"""AlphaBetaAgent 与对局测试。"""

import pytest

from environment import Game, BLACK, WHITE, EMPTY
from agents import AlphaBetaAgent, RandomAgent, TacticalAgent
from engine.alphabeta import SearchConfig


def _quick_cfg():
    return SearchConfig(max_depth=3, time_limit_ms=500, max_candidates=10,
                        enable_vcf=True, enable_transposition_table=True)


def _play_game(black_agent, white_agent, max_moves=200):
    """用两个 Agent 下一盘棋，返回 (winner, game)。"""
    g = Game()
    for _ in range(max_moves):
        if g.done:
            break
        if g.current_player == BLACK:
            a = black_agent.choose_action(g)
        else:
            a = white_agent.choose_action(g)
        assert g.play_action(a), "Agent 返回了非法动作"
    return g.winner, g


# ---------------------------------------------------------------------------
# Agent 基本行为
# ---------------------------------------------------------------------------
def test_alphabeta_returns_legal_action():
    g = Game()
    g.play(7, 7)
    g.play(7, 8)
    ab = AlphaBetaAgent(_quick_cfg())
    a = ab.choose_action(g)
    assert a in g.legal_actions()


def test_alphabeta_wins_immediately():
    """四连局面，AlphaBetaAgent 应立即获胜。"""
    g = Game()
    # 黑方四连，白方随便下
    for c in range(4):
        g.play(7, c)      # 黑
        if c < 3:
            g.play(0, c)  # 白
    # 现在轮到黑（第7手），黑应下 (7,4) 或 (7,-1)
    ab = AlphaBetaAgent(_quick_cfg())
    a = ab.choose_action(g)
    r, c = divmod(a, 15)
    assert (r, c) in [(7, 4), (7, -1)] or (r, c) == (7, 4)


def test_alphabeta_blocks_opponent():
    """对手冲四（一端被封），AlphaBetaAgent 应防守唯一成五点。"""
    g = Game()
    # 白方四连 (7,3)(7,4)(7,5)(7,6)，黑方先堵住左端 (7,2)，使白只剩 (7,7) 成五
    g.play(7, 2)  # 黑（先手，堵左端）
    g.play(7, 3)  # 白
    g.play(0, 0)  # 黑
    g.play(7, 4)  # 白
    g.play(0, 1)  # 黑
    g.play(7, 5)  # 白
    g.play(0, 2)  # 黑
    g.play(7, 6)  # 白
    # 现在轮到黑，白方冲四只剩 (7,7) 成五点，黑必须防守 (7,7)
    ab = AlphaBetaAgent(_quick_cfg())
    a = ab.choose_action(g)
    r, c = divmod(a, 15)
    assert (r, c) == (7, 7)


def test_stats_recorded():
    g = Game()
    g.play(7, 7)
    ab = AlphaBetaAgent(_quick_cfg())
    ab.choose_action(g)
    st = ab.stats()
    assert st is not None
    assert st.best_move is not None


def test_reset_clears_state():
    ab = AlphaBetaAgent(_quick_cfg())
    ab.reset()
    assert ab.last_stats is None


# ---------------------------------------------------------------------------
# 对局测试：AlphaBeta vs Random
# ---------------------------------------------------------------------------
def test_alphabeta_beats_random():
    """AlphaBeta 应稳定战胜 Random（至少不输，且多数胜）。"""
    wins = 0
    n = 4  # 少量对局验证基本棋力，避免测试过慢
    for i in range(n):
        black_ab = AlphaBetaAgent(_quick_cfg(), name=f"AB{i}")
        white_rand = RandomAgent(seed=100 + i)
        winner, _ = _play_game(black_ab, white_rand)
        if winner == BLACK:
            wins += 1
    # AlphaBeta 执黑对随机，应至少赢一半（随机几乎无法赢搜索）
    assert wins >= n // 2


def test_alphabeta_vs_tactical():
    """AlphaBeta 与 Tactical Agent 能正常对弈（不崩溃，产出合法结果）。"""
    black_ab = AlphaBetaAgent(_quick_cfg())
    white_tac = TacticalAgent()
    winner, g = _play_game(black_ab, white_tac)
    assert winner in (BLACK, WHITE, EMPTY)
    assert g.move_count >= 1


def test_random_vs_tactical():
    """Random 与 Tactical 能正常对弈。"""
    black_rand = RandomAgent(seed=7)
    white_tac = TacticalAgent()
    winner, g = _play_game(black_rand, white_tac)
    assert winner in (BLACK, WHITE, EMPTY)

"""Gomoku AI Agent 主入口。

当前阶段（Phase 1）提供随机 Agent 自动对局演示，用于验证游戏环境。
后续阶段将在此接入搜索引擎、神经网络与游戏界面。
"""

from __future__ import annotations

import argparse
import random

from environment import Game, BLACK, WHITE, EMPTY
from agents import Agent, RandomAgent, TacticalAgent, AlphaBetaAgent
from engine.alphabeta import SearchConfig

# 命令行参数 -> Agent 工厂
AGENT_CHOICES = {"random", "tactical", "alphabeta"}


def make_agent(kind: str, name: str) -> Agent:
    """根据类型字符串创建 Agent。"""
    if kind == "random":
        return RandomAgent(name=name)
    if kind == "tactical":
        return TacticalAgent(name=name)
    if kind == "alphabeta":
        cfg = SearchConfig(max_depth=6, time_limit_ms=800, max_candidates=10, enable_vcf=True)
        return AlphaBetaAgent(cfg, name=name)
    raise ValueError(f"未知 Agent 类型: {kind}")


def play_auto_game(black: "RandomAgent", white: "RandomAgent", game: Game, verbose: bool = False) -> "Game":
    """执行一局自动对弈，返回结束后的对局对象。"""
    agents = {BLACK: black, WHITE: white}
    step = 0
    while not game.done and step < game.size * game.size:
        agent = agents[game.current_player]
        action = agent.choose_action(game)
        game.play_action(action)
        step += 1
        if verbose:
            r, c = divmod(action, game.size)
            print(f"  第 {step} 手  {'黑' if game.current_player != agent else ''}"
                  f"{('黑' if agents[game.current_player] is black else '白')} -> ({r}, {c})")
    return game


def main() -> None:
    parser = argparse.ArgumentParser(description="Gomoku AI Agent")
    parser.add_argument("--games", type=int, default=1, help="自动对局数量")
    parser.add_argument("--verbose", action="store_true", help="打印每步落子")
    parser.add_argument("--seed", type=int, default=None, help="随机种子")
    parser.add_argument("--gui", action="store_true", help="用图形化界面实时查看对局")
    parser.add_argument("--delay", type=float, default=0.5,
                        help="图形化模式下每步间隔秒数（默认 0.5）")
    parser.add_argument("--black", choices=sorted(AGENT_CHOICES), default="random",
                        help="黑方 Agent 类型（random/tactical/alphabeta，默认 random）")
    parser.add_argument("--white", choices=sorted(AGENT_CHOICES), default="random",
                        help="白方 Agent 类型（random/tactical/alphabeta，默认 random）")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    black = make_agent(args.black, f"黑-{args.black}")
    white = make_agent(args.white, f"白-{args.white}")

    # 图形化模式：一次看一局（带交互），可直接退出
    if args.gui:
        from ui.auto_viewer import view_auto_game
        game = view_auto_game(black, white, delay=args.delay, auto_play=True)
        if game.winner == BLACK:
            print(f"结果: 黑胜 (共 {game.move_count} 手)")
        elif game.winner == WHITE:
            print(f"结果: 白胜 (共 {game.move_count} 手)")
        else:
            print(f"结果: 平局 (共 {game.move_count} 手)")
        return

    stats = {"black": 0, "white": 0, "draw": 0}
    for i in range(args.games):
        game = Game()
        play_auto_game(black, white, game, verbose=args.verbose)
        if game.winner == BLACK:
            stats["black"] += 1
        elif game.winner == WHITE:
            stats["white"] += 1
        else:
            stats["draw"] += 1
        print(f"[对局 {i + 1}] 结果: "
              f"{'黑胜' if game.winner == BLACK else '白胜' if game.winner == WHITE else '平局'} "
              f"(共 {game.move_count} 手)")

    print(f"\n共 {args.games} 局 -> 黑胜 {stats['black']}，白胜 {stats['white']}，平局 {stats['draw']}")


if __name__ == "__main__":
    main()

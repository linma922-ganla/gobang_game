"""Agent 与自动对局单元测试。"""

from environment import Game
from agents import RandomAgent


def test_random_agent_always_legal():
    agent = RandomAgent(seed=42)
    g = Game()
    for _ in range(225):
        if g.done:
            break
        action = agent.choose_action(g)
        r, c = divmod(action, g.size)
        assert g.is_legal(r, c)
        g.play_action(action)


def test_random_agent_reproducible():
    a1 = RandomAgent(seed=1)
    a2 = RandomAgent(seed=1)
    g1 = Game()
    g2 = Game()
    for _ in range(10):
        if g1.done or g2.done:
            break
        assert a1.choose_action(g1) == a2.choose_action(g2)
        g1.play_action(a1.choose_action(g1))
        g2.play_action(a2.choose_action(g2))


def test_auto_game_terminates():
    """随机对局必须能正常结束（有胜负或平局），不会死循环。"""
    agent = RandomAgent(seed=7)
    g = Game()
    steps = 0
    while not g.done and steps < 225:
        action = agent.choose_action(g)
        g.play_action(action)
        steps += 1
    assert g.done is True
    assert steps <= 225

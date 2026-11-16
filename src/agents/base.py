"""Agent 接口定义。

所有对弈智能体（随机、规则、搜索、神经网络）都实现统一的 Agent 接口，
游戏界面通过该接口请求 AI 落子，从而与具体模型解耦。

统一采用一维动作索引（action = row * size + col）作为对外接口。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from environment import Game


class Agent(ABC):
    """对弈智能体基类。"""

    def __init__(self, name: str = "Agent"):
        self.name = name

    @abstractmethod
    def choose_action(self, game: Game) -> int:
        """根据当前局面选择一个合法动作。

        Args:
            game: 当前对局（未结束）。

        Returns:
            一维动作索引（row * size + col）。
        """
        raise NotImplementedError

    def reset(self) -> None:
        """可选：在新对局开始前重置内部状态。"""
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"

"""棋谱（对局记录）的保存与加载。

使用 JSON 格式持久化一局五子棋的完整信息，便于查看、交换与复现。

文件结构::

    {
        "format": "gomoku-record",
        "version": 1,
        "size": 15,
        "win_length": 5,
        "forbidden": false,
        "winner": 1,           # 1=黑胜 / -1=白胜 / 0=平局或未结束
        "reason": "win",       # win / draw / ongoing
        "moves": [             # 按落子顺序排列
            {"row": 7, "col": 7, "player": 1},
            ...
        ]
    }
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .board import BLACK, EMPTY, WHITE
from .game import Game, MoveRecord

FORMAT_NAME = "gomoku-record"
FORMAT_VERSION = 1

_WINNER_NAMES = {
    BLACK: "black",
    WHITE: "white",
    EMPTY: "draw",
}


def save_game(game: Game, path: Union[str, Path]) -> Path:
    """将一局对局保存为 JSON 棋谱文件。

    Args:
        game: 要保存的对局。
        path: 保存路径（.json）。父目录不存在时会自动创建。

    Returns:
        实际写入的文件路径（Path）。
    """
    path = Path(path)
    if path.suffix == "":
        path = path.with_suffix(".json")

    data: Dict[str, Any] = {
        "format": FORMAT_NAME,
        "version": FORMAT_VERSION,
        "size": game.size,
        "win_length": game.win_length,
        "forbidden": getattr(game.rules, "forbidden", False),
        "winner": game.winner,
        "reason": _reason_name(game),
        "moves": [
            {"row": m.row, "col": m.col, "player": m.player}
            for m in game.moves
        ],
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_game(path: Union[str, Path]) -> Game:
    """从 JSON 棋谱文件重建对局。

    Args:
        path: 棋谱文件路径。

    Returns:
        已按落子序列完整重放、恢复到保存时刻状态的 Game。

    Raises:
        ValueError: 文件格式不合法或与代码不兼容。
        FileNotFoundError: 文件不存在。
    """
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))

    if data.get("format") != FORMAT_NAME:
        raise ValueError(f"不是合法的棋谱文件（format 应为 {FORMAT_NAME!r}）")
    if data.get("version", 0) > FORMAT_VERSION:
        raise ValueError(f"棋谱版本 {data.get('version')} 高于当前支持的 {FORMAT_VERSION}")

    size = int(data.get("size", 15))
    win_length = int(data.get("win_length", 5))
    forbidden = bool(data.get("forbidden", False))

    game = Game(size=size, win_length=win_length, forbidden=forbidden)

    for m in data.get("moves", []):
        row = int(m["row"])
        col = int(m["col"])
        player = int(m["player"])
        # 逐手重放。若中途出现非法落子（文件损坏），立即报错而非静默跳过。
        if not game.play(row, col):
            raise ValueError(
                f"棋谱第 {game.move_count + 1} 手非法："
                f"({row}, {col}) by {player}"
            )
        # 校验落子者与棋谱记录一致（保证黑白交替正确）
        if game.moves[-1].player != player:
            raise ValueError(
                f"棋谱第 {len(game.moves)} 手颜色不匹配："
                f"期望 {player}，实际 {game.moves[-1].player}"
            )

    return game


def game_to_dict(game: Game) -> Dict[str, Any]:
    """将对局转为可 JSON 序列化的字典（不落盘）。"""
    return {
        "format": FORMAT_NAME,
        "version": FORMAT_VERSION,
        "size": game.size,
        "win_length": game.win_length,
        "forbidden": getattr(game.rules, "forbidden", False),
        "winner": game.winner,
        "reason": _reason_name(game),
        "moves": [
            {"row": m.row, "col": m.col, "player": m.player}
            for m in game.moves
        ],
    }


def _reason_name(game: Game) -> str:
    if not game.done:
        return "ongoing"
    return "win" if game.winner != EMPTY else "draw"


def moves_to_text(game: Game) -> str:
    """生成人类可读的落子序列文本（用于查看）。"""
    parts = []
    for i, m in enumerate(game.moves, 1):
        color = "黑" if m.player == BLACK else "白"
        parts.append(f"{i}. {color}({m.row},{m.col})")
    return "\n".join(parts)

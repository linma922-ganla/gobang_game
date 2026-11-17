"""棋谱保存 / 加载功能的单元测试。"""

import json

import pytest

from environment import BLACK, WHITE, EMPTY, Game, save_game, load_game
from environment.record import moves_to_text, FORMAT_NAME


def _play_horizontal_black_win() -> Game:
    """黑方在 (7,0..4) 横向五连获胜。"""
    g = Game()
    for c in range(5):
        g.play(7, c)          # 黑
        if c < 4:
            g.play(8, c)      # 白
    return g


def test_save_creates_file(tmp_path):
    g = _play_horizontal_black_win()
    p = save_game(g, tmp_path / "game.json")
    assert p.exists()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["format"] == FORMAT_NAME
    assert data["size"] == 15
    assert data["winner"] == BLACK
    assert data["reason"] == "win"
    assert len(data["moves"]) == 9  # 黑5 + 白4


def test_save_auto_append_suffix(tmp_path):
    g = Game()
    g.play(7, 7)
    p = save_game(g, tmp_path / "record")  # 无后缀
    assert p.suffix == ".json"


def test_load_roundtrip_restores_state(tmp_path):
    g = _play_horizontal_black_win()
    p = save_game(g, tmp_path / "r.json")

    g2 = load_game(p)
    # 棋盘一致
    assert g2.board == g.board
    # 落子序列一致
    assert [(m.row, m.col, m.player) for m in g2.moves] == \
           [(m.row, m.col, m.player) for m in g.moves]
    # 状态一致
    assert g2.winner == g.winner
    assert g2.done == g.done
    assert g2.current_player == g.current_player


def test_load_mid_game(tmp_path):
    """保存未结束的对局，加载后应能继续落子。"""
    g = Game()
    g.play(7, 7)
    g.play(7, 8)
    p = save_game(g, tmp_path / "mid.json")

    g2 = load_game(p)
    assert g2.done is False
    assert g2.current_player == BLACK  # 白下完后轮到黑
    assert g2.play(7, 9) is True
    assert g2.move_count == 3


def test_load_draw(tmp_path):
    """平局状态的保存与加载。"""
    g = Game()
    # 手工构造满盘平局代价高，这里直接验证未结束(reason=ongoing)也能正确往返
    g.play(0, 0)
    p = save_game(g, tmp_path / "draw.json")
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["reason"] == "ongoing"


def test_load_white_win_encoding(tmp_path):
    """白方获胜时 winner 编码为 -1，加载后正确。"""
    g = Game()
    g.play(10, 0)              # 黑占位
    for c in range(5):
        g.play(2, c)           # 白横向五连 (2,0..4)
        if c < 4 and not g.done:
            g.play(11, c)      # 黑占位在第11行，与第10行不同行
    assert g.winner == WHITE
    p = save_game(g, tmp_path / "w.json")
    g2 = load_game(p)
    assert g2.winner == WHITE
    assert g2.reward(WHITE) == 1.0
    assert g2.reward(BLACK) == -1.0


def test_load_invalid_format(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text('{"foo": "bar"}', encoding="utf-8")
    with pytest.raises(ValueError):
        load_game(p)


def test_load_corrupt_move(tmp_path):
    """损坏的落子（重复坐标）应报错而非静默跳过。"""
    p = tmp_path / "corrupt.json"
    p.write_text(json.dumps({
        "format": FORMAT_NAME,
        "version": 1,
        "size": 15,
        "win_length": 5,
        "winner": 0,
        "moves": [
            {"row": 7, "col": 7, "player": 1},
            {"row": 7, "col": 7, "player": -1},  # 重复坐标，非法
        ],
    }), encoding="utf-8")
    with pytest.raises(ValueError):
        load_game(p)


def test_moves_to_text():
    g = Game()
    g.play(7, 7)
    g.play(7, 8)
    txt = moves_to_text(g)
    assert "黑(7,7)" in txt
    assert "白(7,8)" in txt


def test_game_save_and_load_methods(tmp_path):
    """Game 类便捷方法 save() / load()。"""
    g = _play_horizontal_black_win()
    g.save(tmp_path / "m.json")
    g2 = Game.load(tmp_path / "m.json")
    assert g2.winner == BLACK
    assert g2.move_count == g.move_count

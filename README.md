# Gomoku AI Agent

基于强化学习与博弈搜索的五子棋智能体。

一个完整的五子棋 AI 项目，包含游戏环境、博弈搜索、神经网络评估、强化学习、自我对弈训练、棋力评测和可视化界面。

## 目标

开发一个能够超过普通人类玩家，并逐步挑战一般业余棋手的五子棋 AI。

### 技术路线

- **Alpha-Beta 剪枝搜索**：多步博弈决策
- **VCF 战术搜索**：识别连续冲四等强制进攻
- **CNN / ResNet 神经网络**：局面价值评估
- **Self-Play**：与自身及历史版本对弈，产生训练数据
- **Pygame**：完整的五子棋游戏界面

> 不采用纯 DQN / 纯 PPO 作为最终架构。

## 游戏规则

- 15×15 标准棋盘
- 黑白双方轮流落子
- 自由规则：任一方形成五子或以上连续连线即获胜
- 不使用禁手规则（三三、四四等）
- 棋盘填满且无人获胜则平局
- 支持黑白双方交换先手

## 棋子编码约定

采用与课程一致的**三值编码**：

| 棋子 | 数值 |
|------|------|
| 空位 | 0 |
| 黑子 | +1 |
| 白子 | -1 |

该编码使「一行之和」可直接用于胜负判断，也便于零和博弈的价值符号转换。

## 状态表示（State）

状态封装为 `environment/state.py` 的 `State` 类，聚合棋盘快照、当前行动方、落子历史等。提供：
- `board_array()`：二维 numpy 数组（shape 15×15，int8，取值 -1/0/1）
- `encode()`：神经网络输入（3×15×15 三通道）
- `hash_key()`：状态唯一标识 tuple（展平棋盘 + 行动方），用于置换表/经验表查表
- `legal_action_mask()`：非法动作屏蔽掩码

## 项目结构

```
gomoku_agent/
├── configs/            # 配置文件
│   └── default.yaml
├── src/
│   ├── environment/    # 游戏环境：棋盘、规则、状态编码
│   ├── engine/         # 战术引擎 + 搜索引擎
│   ├── network/        # 神经网络（Value Network）
│   ├── training/       # 自我对弈、训练
│   ├── evaluation/     # 竞技场、Elo 评测
│   ├── agents/         # 各类 Agent
│   ├── ui/             # Pygame 游戏界面
│   └── main.py
├── tests/              # 单元测试
├── checkpoints/        # 模型检查点
├── data/               # 训练数据
├── logs/               # 日志
└── docs/               # 文档
```

## 环境要求

- Python 3.12（使用 Anaconda `pytorch_env` 环境）
- NumPy、PyTorch（CUDA 版）、Pygame、Pytest、Matplotlib、PyYAML

## 安装与运行

项目依赖安装在 Anaconda 的 `pytorch_env` 环境（Python 3.12.9，已含 torch 2.6.0+cu124、pygame 等）。

```bash
# 激活环境
conda activate pytorch_env

# 运行测试
cd gomoku_agent
python -m pytest
```

如果 conda 不在 PATH 中，可直接使用环境的 Python 解释器：

```bash
C:\Users\malin\.conda\envs\pytorch_env\python.exe -m pytest
```

## 开发进度

见 [PROJECT_PLAN.md](PROJECT_PLAN.md)。

- [x] Phase 0：环境检查与项目初始化
- [ ] Phase 1：游戏环境
- [ ] Phase 2：基础战术引擎
- [ ] Phase 3：Alpha-Beta 搜索
- [ ] Phase 4：神经网络
- [ ] Phase 5：Self-Play
- [ ] Phase 6：完整游戏界面
- [ ] Phase 7：评测与优化

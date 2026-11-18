# 批量推理接口协议（MODEL INTERFACE）

> 本文件定义未来 Policy-Value 网络的推理接口协议。
> 当前**不实现**完整网络，仅约定接口形状，供后续开发与批量推理服务对齐。
> 避免为此建立空类、空文件或过度抽象的框架。

---

## 1. 设计原则

1. 推理接口与具体模型解耦，便于后续替换 CNN / ResNet / NNUE。
2. 同时支持「单状态」与「批量」两种调用路径，训练和部署共用。
3. 输出统一为 numpy 数组，避免依赖 PyTorch tensor 泄漏到上层。
4. 合法动作掩码由环境层提供，网络只负责输出概率/价值，屏蔽逻辑在调用方或包装层完成。

---

## 2. 接口约定（协议，非实现）

```python
class PolicyValueModel:
    """轻量 Policy-Value 网络推理协议。"""

    def predict(self, states) -> tuple:
        """单状态或批量推理。

        Args:
            states: 单个 State 或 State 列表。每个 State 通过 encode()
                    得到 (3, size, size) 输入；批量则堆叠为 (N, 3, size, size)。

        Returns:
            (policy, value)：
              - policy: np.ndarray，形状 (N, size*size) 的落子概率（已 softmax）。
              - value:  np.ndarray，形状 (N,) 的局面价值，范围 [-1, 1]。
        """

    def predict_batch(self, states) -> tuple:
        """显式批量推理，等价于 predict(states) 的批量路径。"""
```

### 关键约束

- **输入编码**：复用 `State.encode()`，输出 `(3, size, size)` 张量（3 通道：己方/对手/最近落子）。
- **policy 输出**：`(N, 225)` 概率分布，softmax 在模型内完成。
- **value 输出**：`(N,)`，建议经 tanh 压到 [-1, 1]，与现有 `evaluate_board` 的符号方向一致（正=当前方占优）。
- **非法动作屏蔽**：由调用方用 `State.legal_action_mask()`（`(225,)`）与 policy 做 `mask * policy` 后重新归一化。

---

## 3. 与现有 Agent 接口的关系

现有 `Agent.choose_action(game) -> int` 保持不变。未来可新增：

```python
class NetworkAgent(Agent):
    """基于 Policy-Value 网络的 Agent（未来实现）。"""
    def choose_action(self, game):
        state = game.get_state()
        policy, value = self.model.predict([state])
        mask = state.legal_action_mask()
        # mask + argmax（部署期温度 0 时取贪心）
        ...
```

- 训练期用温度采样，部署期退化为贪心（温度 0）。
- 复杂局面可触发有限搜索（见 RESEARCH_ROADMAP 研究 G）。

---

## 4. 批量推理服务（训练期）

- 多个对局产生的待评估状态收集到同一 Batch，统一送入 GPU。
- 避免「每生成一个子节点就调用一次 PyTorch」。
- 延迟评估 vs 批量评估的效率差异见 RESEARCH_ROADMAP 研究 A。

---

## 5. 训练数据格式（Task 7）

统一记录格式，支持 JSONL / NPZ。每条样本字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `board_state` | int8 数组 | 棋盘 `(size, size)`，0/1/2（空/黑/白） |
| `current_player` | int | 1 黑 / -1 白 |
| `policy_target` | float 数组 | `(size*size,)` 目标概率（如 MCTS 访问次数归一化） |
| `value_target` | float | `[-1, 1]` 目标价值（终局回传） |
| `action_mask` | int 数组 | `(size*size,)` 合法动作掩码 |
| `game_result` | int | 1 / -1 / 0（黑胜/白胜/平） |
| `game_length` | int | 总手数 |
| `opening_type` | str | 开局类型（可选） |
| `opponent_version` | str | 对手模型/引擎版本 |
| `source_type` | str | `self_play` / `teacher_distill` / `human` |

### 格式选择

- **JSONL**：人类可读、易调试，适合小规模。
- **NPZ**：紧凑、加载快，适合大规模训练。
- **棋谱 JSON 持久化**（`environment/record.py`）继续保留，不与训练数据格式混为一个文件。

---

## 6. 基准测试指标（Task 6）

未来基准工具需测量（等模型存在后再跑真实基准，**不要用随机初始化模型冒充棋力**）：

- CPU 单状态处理速度
- GPU 单状态推理速度
- GPU Batch 8 / 16 / 32 推理速度
- PyTorch Eager vs 优化执行模式差异
- 完整落子流程端到端延迟

# 项目开发计划

## 分阶段路线图

### Phase 0：环境检查和项目初始化
- [x] 检查本机 Python、PyTorch、CUDA、GPU 环境
- [x] 建立项目目录结构
- [x] 创建依赖配置（requirements.txt、pyproject.toml）
- [x] 创建 README.md 与 PROJECT_PLAN.md

### Phase 1：游戏环境
- [x] 实现 15×15 棋盘、落子、合法性、胜负判断、状态编码
- [x] 随机 Agent 自动对局测试
- [x] 单元测试

### Phase 2：基础战术引擎
- [x] 棋形识别（五连、活四、冲四、活三、眠三、活二、眠二）
- [x] 直接获胜检测、对手必胜点检测、必防位置识别
- [x] 局面评分
- [x] 候选动作筛选（候选动作 + 中心开局）

### Phase 3：Alpha-Beta 搜索
- [x] Negamax + Alpha-Beta 剪枝 + 迭代加深
- [x] 候选动作筛选、Move Ordering
- [x] Zobrist Hash（增量更新）、置换表（EXACT/LOWER/UPPER）
- [x] VCF 战术搜索（严格 win/no_win/unknown 三态）、搜索时间限制
- [x] AlphaBetaAgent 接入 Agent 接口与 Pygame 界面
- [x] 单元测试（搜索逻辑/哈希/置换表/VCF/工程质量/对局）

### Phase 4：神经网络（目标：轻量 Policy-Value 网络）
- [ ] PyTorch 轻量 ResNet 双头网络（Policy Head 225 输出 + Value Head 单输出）
- [ ] 统一训练数据格式（见 docs/MODEL_INTERFACE.md）
- [ ] 批量推理接口（见 docs/MODEL_INTERFACE.md，协议已设计）
- [ ] 生成训练数据、训练模型
- [ ] 逐步替换传统静态局面评分

### Phase 5：Self-Play
- [ ] 自动对弈、Replay Buffer、历史模型池、模型迭代
- [ ] （研究项见 docs/RESEARCH_ROADMAP.md：MCTS、蒸馏、课程学习等）

### Phase 6：完整游戏界面
- [x] Pygame 棋盘渲染（木质棋盘、网格线、星位、棋子立体效果）
- [x] 鼠标点击落子、悬停预览、最近落子高亮、获胜连线高亮
- [x] 侧边栏（玩家信息、对局状态、AI 信息、按钮）
- [x] 三种模式：双人对战、人机对战、AI 自动对战
- [x] 悔棋、重新开始、交换先手
- [x] AI 后台线程调度（不阻塞主线程），接入随机/战术/Alpha-Beta Agent
- [x] headless 单元测试
- [x] 接入 Alpha-Beta 搜索 Agent（Phase 3 完成），AI 信息栏展示搜索深度/评分/VCF/节点/NPS
- [ ] 接入神经网络 Agent（Phase 4 完成后）

### Phase 7：评测和优化
- [ ] 竞技场、版本对比、速度优化、棋力测试

## 架构重整（本轮完成）

### 已完成
- [x] 冻结项目基线（git 提交 6e79f73，20 文件 +1644 行）
- [x] 搜索性能诊断统计埋点（nodes/NPS/depth/candidate/VCF/TT命中率/叶节点估值/递归深度）
- [x] 有限时间搜索（0.5/1/3/5 秒预算，迭代加深 + 超时安全恢复）
- [x] VCF 独立节点预算（max_nodes，防无限递归）
- [x] 平局判断改计数器（O(1)）
- [x] 基准测试工具（benchmarks/benchmark.py）
- [x] 批量推理接口协议 + 训练数据格式设计（docs/MODEL_INTERFACE.md）

### 文档
- [x] docs/PROJECT_VISION.md（目标分层：长期/研究/立即做）
- [x] docs/RESEARCH_ROADMAP.md（7 个研究项）
- [x] docs/ARCHITECTURE_DECISIONS.md（架构决策 + 诊断结论）
- [x] docs/MODEL_INTERFACE.md（接口协议 + 训练数据格式）

### 诊断结论（重要）
- 叶节点估值（evaluate_board 全盘棋形扫描）占总耗时 25–44%，是最大瓶颈
- TT 命中率偏低（3.4%–6.5%），置换表加速作用未充分发挥
- NPS 稳定在 2500–4400（Python 纯实现上限）
- VCF 节点数少，不是瓶颈

## 环境检查记录（Phase 0）

- Python 3.13.14
- GPU：NVIDIA GeForce RTX 4070（8GB，CUDA 13.2，驱动 596.49）
- NumPy / PyTorch / Pygame / Pytest / Matplotlib：初始均未安装

## 开发纪律

1. 不一次性生成大量空壳文件
2. 每完成一个阶段必须执行测试
3. 核心模块必须有清晰接口和注释
4. 优先保证规则正确，再追求速度与复杂度
5. 不允许跳过必胜、必防等基本战术判断
6. 不过早引入 Transformer、分布式训练等不必要技术
7. 模型训练支持中断恢复
8. 不覆盖或删除已有项目文件
9. Bug 要定位原因修复，不通过关闭测试绕过
10. 测试必须使用真实执行结果

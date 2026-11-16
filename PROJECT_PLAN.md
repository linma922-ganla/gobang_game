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
- [ ] Negamax + Alpha-Beta + 迭代加深
- [ ] 候选动作筛选、Move Ordering
- [ ] Zobrist Hash、置换表
- [ ] VCF 战术搜索、搜索时间限制

### Phase 4：神经网络
- [ ] PyTorch Value Network（3×15×15 输入，[-1,1] 输出）
- [ ] 生成训练数据、训练模型
- [ ] 逐步替换传统静态局面评分

### Phase 5：Self-Play
- [ ] 自动对弈、Replay Buffer、历史模型池、模型迭代

### Phase 6：完整游戏界面
- [x] Pygame 棋盘渲染（木质棋盘、网格线、星位、棋子立体效果）
- [x] 鼠标点击落子、悬停预览、最近落子高亮、获胜连线高亮
- [x] 侧边栏（玩家信息、对局状态、AI 信息、按钮）
- [x] 三种模式：双人对战、人机对战、AI 自动对战
- [x] 悔棋、重新开始、交换先手
- [x] AI 后台线程调度（不阻塞主线程），接入随机/战术 Agent
- [x] headless 单元测试
- [ ] 接入 Alpha-Beta / 神经网络 Agent（Phase 3 / 4 完成后）

### Phase 7：评测和优化
- [ ] 竞技场、版本对比、速度优化、棋力测试

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

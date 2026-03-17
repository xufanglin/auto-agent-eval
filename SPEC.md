# Agent Eval — 项目规格定义

## 核心概念

### 1. Task（任务）

一个 Task 是一个**不可变的任务定义**，描述"要做什么"。

```
Task:
  id: string                    # 唯一标识，如 "django-11099"
  name: string                  # 人类可读名称
  description: string           # 任务描述（给人看的）
  prompt: string                # 给 Agent 的指令
  workspace_dir: Path           # 初始工作区目录（包含所有给 Agent 的文件）
  metadata:
    source: string              # 来源（swe-bench, custom, ...）
    category: string            # 分类（bugfix, coding, analysis, refactoring, ...）
    difficulty: string          # 难度（easy, medium, hard）
    expected_duration: string   # 预期耗时（5m, 1h, 4h, ...）
    tags: list[string]          # 标签
```

Task 不包含评估逻辑。Task 只回答"做什么"，不回答"做得怎样"。

### 2. Agent（被测 Agent）

一个 Agent 是一个**可执行的接口**，接收 prompt + workspace，产出修改后的 workspace。

```
Agent:
  id: string                    # 唯一标识，如 "claude-code-sonnet"
  name: string                  # 显示名称
  type: string                  # 类型（claude-code, cli, mock, ...）
  config:                       # 类型特定的配置
    model: string               # 模型（对 claude-code）
    command: string             # 命令（对 cli 类型）
    timeout: int                # 超时秒数
    isolation:                  # 隔离配置
      env_vars: dict            # 允许传递的环境变量
      system_prompt: string     # 覆盖的 system prompt
      settings_sources: string  # 配置源控制
```

Agent 的职责边界：
- 接收 prompt 和 workspace 路径
- 在 workspace 中执行操作
- 返回执行日志
- **不负责**环境准备和评估

### 3. Environment（运行环境）

Environment 负责**创建和管理隔离的工作空间**。

```
Environment:
  type: string                  # local, docker
  config:
    image: string               # Docker 镜像（docker 类型）
    keep: bool                  # 运行后是否保留工作区
    base_dir: Path              # 工作区父目录
```

Environment 的职责：
- 创建临时工作区
- 复制 Task 的初始文件到工作区
- 保存原始文件副本（用于 diff 检查）
- 运行结束后清理（除非 keep=true）

### 4. Metric（评估指标）

一个 Metric 是一个**单一维度的评估标准**。这是最关键的抽象。

```
Metric:
  id: string                    # 如 "tests_pass", "file_modified", "code_quality"
  name: string                  # 人类可读名称
  type: string                  # code_check | llm_judge
  weight: float                 # 在总分中的权重（0.0 - 1.0）
  config:                       # 类型特定的配置
    # code_check 类型：
    check_type: string          # command | file_exists | python_script
    command: string             # 要执行的命令
    script: string              # 要执行的 Python 脚本
    expect_exit: int            # 期望的退出码
    # llm_judge 类型：
    model: string               # 评判用的模型
    criteria: string            # 评判标准描述
    scale: [int, int]           # 评分范围，如 [0, 2]
  result_schema:
    score: float                # 0.0 - 1.0（归一化后）
    passed: bool                # 是否通过
    reason: string              # 评判理由
    raw_output: string          # 原始输出
```

### 5. EvalSpec（评估规格）

一个 EvalSpec 是一组 Metric 的集合，定义"怎么评"。

```
EvalSpec:
  metrics: list[Metric]         # 评估指标列表
  pass_threshold: float         # 通过阈值（默认 0.8）
  scoring: string               # weighted_average | all_pass | any_pass
```

### 6. EvalRun（一次评测运行）

一个 EvalRun 是 Task + Agent + Environment + EvalSpec 的一次组合执行。

```
EvalRun:
  id: string                    # 运行 ID（自动生成）
  task: Task
  agent: Agent
  environment: Environment
  eval_spec: EvalSpec
  status: pending | running | completed | failed
  result:
    score: float
    passed: bool
    metrics: list[MetricResult]
    duration_seconds: float
    agent_output: string
    timestamp: string
```

### 7. EvalSuite（评测套件）

一个 EvalSuite 是多个 EvalRun 的集合，用于批量评测。

```
EvalSuite:
  name: string
  runs: list[EvalRun]
  summary:
    total: int
    passed: int
    average_score: float
    by_category: dict[string, float]
    by_agent: dict[string, float]
```

## 目录结构

```
agent-eval/
├── tasks/                          # 任务库
│   └── {task-id}/
│       ├── task.yaml               # Task 定义
│       ├── eval.yaml               # EvalSpec 定义
│       └── workspace/              # 初始工作区文件
│           ├── ...                  # 真实文件，不是字符串
│
├── agents/                         # Agent 配置
│   ├── claude-code.yaml            # Claude Code 默认配置
│   ├── claude-code-opus.yaml       # Claude Code Opus 配置
│   └── mock.yaml                   # Mock Agent
│
├── src/agent_eval/
│   ├── models.py                   # 数据模型定义（Task, Agent, Metric, ...）
│   ├── environment.py              # Environment 实现
│   ├── agents.py                   # Agent 实现
│   ├── metrics.py                  # Metric 实现（CodeCheck, LLMJudge）
│   ├── runner.py                   # EvalRun 执行器
│   ├── loader.py                   # 从 YAML 加载配置
│   └── cli.py                      # CLI 入口
│
├── results/                        # 评测结果输出
│   └── {run-id}.json
│
└── pyproject.toml
```

## 使用方式

```bash
# 列出任务和 Agent
agent-eval list tasks
agent-eval list agents

# 运行评测
agent-eval run --agent claude-code --task django-11099
agent-eval run --agent claude-code                      # 所有任务
agent-eval run --agent claude-code --category bugfix    # 按分类筛选

# 对比多个 Agent
agent-eval run --agent claude-code --agent cursor --task django-11099

# 查看结果
agent-eval results
agent-eval results --run-id xxx
```

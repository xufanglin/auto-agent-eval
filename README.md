# Auto Agent Eval (AAE)

A pluggable framework for evaluating AI coding agents — **where agents judge agents**.

## Why "Agent-as-Judge"?

Most benchmarks use simple pass/fail tests. But real-world agent tasks — refactoring code, writing reports, analyzing data — have no single "correct answer". AAE goes beyond **LLM-as-Judge** (a single API call scoring text) to **Agent-as-Judge**: a full agent with tools, file access, and code execution capabilities that reviews another agent's work, just like a human reviewer would.

```mermaid
flowchart LR
    subgraph "Traditional Eval"
        T1[Agent Output] --> G1[Unit Tests<br/>pass / fail]
    end

    subgraph "LLM-as-Judge"
        T2[Agent Output] --> G2[Single LLM Call<br/>score 0-10]
    end

    subgraph "Agent-as-Judge (AAE)"
        T3[Agent Output<br/>+ Workspace<br/>+ Transcript] --> G3[Judge Agent<br/>reads files, runs code,<br/>reasons over evidence]
        G3 --> V[Structured Verdict<br/>per-dimension scores<br/>+ reasoning]
    end
```

The judge agent doesn't just read the output — it can inspect the workspace, run the code, diff against originals, and reason about quality across multiple dimensions. This mirrors how a senior engineer reviews a pull request: not just "does it compile?" but "is this the right approach?"

## How It Works

```mermaid
flowchart TB
    subgraph Define["① Define"]
        TASK[📋 Task<br/>prompt + workspace + eval spec]
        AGENT[🤖 Agent Under Test<br/>Claude Code / Cursor / any CLI]
    end

    subgraph Execute["② Execute"]
        ENV[📦 Sandbox<br/>isolated workspace copy]
        RUN[Agent runs task<br/>modifies files]
    end

    subgraph Evaluate["③ Evaluate"]
        CC[✅ Code Checks<br/>deterministic]
        AJ[🧠 Agent Judge<br/>agentic evaluation]
        COMP[⚖️ Composite Score<br/>weighted combination]
    end

    subgraph Archive["④ Archive"]
        WS[📁 Workspace snapshot<br/>before & after]
        LOG[📝 Agent transcript]
        SCORE[📊 Per-metric scores<br/>+ judge reasoning]
    end

    TASK --> ENV
    AGENT --> RUN
    ENV --> RUN
    RUN --> CC
    RUN --> AJ
    CC --> COMP
    AJ --> COMP
    COMP --> WS
    COMP --> LOG
    COMP --> SCORE
```

Every run archives the complete workspace (before and after), agent output transcript, and detailed per-metric scores with judge reasoning — enabling human review of any result.

## Evaluation Philosophy

Inspired by [Anthropic's eval framework](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents), AAE is built around these principles:

### Three Layers of Grading

| Layer | What | When to Use |
|-------|------|-------------|
| **Code Check** | pytest, file existence, script output, exit codes | Verifiable outcomes with clear pass/fail |
| **Agent Judge** | An agent that reads files, runs code, and reasons | Subjective quality, design decisions, completeness |
| **Human Review** | Browse workspace + transcript in web UI | Calibration, edge cases, final sign-off |

```mermaid
flowchart TB
    W[Agent Workspace] --> C{Composite Evaluator}

    C --> D["Code Checks (deterministic)<br/>weight: configurable"]
    C --> A["Agent Judge (agentic)<br/>weight: configurable"]

    D --> D1["✅ tests pass"]
    D --> D2["✅ file exists"]
    D --> D3["✅ output valid"]

    A --> A1["📝 accuracy<br/><i>reads CSV, verifies numbers</i>"]
    A --> A2["📝 completeness<br/><i>checks all sections present</i>"]
    A --> A3["📝 insight<br/><i>evaluates reasoning quality</i>"]

    D1 & D2 & D3 --> S["Final Score + Reasoning"]
    A1 & A2 & A3 --> S

    S --> H["👤 Human Review<br/><i>workspace + transcript in web UI</i>"]
```

### Outcome vs Transcript

AAE evaluates both **what the agent produced** (outcome) and **how it got there** (transcript):

- **Outcome**: Did the code pass tests? Does the report contain correct numbers?
- **Transcript**: What did the agent do? How long did it take? What tools did it use?

Both are archived for every run, because a passing score doesn't tell the whole story — you need to read the transcripts.

### Capability vs Regression

- **Capability evals** start at low pass rates — tasks the agent struggles with, giving you a hill to climb
- **Regression evals** should stay near 100% — protecting against backsliding when you change prompts or models

As capability evals reach high pass rates, they graduate into the regression suite.

## Features

- **Agent-as-Judge** — judge agents that read files, run code, and reason over evidence
- **Code checks** — pytest, file existence, script output, custom Python scripts
- **Composite scoring** — weighted combination of code checks + agent judges
- **Full archival** — workspaces (before & after), agent transcripts, judge reasoning
- **Web dashboard** — sidebar navigation, drill into metrics, browse workspace files
- **Pluggable** — add tasks and agents via YAML, no code changes needed

## Quick Start

```bash
uv sync

# List available tasks and agents
uv run agent-eval list

# Run Claude Code on all tasks
uv run agent-eval run --agent claude-code

# Run on a specific task
uv run agent-eval run django-11099 --agent claude-code

# Compare agents
uv run agent-eval run -a claude-code -a claude-code-opus

# Filter by category
uv run agent-eval run --agent claude-code --category bugfix

# View results in terminal
uv run agent-eval results

# Start web dashboard
cd web && npm install && npm run build && cd ..
uv run agent-eval serve --port 9090
```

## Architecture

```mermaid
graph TB
    subgraph CLI["CLI (agent-eval)"]
        RUN[run]
        LIST[list]
        RES[results]
        SERVE[serve]
    end

    subgraph Core
        RUN --> RUNNER[Runner]
        RUNNER --> LOADER[Loader<br/>YAML → models]
        RUNNER --> ENV[Environment<br/>sandbox setup]
        RUNNER --> AG[Agent<br/>execute task]
        RUNNER --> MET[Metrics<br/>code check + agent judge]
    end

    subgraph Storage
        LOADER --> TASKS[(tasks/)]
        LOADER --> AGENTS[(agents/)]
        RUNNER --> RESULTS[(results/<br/>scores + workspaces<br/>+ transcripts)]
    end

    subgraph Web["Web Dashboard"]
        SERVE --> SERVER[API Server]
        SERVER --> RESULTS
        SERVER --> SPA[React SPA<br/>sidebar + detail view<br/>+ file browser]
    end
```

## Results Structure

Every run is fully archived for human review:

```
results/20260318_070812_claude-code/
├── summary.json                        # overall scores, by-agent, by-category
├── csv-stats.json                      # per-task metric details + judge reasoning
├── django-11099.json
├── workspaces/
│   └── claude-code/
│       ├── csv-stats/
│       │   ├── .originals/             # files before agent ran (for diff)
│       │   ├── stats.py               # files after agent ran
│       │   └── test_data.csv
│       └── django-11099/
│           └── validators.py
└── logs/
    └── claude-code/
        ├── csv-stats.log              # full agent transcript
        └── django-11099.log
```

## Adding a Task

```
tasks/my-task/
├── task.yaml           # prompt + metadata
├── eval.yaml           # evaluation spec
└── workspace/          # initial files given to the agent
```

**task.yaml:**
```yaml
name: my-task
prompt: |
  Fix the bug in main.py. Run `python test.py` to verify.
metadata:
  category: bugfix
  difficulty: easy
```

**eval.yaml** — combine code checks and agent judges:
```yaml
evaluator:
  type: composite
  evaluators:
    - type: code
      weight: 0.6
      checks:
        - name: "tests pass"
          type: command
          cmd: "python test.py"
          expect_exit: 0
    - type: llm_judge
      weight: 0.4
      rubric:
        quality: "Is the fix clean and minimal?"
        correctness: "Does it address the root cause, not just the symptom?"
```

## Adding an Agent

```yaml
# agents/my-agent.yaml
name: My Agent
type: cli
config:
  command: my-agent-cli
  timeout: 300
```

Supported types: `claude-code`, `cli`, `mock`, `script`

## Included Tasks

| Task | Category | Difficulty | Description |
|------|----------|------------|-------------|
| csv-stats | data | easy | Fix a CSV stats script that crashes on non-numeric data |
| django-11099 | bugfix | easy | Fix URLValidator to accept IPv6 URLs (from SWE-bench) |
| wordfreq | coding | easy | Build a word frequency CLI tool from scratch |
| refactor | refactoring | medium | Refactor messy code while preserving behavior |
| sales-report | analysis | medium | Analyze CSV data and write a Markdown report |

## Tech Stack

- **Backend**: Python 3.14, PyYAML, stdlib HTTP server
- **Frontend**: Vite + React + TypeScript
- **Package manager**: uv

## References

- [Demystifying Evals for AI Agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) — Anthropic's guide to agent evaluation
- [Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) — Anthropic's agent design patterns
- [SWE-bench](https://www.swebench.com/) — coding agent benchmark
- [τ-bench](https://github.com/sierra-research/tau2-bench) — conversational agent benchmark

## License

MIT

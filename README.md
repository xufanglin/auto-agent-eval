# agent-eval

Pluggable AI Agent evaluation framework. Evaluate coding agents (Claude Code, Cursor, etc.) on reproducible tasks with automated scoring.

## Quick Start

```bash
uv sync

# List available tasks and agents
uv run agent-eval list

# Dry run with mock agent
uv run agent-eval run --mock

# Evaluate Claude Code on a specific task
uv run agent-eval run django-11099 --agent claude-code

# Evaluate on all tasks
uv run agent-eval run --agent claude-code

# Compare agents
uv run agent-eval run -a claude-code -a claude-code-opus -o results/compare.json

# Filter by category
uv run agent-eval run --agent claude-code --category bugfix
```

## Architecture

Four pluggable components:

- **Task** (`tasks/{id}/`) — what to do (task.yaml + workspace/ + eval.yaml)
- **Agent** (`agents/{id}.yaml`) — who does it (claude-code, cli, mock, script)
- **Environment** — where to run (local sandbox, docker)
- **Metric** — how to judge (code_check, llm_judge)

## Adding a Task

```
tasks/my-task/
├── task.yaml           # prompt + metadata
├── eval.yaml           # metrics definition
└── workspace/          # files given to the agent
    └── ...
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

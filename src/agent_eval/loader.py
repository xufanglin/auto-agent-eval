"""Load tasks, agents, and eval specs from YAML files."""

from __future__ import annotations

from pathlib import Path

import yaml

from agent_eval.models import AgentConfig, EnvironmentConfig, EvalSpec, Metric, Task

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if not (PROJECT_ROOT / "tasks").exists():
    PROJECT_ROOT = Path.cwd()

TASKS_DIR = PROJECT_ROOT / "tasks"
AGENTS_DIR = PROJECT_ROOT / "agents"
RESULTS_DIR = PROJECT_ROOT / "results"


# ── Tasks ───────────────────────────────────────────────

def list_tasks(tasks_dir: Path | None = None) -> list[str]:
    d = tasks_dir or TASKS_DIR
    if not d.exists():
        return []
    return sorted(
        p.name for p in d.iterdir()
        if p.is_dir() and (p / "task.yaml").exists()
    )


def load_task(task_id: str, tasks_dir: Path | None = None) -> Task:
    d = (tasks_dir or TASKS_DIR) / task_id
    cfg = yaml.safe_load((d / "task.yaml").read_text())
    return Task(
        id=task_id,
        name=cfg.get("name", task_id),
        description=cfg.get("description", cfg.get("prompt", "")[:100]),
        prompt=cfg["prompt"],
        workspace_dir=d / "workspace",
        metadata=cfg.get("metadata", {}),
    )


def load_eval_spec(task_id: str, tasks_dir: Path | None = None) -> EvalSpec:
    d = (tasks_dir or TASKS_DIR) / task_id
    cfg = yaml.safe_load((d / "eval.yaml").read_text())

    eval_cfg = cfg.get("evaluator", cfg)
    metrics = _parse_metrics(eval_cfg, prefix=task_id)

    return EvalSpec(
        metrics=metrics,
        pass_threshold=cfg.get("pass_threshold", 0.8),
        scoring=cfg.get("scoring", "weighted_average"),
    )


def _parse_metrics(cfg: dict, prefix: str = "") -> list[Metric]:
    """Parse metrics from eval.yaml config."""
    metrics = []

    if cfg.get("type") == "composite":
        for i, sub in enumerate(cfg.get("evaluators", [])):
            sub_metrics = _parse_metrics(sub, prefix=prefix)
            weight = sub.get("weight", 1.0)
            for m in sub_metrics:
                m.weight = weight
            metrics.extend(sub_metrics)
        return metrics

    if cfg.get("type") == "code":
        for check in cfg.get("checks", []):
            check_type = check.get("type", "command")
            metric_config = dict(check)
            # Normalize check_type naming
            type_map = {"python": "python_script", "file_exists": "file_exists", "command": "command"}
            metric_config["check_type"] = type_map.get(check_type, check_type)
            # Remap YAML fields to metric config
            if "cmd" in check:
                metric_config["command"] = check["cmd"]
            if "script" in check:
                metric_config["script"] = check["script"]

            metrics.append(Metric(
                id=f"{prefix}:{check.get('name', f'check_{len(metrics)}')}",
                name=check.get("name", f"check_{len(metrics)}"),
                type="code_check",
                config=metric_config,
            ))
        return metrics

    if cfg.get("type") == "llm_judge":
        rubric = cfg.get("rubric", {})
        for dim, criteria in rubric.items():
            metrics.append(Metric(
                id=f"{prefix}:llm:{dim}",
                name=f"llm_judge:{dim}",
                type="llm_judge",
                config={
                    "model": cfg.get("model", "claude"),
                    "criteria": criteria,
                    "scale": cfg.get("scale", [0, 2]),
                },
            ))
        return metrics

    return metrics


# ── Agents ──────────────────────────────────────────────

def list_agents(agents_dir: Path | None = None) -> list[str]:
    d = agents_dir or AGENTS_DIR
    if not d.exists():
        return []
    return sorted(p.stem for p in d.glob("*.yaml"))


def load_agent_config(agent_id: str, agents_dir: Path | None = None) -> AgentConfig:
    d = agents_dir or AGENTS_DIR
    path = d / f"{agent_id}.yaml"
    cfg = yaml.safe_load(path.read_text())
    return AgentConfig(
        id=agent_id,
        name=cfg.get("name", agent_id),
        type=cfg.get("type", "cli"),
        config=cfg.get("config", {}),
    )


# ── Environment ─────────────────────────────────────────

def load_environment_config(cfg: dict | None = None) -> EnvironmentConfig:
    if not cfg:
        return EnvironmentConfig(type="local")
    return EnvironmentConfig(
        type=cfg.get("type", "local"),
        config=cfg.get("config", {}),
    )

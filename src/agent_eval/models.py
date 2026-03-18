"""Data models for the evaluation framework."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal


@dataclass
class Task:
    id: str
    name: str
    description: str
    prompt: str
    workspace_dir: Path
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def category(self) -> str:
        return self.metadata.get("category", "")

    @property
    def difficulty(self) -> str:
        return self.metadata.get("difficulty", "")


@dataclass
class AgentConfig:
    id: str
    name: str
    type: str  # claude-code, cli, mock
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class EnvironmentConfig:
    type: str = "local"  # local, docker
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class Metric:
    id: str
    name: str
    type: str  # code_check, llm_judge
    weight: float = 1.0
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvalSpec:
    metrics: list[Metric]
    pass_threshold: float = 0.8
    scoring: str = "weighted_average"  # weighted_average, all_pass, any_pass


@dataclass
class MetricResult:
    metric_id: str
    metric_name: str
    score: float  # 0.0 - 1.0 normalized
    passed: bool
    reason: str = ""
    raw_output: str = ""


@dataclass
class RunResult:
    score: float
    passed: bool
    metrics: list[MetricResult]
    duration_seconds: float
    agent_output_length: int = 0
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class EvalRun:
    id: str
    task_id: str
    agent_id: str
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    result: RunResult | None = None
    workspace: Path | None = None
    agent_output: str = ""

    @staticmethod
    def create(task_id: str, agent_id: str) -> EvalRun:
        return EvalRun(
            id=uuid.uuid4().hex[:12],
            task_id=task_id,
            agent_id=agent_id,
        )

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("workspace", None)
        d.pop("agent_output", None)
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


@dataclass
class SuiteSummary:
    total: int
    passed: int
    average_score: float
    by_category: dict[str, float]
    by_agent: dict[str, float]


@dataclass
class EvalSuite:
    name: str
    runs: list[EvalRun] = field(default_factory=list)

    def summary(self, tasks: dict[str, Task] | None = None) -> SuiteSummary:
        completed = [r for r in self.runs if r.status == "completed" and r.result]
        if not completed:
            return SuiteSummary(0, 0, 0.0, {}, {})

        scores = [r.result.score for r in completed]
        passed = sum(1 for r in completed if r.result.passed)

        by_agent: dict[str, list[float]] = {}
        by_category: dict[str, list[float]] = {}
        for r in completed:
            by_agent.setdefault(r.agent_id, []).append(r.result.score)
            if tasks and r.task_id in tasks:
                cat = tasks[r.task_id].category or "other"
                by_category.setdefault(cat, []).append(r.result.score)

        return SuiteSummary(
            total=len(completed),
            passed=passed,
            average_score=sum(scores) / len(scores),
            by_category={k: sum(v) / len(v) for k, v in by_category.items()},
            by_agent={k: sum(v) / len(v) for k, v in by_agent.items()},
        )

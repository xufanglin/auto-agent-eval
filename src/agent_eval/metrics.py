"""Metric implementations: code checks and LLM judges."""

from __future__ import annotations

import json
import subprocess
import sys
from abc import ABC, abstractmethod
from pathlib import Path

from agent_eval.models import EvalSpec, Metric, MetricResult


class MetricEvaluator(ABC):
    """Evaluates a single metric against workspace artifacts."""

    def __init__(self, metric: Metric):
        self.metric = metric

    @abstractmethod
    def evaluate(self, workspace: Path) -> MetricResult:
        """Evaluate and return result."""


class CodeCheckEvaluator(MetricEvaluator):
    """Deterministic code-based check."""

    def evaluate(self, workspace: Path) -> MetricResult:
        cfg = self.metric.config
        check_type = cfg.get("check_type", "command")

        if check_type == "file_exists":
            return self._check_file_exists(workspace, cfg)
        if check_type == "command":
            return self._check_command(workspace, cfg)
        if check_type == "python_script":
            return self._check_python(workspace, cfg)

        return MetricResult(
            metric_id=self.metric.id, metric_name=self.metric.name,
            score=0.0, passed=False, reason=f"Unknown check_type: {check_type}",
        )

    def _check_file_exists(self, workspace: Path, cfg: dict) -> MetricResult:
        path = workspace / cfg["path"]
        exists = path.exists()
        return MetricResult(
            metric_id=self.metric.id, metric_name=self.metric.name,
            score=1.0 if exists else 0.0, passed=exists,
            reason=f"{'Found' if exists else 'Missing'}: {cfg['path']}",
        )

    def _check_command(self, workspace: Path, cfg: dict) -> MetricResult:
        try:
            r = subprocess.run(
                cfg["command"], shell=True, cwd=workspace,
                capture_output=True, text=True,
                timeout=cfg.get("timeout", 120),
            )
            expected = cfg.get("expect_exit", 0)
            passed = r.returncode == expected
            output = (r.stdout + r.stderr).strip()
            return MetricResult(
                metric_id=self.metric.id, metric_name=self.metric.name,
                score=1.0 if passed else 0.0, passed=passed,
                reason=output[-300:] if output else f"exit={r.returncode}",
                raw_output=output,
            )
        except subprocess.TimeoutExpired:
            return MetricResult(
                metric_id=self.metric.id, metric_name=self.metric.name,
                score=0.0, passed=False, reason="Timeout",
            )

    def _check_python(self, workspace: Path, cfg: dict) -> MetricResult:
        try:
            local_vars: dict = {"__builtins__": __builtins__, "workspace": workspace}
            exec(cfg["script"], local_vars)
            score = float(local_vars.get("score", 0.0))
            reason = str(local_vars.get("reason", ""))
            return MetricResult(
                metric_id=self.metric.id, metric_name=self.metric.name,
                score=score, passed=score > 0.5, reason=reason,
            )
        except Exception as e:
            return MetricResult(
                metric_id=self.metric.id, metric_name=self.metric.name,
                score=0.0, passed=False, reason=str(e),
            )


class LLMJudgeEvaluator(MetricEvaluator):
    """LLM-based evaluation."""

    def evaluate(self, workspace: Path) -> MetricResult:
        cfg = self.metric.config
        context = self._gather_context(workspace)
        prompt = self._build_prompt(cfg, context)

        try:
            r = subprocess.run(
                ["claude", "--print", "--no-session-persistence"],
                input=prompt, capture_output=True, text=True, timeout=180,
            )
            return self._parse_response(r.stdout, cfg)
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            return MetricResult(
                metric_id=self.metric.id, metric_name=self.metric.name,
                score=0.0, passed=False, reason=f"LLM judge failed: {e}",
            )

    def _gather_context(self, workspace: Path) -> str:
        parts = []
        for f in sorted(workspace.rglob("*")):
            if f.is_file() and not f.name.startswith(".") and f.stat().st_size < 50000:
                try:
                    parts.append(f"--- {f.relative_to(workspace)} ---\n{f.read_text()}")
                except UnicodeDecodeError:
                    pass
        return "\n\n".join(parts)

    def _build_prompt(self, cfg: dict, context: str) -> str:
        criteria = cfg.get("criteria", "Evaluate the quality of the work.")
        scale = cfg.get("scale", [0, 2])
        return (
            f"You are an evaluation judge.\n\n"
            f"CRITERIA: {criteria}\n"
            f"SCALE: {scale[0]} to {scale[1]}\n\n"
            f"ARTIFACTS:\n{context}\n\n"
            f'Respond in JSON: {{"score": <number>, "reason": "<explanation>"}}'
        )

    def _parse_response(self, response: str, cfg: dict) -> MetricResult:
        try:
            start = response.index("{")
            end = response.rindex("}") + 1
            data = json.loads(response[start:end])
            scale = cfg.get("scale", [0, 2])
            raw_score = float(data.get("score", 0))
            normalized = raw_score / scale[1] if scale[1] > 0 else 0.0
            return MetricResult(
                metric_id=self.metric.id, metric_name=self.metric.name,
                score=normalized, passed=normalized > 0.5,
                reason=data.get("reason", ""),
                raw_output=response,
            )
        except (ValueError, json.JSONDecodeError):
            return MetricResult(
                metric_id=self.metric.id, metric_name=self.metric.name,
                score=0.0, passed=False,
                reason=f"Failed to parse: {response[:200]}",
            )


def create_evaluator(metric: Metric) -> MetricEvaluator:
    evaluators = {
        "code_check": CodeCheckEvaluator,
        "llm_judge": LLMJudgeEvaluator,
    }
    cls = evaluators.get(metric.type)
    if not cls:
        raise ValueError(f"Unknown metric type: {metric.type}")
    return cls(metric)


def evaluate_all(workspace: Path, spec: EvalSpec) -> list[MetricResult]:
    """Run all metrics in an EvalSpec against a workspace."""
    results = []
    for metric in spec.metrics:
        evaluator = create_evaluator(metric)
        results.append(evaluator.evaluate(workspace))
    return results


def compute_score(results: list[MetricResult], spec: EvalSpec) -> tuple[float, bool]:
    """Compute overall score from metric results."""
    if not results:
        return 0.0, False

    if spec.scoring == "all_pass":
        passed = all(r.passed for r in results)
        return (1.0 if passed else 0.0), passed

    if spec.scoring == "any_pass":
        passed = any(r.passed for r in results)
        return (1.0 if passed else 0.0), passed

    # weighted_average
    total_weight = sum(m.weight for m in spec.metrics)
    if total_weight == 0:
        return 0.0, False

    score = sum(
        r.score * m.weight
        for r, m in zip(results, spec.metrics)
    ) / total_weight

    return score, score >= spec.pass_threshold

"""EvalRun executor: orchestrates task → environment → agent → metrics."""

from __future__ import annotations

import re
import time

from agent_eval.agents import Agent
from agent_eval.environment import Environment
from agent_eval.metrics import compute_score, evaluate_all
from agent_eval.models import EvalRun, EvalSpec, RunResult, Task


def _parse_cost(agent_output: str) -> float | None:
    """Extract credit cost from agent output.

    Supports:
    - kiro:   '▸ Credits: 0.33'
    - copilot: 'AI Credits <ansi>4.71'
    """
    # Strip ANSI escape codes before matching
    clean = re.sub(r'\x1b\[[0-9;]*m', '', agent_output)
    for pattern in [
        r'Credits:\s*([\d.]+)',   # kiro: ▸ Credits: 0.33
        r'AI Credits\s+([\d.]+)', # copilot: AI Credits 4.71
    ]:
        m = re.search(pattern, clean)
        if m:
            return float(m.group(1))
    return None


def execute_run(
    run: EvalRun,
    task: Task,
    agent: Agent,
    environment: Environment,
    eval_spec: EvalSpec,
) -> EvalRun:
    """Execute a single evaluation run. Mutates and returns the EvalRun.

    NOTE: Does NOT call environment.cleanup(). Caller is responsible for
    cleaning up after archiving the workspace.
    """
    run.status = "running"
    workspace = environment.setup(task)
    run.workspace = workspace

    try:
        start = time.time()
        agent_output = agent.run(task.prompt, workspace)
        duration = time.time() - start

        run.agent_output = agent_output

        metric_results = evaluate_all(workspace, eval_spec)
        score, passed = compute_score(metric_results, eval_spec)

        cost = _parse_cost(agent_output)
        credit_price = agent.config.config.get("credit_price")
        cost_usd = round(cost * credit_price, 4) if cost is not None and credit_price else None

        run.result = RunResult(
            score=score,
            passed=passed,
            metrics=metric_results,
            duration_seconds=round(duration, 2),
            agent_output_length=len(agent_output),
            cost=cost,
            cost_usd=cost_usd,
        )
        run.status = "completed"

    except Exception as e:
        run.agent_output = ""
        run.result = RunResult(
            score=0.0, passed=False, metrics=[],
            duration_seconds=0.0,
        )
        run.status = "failed"
        print(f"  ❌ Run failed: {e}")

    return run

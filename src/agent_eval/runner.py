"""EvalRun executor: orchestrates task → environment → agent → metrics."""

from __future__ import annotations

import time

from agent_eval.agents import Agent
from agent_eval.environment import Environment
from agent_eval.metrics import compute_score, evaluate_all
from agent_eval.models import EvalRun, EvalSpec, RunResult, Task


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

        run.result = RunResult(
            score=score,
            passed=passed,
            metrics=metric_results,
            duration_seconds=round(duration, 2),
            agent_output_length=len(agent_output),
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

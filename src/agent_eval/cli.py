"""CLI entry point."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from agent_eval.agents import create_agent
from agent_eval.environment import create_environment
from agent_eval.loader import (
    RESULTS_DIR,
    list_agents, list_tasks, load_agent_config, load_environment_config,
    load_eval_spec, load_task,
)
from agent_eval.models import EvalRun, EvalSuite
from agent_eval.runner import execute_run


# ── Output formatting ───────────────────────────────────

def print_run(run: EvalRun) -> None:
    r = run.result
    if not r:
        print(f"  {run.task_id}: no result")
        return

    status = "✅ PASS" if r.passed else "⚠️  PARTIAL" if r.score >= 0.5 else "❌ FAIL"
    print(f"\n{'='*60}")
    print(f"Task:  {run.task_id}")
    print(f"Agent: {run.agent_id}")
    print(f"Score: {r.score:.2f}  {status}")
    print(f"Time:  {r.duration_seconds:.1f}s")
    print(f"{'─'*60}")
    for m in r.metrics:
        icon = "✅" if m.passed else "❌"
        reason = m.reason.strip().split("\n")[0][:80] if m.reason else ""
        print(f"  {icon} {m.metric_name}")
        if reason:
            print(f"     {reason}")
    print(f"{'='*60}")


def print_summary(suite: EvalSuite, tasks: dict) -> None:
    s = suite.summary(tasks)
    print(f"\n{'='*60}")
    print(f"SUITE: {suite.name}")
    print(f"{'─'*60}")

    for run in suite.runs:
        if run.result:
            bar = "█" * int(run.result.score * 20) + "░" * (20 - int(run.result.score * 20))
            label = f"{run.agent_id}/{run.task_id}"
            print(f"  {label:40s} {bar} {run.result.score:.0%}")

    print(f"{'─'*60}")
    if s.by_agent:
        for agent_id, score in s.by_agent.items():
            print(f"  Agent {agent_id:30s} avg: {score:.0%}")
    if s.by_category:
        for cat, score in s.by_category.items():
            print(f"  Category {cat:27s} avg: {score:.0%}")
    print(f"{'─'*60}")
    print(f"  {'OVERALL':40s} {s.average_score:.0%}  ({s.passed}/{s.total} passed)")
    print(f"{'='*60}")


# ── Results I/O ─────────────────────────────────────────

def _save_results(suite: EvalSuite, tasks: dict, agent_ids: list[str], output: str | None) -> None:
    """Save results to structured directory layout.

    Layout:
        results/{timestamp}_{agents}/
            summary.json        — suite-level overview
            {task_id}.json      — per-task detail
    """
    if output:
        # Explicit -o: write single file (backward compat)
        p = Path(output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(
            {"suite": suite.name, "runs": [r.to_dict() for r in suite.runs]},
            indent=2, ensure_ascii=False,
        ))
        print(f"\nResults saved to {output}")
        return

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    agents_label = "+".join(sorted(set(agent_ids)))
    run_dir = RESULTS_DIR / f"{ts}_{agents_label}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Per-task files
    for run in suite.runs:
        (run_dir / f"{run.task_id}.json").write_text(
            json.dumps(run.to_dict(), indent=2, ensure_ascii=False)
        )

    # Summary
    s = suite.summary(tasks)
    summary = {
        "suite": suite.name,
        "timestamp": ts,
        "agents": sorted(set(agent_ids)),
        "tasks": [r.task_id for r in suite.runs],
        "overall": {
            "score": round(s.average_score, 4),
            "passed": s.passed,
            "total": s.total,
        },
        "by_agent": {k: round(v, 4) for k, v in s.by_agent.items()},
        "by_category": {k: round(v, 4) for k, v in s.by_category.items()},
        "runs": [
            {
                "task": r.task_id,
                "agent": r.agent_id,
                "score": round(r.result.score, 4) if r.result else 0,
                "passed": r.result.passed if r.result else False,
                "duration": r.result.duration_seconds if r.result else 0,
                "status": r.status,
            }
            for r in suite.runs
        ],
    }
    (run_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False)
    )
    print(f"\nResults saved to {run_dir}/")


def _load_result_dirs() -> list[Path]:
    """List all result directories, newest first."""
    if not RESULTS_DIR.exists():
        return []
    return sorted(
        (d for d in RESULTS_DIR.iterdir() if d.is_dir() and (d / "summary.json").exists()),
        reverse=True,
    )


# ── Commands ────────────────────────────────────────────

def cmd_list(args):
    if args.what in ("tasks", "all"):
        print("Tasks:")
        for tid in list_tasks():
            task = load_task(tid)
            print(f"  {tid:25s} [{task.category:12s}] [{task.difficulty}]")

    if args.what in ("agents", "all"):
        print("Agents:")
        for aid in list_agents():
            cfg = load_agent_config(aid)
            print(f"  {aid:25s} [{cfg.type}]")


def cmd_run(args):
    available_tasks = list_tasks()
    task_ids = args.tasks if args.tasks else available_tasks
    if args.category:
        task_ids = [
            tid for tid in task_ids
            if load_task(tid).category == args.category
        ]

    agent_ids = args.agent if args.agent else ["mock" if args.mock else "claude-code"]

    suite = EvalSuite(name=args.name or "eval")
    tasks = {}
    env_config = load_environment_config({"config": {"keep": args.keep_workspace}})

    for agent_id in agent_ids:
        agent_config = load_agent_config(agent_id)
        agent = create_agent(agent_config)

        for task_id in task_ids:
            if task_id not in available_tasks:
                print(f"⚠️  Unknown task: {task_id}")
                continue

            task = load_task(task_id)
            tasks[task_id] = task
            eval_spec = load_eval_spec(task_id)
            env = create_environment(env_config)

            run = EvalRun.create(task_id=task_id, agent_id=agent_id)
            print(f"\n▶ Running: {agent_id} / {task_id} ({task.category})")

            execute_run(run, task, agent, env, eval_spec)
            print_run(run)
            suite.runs.append(run)

    if suite.runs:
        print_summary(suite, tasks)
        _save_results(suite, tasks, agent_ids, args.output)


def cmd_results(args):
    dirs = _load_result_dirs()
    if not dirs:
        print("No results found.")
        return

    if args.run_id:
        matches = [d for d in dirs if args.run_id in d.name]
        if not matches:
            print(f"No results matching '{args.run_id}'")
            return
        # Show detail for matched run
        for d in matches:
            summary = json.loads((d / "summary.json").read_text())
            print(f"\n{'='*60}")
            print(f"Run:    {d.name}")
            print(f"Suite:  {summary['suite']}")
            print(f"Agents: {', '.join(summary['agents'])}")
            print(f"Score:  {summary['overall']['score']:.0%}  ({summary['overall']['passed']}/{summary['overall']['total']} passed)")
            print(f"{'─'*60}")
            for r in summary["runs"]:
                icon = "✅" if r["passed"] else "❌"
                print(f"  {icon} {r['agent']:20s} {r['task']:20s} {r['score']:.0%}  {r['duration']:.0f}s")
            print(f"{'='*60}")
        return

    # List all runs
    print(f"{'Run':50s} {'Score':>8s} {'Pass':>8s}")
    print("─" * 70)
    for d in dirs:
        summary = json.loads((d / "summary.json").read_text())
        o = summary["overall"]
        agents = "+".join(summary["agents"])
        print(f"  {d.name:48s} {o['score']:.0%}  {o['passed']}/{o['total']}")


def main():
    parser = argparse.ArgumentParser(
        prog="agent-eval",
        description="Pluggable AI Agent Evaluation Framework",
    )
    sub = parser.add_subparsers(dest="command")

    # list
    p_list = sub.add_parser("list", help="List available tasks and agents")
    p_list.add_argument("what", nargs="?", default="all", choices=["tasks", "agents", "all"])
    p_list.set_defaults(func=cmd_list)

    # run
    p_run = sub.add_parser("run", help="Run evaluation")
    p_run.add_argument("tasks", nargs="*", help="Task IDs (default: all)")
    p_run.add_argument("--agent", "-a", action="append", help="Agent ID (repeatable)")
    p_run.add_argument("--category", "-c", help="Filter tasks by category")
    p_run.add_argument("--mock", action="store_true", help="Use mock agent")
    p_run.add_argument("--name", "-n", help="Suite name")
    p_run.add_argument("--output", "-o", help="Save results to single JSON file (legacy)")
    p_run.add_argument("--keep-workspace", "-k", action="store_true")
    p_run.set_defaults(func=cmd_run)

    # results
    p_res = sub.add_parser("results", help="View past results")
    p_res.add_argument("run_id", nargs="?", help="Filter by run directory name")
    p_res.set_defaults(func=cmd_results)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()

"""Agent implementations."""

from __future__ import annotations

import os
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

from agent_eval.models import AgentConfig


class Agent(ABC):
    """Executes a task in a workspace."""

    def __init__(self, config: AgentConfig):
        self.config = config

    @property
    def id(self) -> str:
        return self.config.id

    @property
    def name(self) -> str:
        return self.config.name

    @abstractmethod
    def run(self, prompt: str, workspace: Path) -> str:
        """Run the agent, return output log."""


class ClaudeCodeAgent(Agent):
    """Claude Code CLI with environment isolation for reproducible eval."""

    def run(self, prompt: str, workspace: Path) -> str:
        cfg = self.config.config
        isolation = cfg.get("isolation", {})

        cmd = [
            "claude",
            "--print",
            "--no-session-persistence",
            "--permission-mode", "acceptEdits",
            "--setting-sources", isolation.get("settings_sources", "user"),
            "--system-prompt", isolation.get(
                "system_prompt",
                "You are a coding assistant. Complete the task. Do not ask questions.",
            ),
        ]
        if model := cfg.get("model"):
            cmd.extend(["--model", model])

        allowed_vars = isolation.get("env_vars", [
            "HOME", "PATH", "TMPDIR",
            "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL",
            "ANTHROPIC_API_KEY", "ANTHROPIC_MODEL",
            "CLAUDE_CODE_USE_BEDROCK",
            "AWS_PROFILE", "AWS_REGION",
            "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY",
        ])
        clean_env = {k: os.environ[k] for k in allowed_vars if k in os.environ}

        result = subprocess.run(
            cmd, cwd=workspace, env=clean_env,
            input=prompt, capture_output=True, text=True,
            timeout=cfg.get("timeout", 600),
        )
        return result.stdout + result.stderr


class CLIAgent(Agent):
    """Generic CLI agent."""

    def run(self, prompt: str, workspace: Path) -> str:
        cfg = self.config.config
        command = cfg["command"]
        if isinstance(command, str):
            command = command.split()

        result = subprocess.run(
            [*command, prompt], cwd=workspace,
            capture_output=True, text=True,
            timeout=cfg.get("timeout", 600),
        )
        return result.stdout + result.stderr


class MockAgent(Agent):
    """Does nothing — for testing the framework."""

    def run(self, prompt: str, workspace: Path) -> str:
        return "MockAgent: no changes made"


class ScriptAgent(Agent):
    """Runs a Python script as the agent — for smart mocks and testing."""

    def run(self, prompt: str, workspace: Path) -> str:
        script = self.config.config.get("script")
        if not script:
            return "ScriptAgent: no script configured"
        script_path = Path(script)
        if not script_path.is_absolute():
            # Resolve relative to project root (cwd)
            script_path = Path.cwd() / script_path
        if not script_path.exists():
            return f"ScriptAgent: script not found: {script_path}"
        result = subprocess.run(
            ["python3", str(script_path), str(workspace)],
            capture_output=True, text=True, timeout=60,
        )
        return result.stdout + result.stderr


# ── Registry ────────────────────────────────────────────

AGENT_TYPES: dict[str, type[Agent]] = {
    "claude-code": ClaudeCodeAgent,
    "cli": CLIAgent,
    "mock": MockAgent,
    "script": ScriptAgent,
}


def create_agent(config: AgentConfig) -> Agent:
    cls = AGENT_TYPES.get(config.type)
    if not cls:
        raise ValueError(f"Unknown agent type: {config.type}. Available: {list(AGENT_TYPES)}")
    return cls(config)

"""Environment implementations: workspace creation and isolation."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path

from agent_eval.models import EnvironmentConfig, Task


class Environment(ABC):
    """Manages an isolated workspace for a single eval run."""

    def __init__(self, config: EnvironmentConfig):
        self.config = config
        self.workspace: Path | None = None

    @abstractmethod
    def setup(self, task: Task) -> Path:
        """Create workspace with task files, return workspace path."""

    @abstractmethod
    def cleanup(self) -> None:
        """Remove workspace (unless keep=True)."""

    @property
    def keep(self) -> bool:
        return self.config.config.get("keep", False)


class LocalEnvironment(Environment):
    """Local directory sandbox."""

    def setup(self, task: Task) -> Path:
        base = self.config.config.get("base_dir")
        self.workspace = Path(tempfile.mkdtemp(
            dir=base, prefix=f"eval_{task.id}_",
        ))

        # Copy workspace files
        if task.workspace_dir.exists():
            for src in task.workspace_dir.rglob("*"):
                if src.is_file():
                    rel = src.relative_to(task.workspace_dir)
                    dst = self.workspace / rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    # Keep original copy for diff-based checks
                    orig = self.workspace / f".originals" / rel
                    orig.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, orig)

        return self.workspace

    def cleanup(self) -> None:
        if not self.keep and self.workspace and self.workspace.exists():
            shutil.rmtree(self.workspace)


class DockerEnvironment(Environment):
    """Docker container sandbox."""

    def setup(self, task: Task) -> Path:
        self.workspace = Path(tempfile.mkdtemp(prefix=f"eval_{task.id}_"))

        if task.workspace_dir.exists():
            for src in task.workspace_dir.rglob("*"):
                if src.is_file():
                    rel = src.relative_to(task.workspace_dir)
                    dst = self.workspace / rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    orig = self.workspace / f".originals" / rel
                    orig.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, orig)

        image = self.config.config.get("image", "python:3.12-slim")
        r = subprocess.run(
            ["docker", "run", "-d", "-v", f"{self.workspace}:/workspace",
             "-w", "/workspace", image, "sleep", "3600"],
            capture_output=True, text=True,
        )
        self._container_id = r.stdout.strip()
        return self.workspace

    def cleanup(self) -> None:
        cid = getattr(self, "_container_id", None)
        if cid:
            subprocess.run(["docker", "rm", "-f", cid], capture_output=True)
        if not self.keep and self.workspace and self.workspace.exists():
            shutil.rmtree(self.workspace)


def create_environment(config: EnvironmentConfig) -> Environment:
    if config.type == "docker":
        return DockerEnvironment(config)
    return LocalEnvironment(config)

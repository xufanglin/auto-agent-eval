"""Lightweight API server for the web UI. Serves results as JSON + static files."""

from __future__ import annotations

import json
import mimetypes
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from agent_eval.loader import RESULTS_DIR

STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "web" / "dist"


class APIHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/runs":
            self._json_response(self._list_runs())
        elif self.path.startswith("/api/runs/") and "/files/" in self.path:
            # /api/runs/{dir}/files/{agent}/{task}/{path...}
            rest = self.path[len("/api/runs/"):]
            run_name, _, file_path = rest.partition("/files/")
            self._serve_workspace_file(run_name, file_path)
        elif self.path.startswith("/api/runs/"):
            run_name = self.path[len("/api/runs/"):]
            self._json_response(self._get_run(run_name))
        else:
            self._serve_static()

    def _list_runs(self) -> list[dict]:
        if not RESULTS_DIR.exists():
            return []
        runs = []
        for d in sorted(RESULTS_DIR.iterdir(), reverse=True):
            summary_path = d / "summary.json"
            if d.is_dir() and summary_path.exists():
                summary = json.loads(summary_path.read_text())
                summary["dir_name"] = d.name
                runs.append(summary)
        return runs

    def _get_run(self, run_name: str) -> dict:
        run_dir = RESULTS_DIR / run_name
        if not run_dir.exists():
            return {"error": "not found"}
        summary = json.loads((run_dir / "summary.json").read_text())
        summary["dir_name"] = run_name
        summary["task_details"] = {}
        for f in run_dir.glob("*.json"):
            if f.name != "summary.json":
                summary["task_details"][f.stem] = json.loads(f.read_text())

        # Workspace file listings per agent/task
        ws_dir = run_dir / "workspaces"
        summary["workspaces"] = {}
        if ws_dir.exists():
            for agent_dir in ws_dir.iterdir():
                if not agent_dir.is_dir():
                    continue
                for task_dir in agent_dir.iterdir():
                    if not task_dir.is_dir():
                        continue
                    key = f"{agent_dir.name}/{task_dir.name}"
                    files = []
                    for f in sorted(task_dir.rglob("*")):
                        if f.is_file() and not f.name.startswith("."):
                            rel = str(f.relative_to(task_dir))
                            files.append({"path": rel, "size": f.stat().st_size})
                    summary["workspaces"][key] = files

        # Agent logs
        log_dir = run_dir / "logs"
        summary["logs"] = {}
        if log_dir.exists():
            for agent_dir in log_dir.iterdir():
                if not agent_dir.is_dir():
                    continue
                for f in agent_dir.glob("*.log"):
                    key = f"{agent_dir.name}/{f.stem}"
                    try:
                        summary["logs"][key] = f.read_text()[:50000]
                    except UnicodeDecodeError:
                        pass

        return summary

    def _serve_workspace_file(self, run_name: str, file_path: str):
        full = RESULTS_DIR / run_name / "workspaces" / file_path
        if not full.exists() or not full.is_file():
            self.send_error(404)
            return
        # Security: ensure path stays within results dir
        try:
            full.resolve().relative_to(RESULTS_DIR.resolve())
        except ValueError:
            self.send_error(403)
            return
        content = full.read_bytes()
        mime = mimetypes.guess_type(str(full))[0] or "text/plain"
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(content)

    def _json_response(self, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _serve_static(self):
        path = self.path.split("?")[0]
        if path == "/":
            path = "/index.html"
        file_path = STATIC_DIR / path.lstrip("/")
        if not file_path.exists() or not file_path.is_file():
            file_path = STATIC_DIR / "index.html"
        if not file_path.exists():
            self.send_error(404)
            return
        content = file_path.read_bytes()
        mime = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        if "/api/" in str(args[0]):
            super().log_message(format, *args)


def serve(host: str = "0.0.0.0", port: int = 8080):
    print(f"Serving on http://{host}:{port}")
    print(f"  API:    http://{host}:{port}/api/runs")
    print(f"  UI:     http://{host}:{port}/")
    server = HTTPServer((host, port), APIHandler)
    server.allow_reuse_address = True
    server.serve_forever()

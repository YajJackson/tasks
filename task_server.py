#!/usr/bin/env python3
"""Lightweight HTTP server exposing CRUD APIs and static UI for task.sh."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import threading
import time
from datetime import datetime
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from typing import Any, Dict, List
from urllib.parse import urlparse

SCRIPT_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = SCRIPT_DIR / "webapp"
PROJECT_DIR = Path.cwd()
TASK_DIR = PROJECT_DIR / ".project_tasks"
TASK_FILE = TASK_DIR / "tasks.json"
WEB_DIR = FRONTEND_DIR / "dist"

_TASK_LOCK = threading.Lock()


def ensure_storage() -> None:
    """Make sure the task directory and file exist."""
    TASK_DIR.mkdir(parents=True, exist_ok=True)
    if not TASK_FILE.exists():
        TASK_FILE.write_text("[]", encoding="utf-8")


def load_tasks() -> List[Dict[str, Any]]:
    with _TASK_LOCK:
        if not TASK_FILE.exists():
            return []
        try:
            data = json.loads(TASK_FILE.read_text(encoding="utf-8") or "[]")
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass
        return []


def save_tasks(tasks: List[Dict[str, Any]]) -> None:
    with _TASK_LOCK:
        tmp_path = TASK_FILE.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(tasks, indent=2), encoding="utf-8")
        tmp_path.replace(TASK_FILE)


def generate_id() -> str:
    return str(int(time.time() * 1000))


def now_string() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class TaskRequestHandler(SimpleHTTPRequestHandler):
    """Serve static assets from `web` and expose `/api/tasks` endpoints."""

    def __init__(self, *args: Any, directory: str | None = None, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003 - match signature
        # Keep stdout clean; comment out to enable verbose logging.
        return

    # --- Helpers -----------------------------------------------------------------

    def _json_response(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _no_content(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def _not_found(self) -> None:
        self._json_response({"error": "Task not found"}, HTTPStatus.NOT_FOUND)

    def _bad_request(self, message: str) -> None:
        self._json_response({"error": message}, HTTPStatus.BAD_REQUEST)

    def _parse_body(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
            if isinstance(payload, dict):
                return payload
        except json.JSONDecodeError as error:
            raise ValueError("Invalid JSON payload") from error
        raise ValueError("JSON body must be an object")

    # --- Routing ------------------------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802 - match base class
        parsed = urlparse(self.path)
        if parsed.path == "/api/tasks":
            self._json_response(load_tasks())
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802 - match base class
        parsed = urlparse(self.path)
        if parsed.path != "/api/tasks":
            return super().do_POST()  # default 501

        try:
            payload = self._parse_body()
        except ValueError as error:
            self._bad_request(str(error))
            return

        name = (payload.get("name") or "").strip()
        description = (payload.get("description") or "").strip()
        if not name or not description:
            self._bad_request("Both name and description are required.")
            return

        # Parse tags (optional)
        tags = payload.get("tags", [])
        if not isinstance(tags, list):
            self._bad_request("Tags must be an array.")
            return
        tags = [str(tag).strip() for tag in tags if str(tag).strip()]

        tasks = load_tasks()
        task = {
            "id": generate_id(),
            "name": name,
            "description": description,
            "date": now_string(),
            "status": "TODO",
            "tags": tags,
        }
        tasks.append(task)
        save_tasks(tasks)
        self._json_response(task, HTTPStatus.CREATED)

    def do_PATCH(self) -> None:  # noqa: N802 - match base class
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/tasks/"):
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        task_id = parsed.path.split("/", 3)[-1]
        tasks = load_tasks()
        task = next((item for item in tasks if item.get("id") == task_id), None)
        if task is None:
            self._not_found()
            return

        try:
            payload = self._parse_body()
        except ValueError as error:
            self._bad_request(str(error))
            return

        allowed_fields = {"name", "description", "status", "tags"}
        for key in payload.keys():
            if key not in allowed_fields:
                self._bad_request(f"Unsupported field '{key}'.")
                return

        if "name" in payload:
            value = (payload["name"] or "").strip()
            if not value:
                self._bad_request("Name cannot be empty.")
                return
            task["name"] = value

        if "description" in payload:
            value = (payload["description"] or "").strip()
            if not value:
                self._bad_request("Description cannot be empty.")
                return
            task["description"] = value

        if "status" in payload:
            status = (payload["status"] or "").upper()
            if status not in {"TODO", "DONE"}:
                self._bad_request("Status must be TODO or DONE.")
                return
            task["status"] = status

        if "tags" in payload:
            tags = payload["tags"]
            if not isinstance(tags, list):
                self._bad_request("Tags must be an array.")
                return
            task["tags"] = [str(tag).strip() for tag in tags if str(tag).strip()]

        save_tasks(tasks)
        self._json_response(task)

    def do_DELETE(self) -> None:  # noqa: N802 - match base class
        parsed = urlparse(self.path)
        if not parsed.path.startswith("/api/tasks/"):
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        task_id = parsed.path.split("/", 3)[-1]
        tasks = load_tasks()
        new_tasks = [task for task in tasks if task.get("id") != task_id]
        if len(new_tasks) == len(tasks):
            self._not_found()
            return

        save_tasks(new_tasks)
        self._no_content()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve the task board web UI and API")
    parser.add_argument("--host", default="127.0.0.1", help="Hostname or IP to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")
    return parser.parse_args()


def run_server(host: str, port: int) -> None:
    ensure_storage()

    if not WEB_DIR.exists():
        raise SystemExit(
            f"Web assets not found in {WEB_DIR}. Run 'npm run build' inside {FRONTEND_DIR} first."
        )

    handler = TaskRequestHandler
    TCPServer.allow_reuse_address = True
    with TCPServer((host, port), handler) as httpd:
        print(f"Serving task board at http://{host}:{port} (Press Ctrl+C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\nShutting down server...')


def main() -> None:
    arguments = parse_args()
    run_server(arguments.host, arguments.port)


if __name__ == "__main__":
    main()

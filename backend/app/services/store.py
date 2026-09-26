"""SQLite 持久化：任务、报警、测量、报告。开发默认文件库，测试可换路径。"""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any


class Store:
    def __init__(self, path: str) -> None:
        self.path = path
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init()

    def _init(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS tasks (
              id TEXT PRIMARY KEY,
              state TEXT NOT NULL,
              body TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS alarms (
              id TEXT PRIMARY KEY,
              state TEXT NOT NULL,
              body TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS measurements (
              idempotency_key TEXT PRIMARY KEY,
              body TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS reports (
              id TEXT PRIMARY KEY,
              task_id TEXT NOT NULL,
              body TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS points (
              id TEXT PRIMARY KEY,
              body TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS approvals (
              id TEXT PRIMARY KEY,
              state TEXT NOT NULL,
              body TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS audit_events (
              id TEXT PRIMARY KEY,
              body TEXT NOT NULL
            );
            """
        )
        self._conn.commit()

    def save_task(self, task: dict[str, Any]) -> None:
        body = json.dumps(task, ensure_ascii=False)
        with self._lock:
            self._conn.execute(
                "INSERT INTO tasks(id, state, body) VALUES(?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET state=excluded.state, body=excluded.body",
                (task["id"], task["state"], body),
            )
            self._conn.commit()

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute("SELECT body FROM tasks WHERE id=?", (task_id,)).fetchone()
        return json.loads(row["body"]) if row else None

    def list_tasks(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute("SELECT body FROM tasks ORDER BY id").fetchall()
        return [json.loads(r["body"]) for r in rows]

    def list_tasks_in(self, states: set[str]) -> list[dict[str, Any]]:
        return [t for t in self.list_tasks() if t["state"] in states]

    def add_alarm(self, alarm: dict[str, Any]) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO alarms(id, state, body) VALUES(?,?,?)",
                (alarm["id"], alarm["state"], json.dumps(alarm, ensure_ascii=False)),
            )
            self._conn.commit()

    def list_alarms(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute("SELECT body FROM alarms ORDER BY id").fetchall()
        return [json.loads(r["body"]) for r in rows]

    def update_alarm(self, alarm_id: str, **fields: Any) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute("SELECT body FROM alarms WHERE id=?", (alarm_id,)).fetchone()
            if not row:
                return None
            alarm = json.loads(row["body"])
            alarm.update(fields)
            self._conn.execute(
                "UPDATE alarms SET state=?, body=? WHERE id=?",
                (alarm["state"], json.dumps(alarm, ensure_ascii=False), alarm_id),
            )
            self._conn.commit()
        return alarm

    def put_measurement(self, key: str, body: dict[str, Any]) -> str:
        """重复键忽略（保留首次）。返回 stored 或 replay。"""
        payload = json.dumps(body, ensure_ascii=False)
        with self._lock:
            cur = self._conn.execute(
                "INSERT OR IGNORE INTO measurements(idempotency_key, body) VALUES(?,?)",
                (key, payload),
            )
            self._conn.commit()
            return "stored" if cur.rowcount == 1 else "replay"

    def list_measurements(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute("SELECT body FROM measurements").fetchall()
        return [json.loads(r["body"]) for r in rows]

    def save_report(self, report: dict[str, Any]) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO reports(id, task_id, body) VALUES(?,?,?)",
                (report["id"], report["task_id"], json.dumps(report, ensure_ascii=False)),
            )
            self._conn.commit()

    def list_reports(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute("SELECT body FROM reports").fetchall()
        return [json.loads(r["body"]) for r in rows]

    def get_report(self, report_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute("SELECT body FROM reports WHERE id=?", (report_id,)).fetchone()
        return json.loads(row["body"]) if row else None

    def save_point(self, point: dict[str, Any]) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO points(id, body) VALUES(?,?) "
                "ON CONFLICT(id) DO UPDATE SET body=excluded.body",
                (point["id"], json.dumps(point, ensure_ascii=False)),
            )
            self._conn.commit()

    def list_points(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute("SELECT body FROM points ORDER BY id").fetchall()
        return [json.loads(r["body"]) for r in rows]

    def get_point(self, point_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute("SELECT body FROM points WHERE id=?", (point_id,)).fetchone()
        return json.loads(row["body"]) if row else None

    def delete_point(self, point_id: str) -> bool:
        with self._lock:
            cur = self._conn.execute("DELETE FROM points WHERE id=?", (point_id,))
            self._conn.commit()
            return cur.rowcount == 1

    def save_approval(self, approval: dict[str, Any]) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO approvals(id, state, body) VALUES(?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET state=excluded.state, body=excluded.body",
                (approval["id"], approval["state"], json.dumps(approval, ensure_ascii=False)),
            )
            self._conn.commit()

    def list_approvals(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute("SELECT body FROM approvals ORDER BY id").fetchall()
        return [json.loads(r["body"]) for r in rows]

    def get_approval(self, approval_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute("SELECT body FROM approvals WHERE id=?", (approval_id,)).fetchone()
        return json.loads(row["body"]) if row else None

    def append_audit(self, event: dict[str, Any]) -> None:
        """只追加。不提供更新或删除。"""
        with self._lock:
            self._conn.execute(
                "INSERT INTO audit_events(id, body) VALUES(?,?)",
                (event["id"], json.dumps(event, ensure_ascii=False)),
            )
            self._conn.commit()

    def list_audit(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute("SELECT body FROM audit_events ORDER BY id").fetchall()
        return [json.loads(r["body"]) for r in rows]

    def backup_to(self, dest: Path) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            out = sqlite3.connect(dest)
            try:
                self._conn.backup(out)
            finally:
                out.close()

    def restore_from(self, src: Path) -> None:
        if self.path == ":memory:":
            raise RuntimeError("内存库不支持文件恢复")
        with self._lock:
            self._conn.close()
            Path(self.path).write_bytes(src.read_bytes())
            self._conn = sqlite3.connect(self.path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row

"""任务批报告：先 HTML 归档（PDF 引擎仍待选型）。"""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any
from uuid import uuid4


def render_task_html(task: dict[str, Any]) -> str:
    rows = []
    for sample in task.get("samples") or []:
        rows.append(f"<pre>{html.escape(str(sample))}</pre>")
    body = "\n".join(rows) or "<p>无采样</p>"
    return (
        "<!DOCTYPE html><html lang='zh-CN'><head><meta charset='utf-8'><title>批报告</title></head>"
        f"<body><h1>任务 {html.escape(task['id'])}</h1>"
        f"<p>状态 {html.escape(task['state'])}</p>{body}</body></html>"
    )


def write_report(task: dict[str, Any], report_dir: Path) -> dict[str, Any]:
    report_dir.mkdir(parents=True, exist_ok=True)
    rid = uuid4().hex[:12]
    path = report_dir / f"{rid}.html"
    path.write_text(render_task_html(task), encoding="utf-8")
    return {
        "id": rid,
        "task_id": task["id"],
        "format": "html",
        "path": str(path),
    }

"""批报告。MVP 归档 HTML；PDF 引擎待选定。"""

from __future__ import annotations

import html
from pathlib import Path

from app.adapters.repository import Repository


def generate_task_report(repo: Repository, settings, task_id: str) -> dict:
    existing = [item for item in repo.list_reports() if item["task_ref"] == task_id]
    if existing:
        return existing[0]
    task = repo.get_task(task_id)
    measurements = repo.list_measurements(task_id=task_id)
    measurement_ids = {item["id"] for item in measurements}
    alarms = [
        item
        for item in repo.list_alarms()
        if item["object_ref"] == task_id or item["object_ref"] in measurement_ids
    ]
    breached = [item for item in alarms if item["rule_id"].startswith("limit.")]
    summary = {
        "task_id": task_id,
        "status": task["status"],
        "robot_id": task["robot_id"],
        "measurement_count": len(measurements),
        "breach_count": len(breached),
        "timeline": task["timeline"],
    }
    body = _html(
        title=f"任务报告 {task_id}",
        sections=[
            ("元数据", [f"状态：{task['status']}", f"机器人：{task['robot_id']}", f"错误：{task.get('error_code') or '-'}"]),
            ("结果", [f"{item['metric']}={item['value']} {item['unit']} ({item['quality']}) @ {item['point_id']}" for item in measurements] or ["无测量"]),
            ("超限", [item["message"] for item in breached] or ["无"]),
            ("时间线", [f"{item['ts']} {item['message']}" for item in task["timeline"]] or ["无"]),
        ],
    )
    path = _write(settings, f"task-{task_id}.html", body)
    return repo.add_report(task_id, str(path), "html", summary)


def generate_summary_report(repo: Repository, settings, parent_id: str, kind: str, child_ids: list[str]) -> dict:
    existing = [item for item in repo.list_reports() if item["task_ref"] == parent_id]
    if existing:
        return existing[0]
    children = [repo.get_task(child_id) for child_id in child_ids]
    lines = [f"{child['id']} {child['robot_id']} {child['status']}" for child in children]
    summary = {"kind": kind, "children": [{"id": child["id"], "status": child["status"]} for child in children]}
    body = _html(title=f"{kind} 汇总 {parent_id}", sections=[("子任务", lines or ["无"])])
    path = _write(settings, f"{kind}-{parent_id}.html", body)
    return repo.add_report(parent_id, str(path), "html", summary)


def _write(settings, name: str, body: str) -> Path:
    directory = Path(settings.reports_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_text(body, encoding="utf-8")
    return path


def _html(title: str, sections: list[tuple[str, list[str]]]) -> str:
    parts = [f"<h1>{html.escape(title)}</h1>"]
    for heading, lines in sections:
        items = "".join(f"<li>{html.escape(line)}</li>" for line in lines)
        parts.append(f"<h2>{html.escape(heading)}</h2><ul>{items}</ul>")
    return "<!DOCTYPE html><html><head><meta charset='utf-8'></head><body>" + "".join(parts) + "</body></html>"

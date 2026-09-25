"""结构化日志。禁止记录密钥与完整设备报文。"""

from __future__ import annotations

import json
import logging
from contextvars import ContextVar
from datetime import UTC, datetime

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
task_id_var: ContextVar[str] = ContextVar("task_id", default="")
robot_id_var: ContextVar[str] = ContextVar("robot_id", default="")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "request_id": getattr(record, "request_id", None) or request_id_var.get(),
            "msg": record.getMessage(),
        }
        task_id = getattr(record, "task_id", None) or task_id_var.get()
        robot_id = getattr(record, "robot_id", None) or robot_id_var.get()
        if task_id:
            payload["task_id"] = task_id
        if robot_id:
            payload["robot_id"] = robot_id
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging() -> None:
    root = logging.getLogger()
    if getattr(root, "_mer_configured", False):
        return
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    root._mer_configured = True  # type: ignore[attr-defined]


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)

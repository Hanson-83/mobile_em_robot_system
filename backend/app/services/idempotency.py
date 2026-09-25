"""Measurement 幂等键（DS §5.1）。"""

from __future__ import annotations

import hashlib
from datetime import datetime


def make_idempotency_key(
    *,
    device_id: str,
    sample_id: str,
    ts: datetime,
    client_request_id: str | None = None,
) -> str:
    if client_request_id:
        return client_request_id
    ts_iso = ts.astimezone().isoformat()
    raw = f"{device_id}|{sample_id}|{ts_iso}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()

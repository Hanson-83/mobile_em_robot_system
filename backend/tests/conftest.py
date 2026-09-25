from __future__ import annotations

import json
import os

os.environ.setdefault("MER_ENV", "dev")
os.environ.setdefault("MER_SECRET", "unit-test-secret-m1xx")
os.environ.setdefault("MER_ALLOW_DEV_AUTH", "true")
os.environ.setdefault(
    "MER_DEV_USERS_JSON",
    json.dumps(
        {
            "admin": {"password": "admin", "roles": ["admin"], "perms": ["*"]},
            "operator": {
                "password": "operator",
                "roles": ["operator"],
                "perms": [
                    "operations.task.read",
                    "operations.task.write",
                    "operations.alarm.ack",
                    "operations.alarm.close",
                    "data.measurement.read",
                    "data.alarm.read",
                    "data.robot.read",
                    "data.map.read",
                    "data.report.read",
                ],
            },
        }
    ),
)

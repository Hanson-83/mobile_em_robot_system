"""初始化角色、开发账号、演示地图。生产必须关闭 MER_DEV_SEED 并更换密钥。"""

from __future__ import annotations

from pathlib import Path

import yaml

from app.core.security import hash_password, hash_token

ALL_PERMISSIONS = [
    "operations.task.read",
    "operations.task.write",
    "operations.alarm.ack",
    "operations.alarm.close",
    "operations.approval.read",
    "operations.approval.write",
    "data.measurement.read",
    "data.measurement.write",
    "data.alarm.read",
    "data.alarm.export",
    "data.report.read",
    "data.report.write",
    "data.robot.read",
    "data.map.read",
    "settings.point.read",
    "settings.point.write",
    "settings.limit.read",
    "settings.limit.write",
    "settings.user.read",
    "settings.user.write",
    "settings.feature.read",
    "settings.feature.write",
    "settings.backup.read",
    "settings.backup.write",
    "settings.audit.read",
]

VIEWER = [
    "operations.task.read",
    "operations.approval.read",
    "data.measurement.read",
    "data.alarm.read",
    "data.report.read",
    "data.robot.read",
    "data.map.read",
    "settings.point.read",
    "settings.limit.read",
    "settings.feature.read",
]

OPERATOR = VIEWER + [
    "operations.task.write",
    "operations.alarm.ack",
    "operations.alarm.close",
    "data.measurement.write",
    "data.alarm.export",
    "data.report.write",
]

API_CLIENT = [
    "operations.task.read",
    "operations.task.write",
    "data.measurement.read",
    "data.measurement.write",
    "data.alarm.read",
    "data.robot.read",
    "data.report.read",
    "data.map.read",
]

DEFAULT_LIMITS = {
    "particle.0.5um": {"max": 1000, "unit": "counts"},
    "particle.5.0um": {"max": 100, "unit": "counts"},
    "temp_c": {"min": 18, "max": 26, "unit": "C"},
    "humidity_rh": {"min": 30, "max": 70, "unit": "%RH"},
    "air_speed_mps": {"max": 0.5, "unit": "m/s"},
}


def load_yaml(path: str) -> dict:
    file = Path(path)
    if not file.exists():
        return {}
    return yaml.safe_load(file.read_text(encoding="utf-8")) or {}


def seed(runtime) -> None:
    repo = runtime.repo
    repo.ensure_role("admin", ALL_PERMISSIONS)
    repo.ensure_role("operator", OPERATOR)
    repo.ensure_role("viewer", VIEWER)
    repo.ensure_role("api_client", API_CLIENT)
    if not runtime.settings.dev_seed:
        return
    repo.ensure_user("admin", hash_password("Admin123!"), "管理员", ["admin"])
    operator = repo.ensure_user("operator", hash_password("Operator1!"), "操作员", ["operator"])
    viewer = repo.ensure_user("viewer", hash_password("Viewer123!"), "查看者", ["viewer"])
    repo.ensure_group("operators", "operator", [operator])
    repo.ensure_group("viewers", "viewer", [viewer])
    repo.ensure_api_token("dev", hash_token(runtime.settings.dev_api_token), "api_client")
    if not repo.list_maps():
        repo.upsert_map("map-demo", "演示地图", "seed", 20, 15, {"crs": "local-meters"})
        repo.upsert_point(
            "point-a",
            "map-demo",
            "采样点 A",
            {"x": 2, "y": 3, "theta": 0, "map_id": "map-demo"},
            "particle+climate+airflow",
            DEFAULT_LIMITS,
        )
        repo.upsert_point(
            "point-b",
            "map-demo",
            "采样点 B",
            {"x": 8, "y": 4, "theta": 1.57, "map_id": "map-demo"},
            "particle+climate+airflow",
            DEFAULT_LIMITS,
        )


def apply_schema(engine) -> None:
    from datetime import UTC, datetime

    from sqlalchemy import text
    from sqlalchemy.orm import Session

    from app.adapters.orm import Base, SchemaVersion

    Base.metadata.create_all(engine)
    if str(engine.url).startswith("sqlite"):
        with engine.begin() as connection:
            columns = [row[1] for row in connection.execute(text("PRAGMA table_info(groups)")).fetchall()]
            if columns and "role_name" not in columns:
                connection.execute(text("ALTER TABLE groups ADD COLUMN role_name VARCHAR(64) DEFAULT ''"))
            connection.execute(
                text(
                    "CREATE TRIGGER IF NOT EXISTS audit_events_no_update BEFORE UPDATE ON audit_events "
                    "BEGIN SELECT RAISE(ABORT, 'audit append-only'); END"
                )
            )
            connection.execute(
                text(
                    "CREATE TRIGGER IF NOT EXISTS audit_events_no_delete BEFORE DELETE ON audit_events "
                    "BEGIN SELECT RAISE(ABORT, 'audit append-only'); END"
                )
            )
    with Session(engine) as session:
        if session.get(SchemaVersion, "001") is None:
            session.add(SchemaVersion(version="001", applied_at=datetime.now(UTC)))
            session.commit()

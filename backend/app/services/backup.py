"""备份与恢复。范围：数据库文件（SQLite）或 pg_dump 占位、活动配置、报告目录。"""

from __future__ import annotations

import json
import shutil
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

from app.core.errors import validation_error
from app.core.logging import get_logger

log = get_logger("mer.backup")


def sqlite_path(database_url: str) -> Path | None:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return None
    raw = database_url[len(prefix) :]
    if raw == ":memory:" or raw.startswith("file:"):
        return None
    return Path(raw)


def create_backup(runtime) -> dict:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ") + "-" + uuid.uuid4().hex[:8]
    dest = Path(runtime.settings.backup_dir) / stamp
    dest.mkdir(parents=True, exist_ok=False)
    db_file = sqlite_path(runtime.settings.database_url)
    if db_file and db_file.exists():
        _sqlite_backup(db_file, dest / "mer.db")
        scope = "sqlite+config+reports"
    else:
        note = dest / "POSTGRES.txt"
        note.write_text(
            "当前不是可文件拷贝的 SQLite。生产 PostgreSQL 请在部署机执行 pg_dump，"
            "见 deploy/sql/backup_postgres.md。本次仅打包 config 与报告目录。\n",
            encoding="utf-8",
        )
        scope = "config+reports"
    config_dest = dest / "config"
    config_dest.mkdir()
    devices = Path(runtime.settings.devices_config)
    features = Path(runtime.settings.features_config)
    manifest = {
        "devices_config": str(devices.resolve()) if devices.exists() else str(devices),
        "features_config": str(features.resolve()) if features.exists() else str(features),
    }
    if devices.exists():
        shutil.copy2(devices, config_dest / "devices.yaml")
    if features.exists():
        shutil.copy2(features, config_dest / "features.yaml")
    (dest / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    reports = Path(runtime.settings.reports_dir)
    if reports.exists():
        shutil.copytree(reports, dest / "reports", dirs_exist_ok=True)
    log.info("backup created at %s", dest)
    return runtime.repo.add_backup(str(dest), scope)


def maybe_auto_backup(runtime) -> dict | None:
    """按开关间隔自动备份。间隔为 0 时不跑。没有上次记录时立即做一次。"""
    minutes = float(runtime.features.snapshot().get("auto_backup_interval_minutes") or 0)
    if minutes <= 0:
        return None
    last = runtime.repo.get_kv("last_auto_backup_at") or {}
    now = datetime.now(UTC).replace(tzinfo=None)
    raw = last.get("ts")
    if raw:
        previous = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if previous.tzinfo is not None:
            previous = previous.astimezone(UTC).replace(tzinfo=None)
        if (now - previous).total_seconds() < minutes * 60:
            return None
    info = create_backup(runtime)
    runtime.repo.put_kv("last_auto_backup_at", {"ts": now.isoformat(), "id": info["id"]})
    return info


def restore_backup(runtime, backup_id: str) -> dict:
    info = runtime.repo.get_backup(backup_id)
    src = Path(info["uri"])
    db_src = src / "mer.db"
    db_file = sqlite_path(runtime.settings.database_url)
    if db_src.exists() and db_file is not None:
        runtime.engine.dispose()
        db_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(db_src, db_file)
        runtime.rebind()
    elif db_src.exists():
        raise validation_error("备份含 SQLite 文件，但当前数据库不是 SQLite 文件")
    manifest_path = src / "manifest.json"
    config_src = src / "config"
    if manifest_path.exists() and config_src.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        _restore_named(config_src / "devices.yaml", manifest.get("devices_config") or runtime.settings.devices_config)
        _restore_named(config_src / "features.yaml", manifest.get("features_config") or runtime.settings.features_config)
    elif config_src.exists():
        named = {
            Path(runtime.settings.devices_config).name: Path(runtime.settings.devices_config),
            Path(runtime.settings.features_config).name: Path(runtime.settings.features_config),
        }
        for item in config_src.iterdir():
            target = named.get(item.name)
            if target is not None:
                _restore_named(item, target)
    reports_src = src / "reports"
    if reports_src.exists():
        shutil.copytree(reports_src, Path(runtime.settings.reports_dir), dirs_exist_ok=True)
    log.info("backup restored %s", backup_id)
    return {"id": backup_id, "restored": True}


def _restore_named(source: Path, target) -> None:
    if not source.exists():
        return
    destination = Path(target)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    shutil.copy2(source, temporary)
    temporary.replace(destination)


def _sqlite_backup(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    src = sqlite3.connect(source)
    dst = sqlite3.connect(target)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()

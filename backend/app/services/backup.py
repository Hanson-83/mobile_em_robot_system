"""备份与恢复：SQLite 业务库 + config YAML + 报告目录。"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.core.errors import DomainError
from app.services.store import Store


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _config_files(config_dir: Path) -> list[Path]:
    files: list[Path] = []
    for pattern in ("*.yaml", "*.yml", "maps/*.geojson"):
        files.extend(sorted(config_dir.glob(pattern)))
    return [p for p in files if p.is_file()]


def create_backup(
    *,
    store: Store,
    config_dir: Path,
    report_dir: Path,
    backup_root: Path,
) -> dict[str, Any]:
    bid = uuid4().hex[:12]
    folder = backup_root / bid
    folder.mkdir(parents=True, exist_ok=True)
    db_path = folder / "mer.sqlite"
    store.backup_to(db_path)
    cfg_out = folder / "config"
    cfg_out.mkdir()
    copied: list[str] = []
    for src in _config_files(config_dir):
        rel = src.relative_to(config_dir)
        dest = cfg_out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        copied.append(str(rel))
    rpt_out = folder / "reports"
    if report_dir.exists():
        shutil.copytree(report_dir, rpt_out, dirs_exist_ok=True)
    else:
        rpt_out.mkdir()
    manifest = {
        "id": bid,
        "db_sha256": _sha256(db_path),
        "config_files": copied,
        "report_files": sorted(p.name for p in rpt_out.glob("*") if p.is_file()),
    }
    (folder / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {"id": bid, "path": str(folder), "manifest": manifest}


def restore_backup(
    *,
    store: Store,
    config_dir: Path,
    report_dir: Path,
    backup_root: Path,
    backup_id: str,
) -> dict[str, Any]:
    folder = backup_root / backup_id
    manifest_path = folder / "manifest.json"
    db_path = folder / "mer.sqlite"
    if not manifest_path.exists() or not db_path.exists():
        raise DomainError("NOT_FOUND", f"备份 {backup_id} 不存在")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    actual = _sha256(db_path)
    if actual != manifest.get("db_sha256"):
        raise DomainError("VALIDATION_ERROR", "备份校验失败：数据库摘要不一致")
    store.restore_from(db_path)
    cfg_src = folder / "config"
    for rel in manifest.get("config_files") or []:
        src = cfg_src / rel
        dest = config_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    rpt_src = folder / "reports"
    if report_dir.exists():
        shutil.rmtree(report_dir)
    if rpt_src.exists():
        shutil.copytree(rpt_src, report_dir)
    else:
        report_dir.mkdir(parents=True, exist_ok=True)
    return {"id": backup_id, "restored": True, "config_files": manifest.get("config_files")}

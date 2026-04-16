from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Any

from app.config import FILES_DB_PATH, UPLOAD_DIR
from app.services.excel_service import workbook_metadata
from app.services.storage import load_json, now_iso, save_json


def _load_records() -> dict[str, Any]:
    return load_json(FILES_DB_PATH, {"currentFileId": None, "files": []})


def _save_records(data: dict[str, Any]) -> None:
    save_json(FILES_DB_PATH, data)


def list_recent_files() -> list[dict[str, Any]]:
    data = _load_records()
    files = sorted(data["files"], key=lambda item: item.get("lastUsedAt", ""), reverse=True)
    return files


def get_current_file() -> dict[str, Any] | None:
    data = _load_records()
    current_file_id = data.get("currentFileId")
    for item in data["files"]:
        if item["id"] == current_file_id:
            return item
    return None


def select_file(file_id: str) -> dict[str, Any]:
    data = _load_records()
    for item in data["files"]:
        if item["id"] == file_id:
            item["lastUsedAt"] = now_iso()
            data["currentFileId"] = file_id
            _save_records(data)
            return item
    raise ValueError("未找到指定文件")


def refresh_file(file_id: str) -> dict[str, Any]:
    data = _load_records()
    for item in data["files"]:
        if item["id"] == file_id:
            file_path = Path(item["storedPath"])
            if not file_path.exists():
                raise ValueError("文件不存在，请重新上传")
            metadata = workbook_metadata(file_path)
            item.update(metadata)
            item["lastUsedAt"] = now_iso()
            _save_records(data)
            return item
    raise ValueError("未找到指定文件")


def save_upload(temp_path: Path, original_name: str) -> dict[str, Any]:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_id = f"file_{uuid.uuid4().hex[:8]}"
    target_path = UPLOAD_DIR / f"{file_id}_{original_name}"
    shutil.copy2(temp_path, target_path)
    metadata = workbook_metadata(target_path)
    record = {
        "id": file_id,
        "fileName": original_name,
        "storedPath": str(target_path),
        "lastUsedAt": now_iso(),
        **metadata,
    }

    data = _load_records()
    data["files"] = [item for item in data["files"] if item.get("storedPath") != str(target_path)]
    data["files"].append(record)
    data["currentFileId"] = file_id
    _save_records(data)
    return record

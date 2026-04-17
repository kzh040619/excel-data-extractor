from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Any

from app.config import UPLOAD_DIR, FILES_JSON
from app.services.excel_service import workbook_metadata
from app.services.storage import load_json, now_iso, save_json


def _load_records() -> dict[str, Any]:
    return load_json(FILES_JSON, {"currentFileId": None, "files": []})


def _save_records(data: dict[str, Any]) -> None:
    save_json(FILES_JSON, data)


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


def delete_file(file_id: str) -> bool:
    """删除文件"""
    data = _load_records()
    file_to_delete = None
    
    # 查找文件
    for item in data["files"]:
        if item["id"] == file_id:
            file_to_delete = item
            break
    
    if not file_to_delete:
        return False
    
    # 删除物理文件
    file_path = Path(file_to_delete["storedPath"])
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception as e:
            print(f"删除文件失败: {e}")
    
    # 从列表中移除
    data["files"] = [item for item in data["files"] if item["id"] != file_id]
    
    # 如果删除的是当前文件，清空currentFileId
    if data.get("currentFileId") == file_id:
        data["currentFileId"] = None
        # 如果还有其他文件，选择最近使用的
        if data["files"]:
            data["currentFileId"] = data["files"][0]["id"]
    
    _save_records(data)
    return True

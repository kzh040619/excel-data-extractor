"""
快捷操作服务 - v1.0.2
"""
import json
from datetime import datetime
from typing import Any

from app.config import SHORTCUTS_JSON


def load_shortcuts() -> list[dict[str, Any]]:
    """加载快捷操作"""
    if not SHORTCUTS_JSON.exists():
        return []
    try:
        with open(SHORTCUTS_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def save_shortcuts(shortcuts: list[dict[str, Any]]) -> None:
    """保存快捷操作"""
    with open(SHORTCUTS_JSON, 'w', encoding='utf-8') as f:
        json.dump(shortcuts, f, ensure_ascii=False, indent=2)


def add_shortcut(
    name: str,
    query_type: str,
    query_content: str,
    filters: list[dict[str, Any]] | None = None,
    columns: list[str] | None = None
) -> dict[str, Any]:
    """添加快捷操作"""
    shortcuts = load_shortcuts()
    
    shortcut = {
        "id": f"shortcut_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        "name": name,
        "type": query_type,
        "content": query_content,
        "filters": filters or [],
        "columns": columns or [],
        "createdAt": datetime.now().isoformat(),
    }
    
    shortcuts.append(shortcut)
    save_shortcuts(shortcuts)
    return shortcut


def get_all_shortcuts() -> list[dict[str, Any]]:
    """获取所有快捷操作"""
    return load_shortcuts()


def delete_shortcut(shortcut_id: str) -> bool:
    """删除快捷操作"""
    shortcuts = load_shortcuts()
    original_len = len(shortcuts)
    shortcuts = [s for s in shortcuts if s.get("id") != shortcut_id]
    
    if len(shortcuts) < original_len:
        save_shortcuts(shortcuts)
        return True
    return False


def update_shortcut(shortcut_id: str, name: str | None = None, **kwargs) -> dict[str, Any] | None:
    """更新快捷操作"""
    shortcuts = load_shortcuts()
    
    for shortcut in shortcuts:
        if shortcut.get("id") == shortcut_id:
            if name:
                shortcut["name"] = name
            shortcut.update(kwargs)
            save_shortcuts(shortcuts)
            return shortcut
    
    return None

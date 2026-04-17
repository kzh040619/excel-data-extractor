"""
查询历史服务 - v1.0.2
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import HISTORY_JSON


def load_history() -> list[dict[str, Any]]:
    """加载查询历史"""
    if not HISTORY_JSON.exists():
        return []
    try:
        with open(HISTORY_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def save_history(history: list[dict[str, Any]]) -> None:
    """保存查询历史"""
    with open(HISTORY_JSON, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def add_history_record(
    query_type: str,
    query_content: str,
    filters: list[dict[str, Any]] | None = None,
    result_count: int = 0,
    file_id: str | None = None
) -> dict[str, Any]:
    """添加历史记录"""
    history = load_history()
    
    record = {
        "id": f"history_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        "type": query_type,
        "content": query_content,
        "filters": filters or [],
        "resultCount": result_count,
        "fileId": file_id,
        "timestamp": datetime.now().isoformat(),
    }
    
    history.insert(0, record)  # 最新的在前面
    
    # 只保留最近100条
    if len(history) > 100:
        history = history[:100]
    
    save_history(history)
    return record


def get_recent_history(limit: int = 20) -> list[dict[str, Any]]:
    """获取最近的历史记录"""
    history = load_history()
    return history[:limit]


def delete_history_record(history_id: str) -> bool:
    """删除历史记录"""
    history = load_history()
    original_len = len(history)
    history = [h for h in history if h.get("id") != history_id]
    
    if len(history) < original_len:
        save_history(history)
        return True
    return False


def clear_history() -> None:
    """清空历史记录"""
    save_history([])

"""
敏感字段管理服务 - v1.0.2
"""
import json
from typing import Any

from app.config import DEFAULT_SENSITIVE_FIELDS, SENSITIVE_FIELDS_JSON


def load_sensitive_fields() -> list[str]:
    """加载敏感字段列表"""
    if not SENSITIVE_FIELDS_JSON.exists():
        # 首次使用，创建默认配置
        save_sensitive_fields(DEFAULT_SENSITIVE_FIELDS)
        return DEFAULT_SENSITIVE_FIELDS.copy()
    
    try:
        with open(SENSITIVE_FIELDS_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return DEFAULT_SENSITIVE_FIELDS.copy()


def save_sensitive_fields(fields: list[str]) -> None:
    """保存敏感字段列表"""
    with open(SENSITIVE_FIELDS_JSON, 'w', encoding='utf-8') as f:
        json.dump(fields, f, ensure_ascii=False, indent=2)


def add_sensitive_field(field: str) -> list[str]:
    """添加敏感字段"""
    fields = load_sensitive_fields()
    if field not in fields:
        fields.append(field)
        save_sensitive_fields(fields)
    return fields


def remove_sensitive_field(field: str) -> list[str]:
    """移除敏感字段"""
    fields = load_sensitive_fields()
    if field in fields:
        fields.remove(field)
        save_sensitive_fields(fields)
    return fields


def reset_to_default() -> list[str]:
    """重置为默认敏感字段"""
    save_sensitive_fields(DEFAULT_SENSITIVE_FIELDS)
    return DEFAULT_SENSITIVE_FIELDS.copy()


def get_safe_columns(all_columns: list[str]) -> list[str]:
    """从所有列中过滤掉敏感字段"""
    sensitive = load_sensitive_fields()
    return [col for col in all_columns if col not in sensitive]

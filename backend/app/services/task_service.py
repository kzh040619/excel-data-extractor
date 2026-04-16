from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any

import pandas as pd

from app.config import DATA_DIR, FIELD_ALIASES, SAFE_FIELDS, SENSITIVE_FIELDS, TASKS_DB_PATH
from app.services.storage import load_json, now_iso, save_json

# 存储待处理的AI任务
PENDING_TASKS_FILE = DATA_DIR / "pending_ai_tasks.json"


def _load_pending_tasks() -> dict[str, Any]:
    if PENDING_TASKS_FILE.exists():
        with open(PENDING_TASKS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"tasks": {}}


def _save_pending_tasks(data: dict[str, Any]) -> None:
    PENDING_TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PENDING_TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def create_ai_task(message: str, file_id: str, available_columns: list[str]) -> dict[str, Any]:
    """创建一个待AI处理的任务"""
    task_id = f"ai_task_{uuid.uuid4().hex[:8]}"
    data = _load_pending_tasks()
    task = {
        "id": task_id,
        "message": message,
        "fileId": file_id,
        "availableColumns": available_columns,
        "status": "pending",  # pending -> processing -> completed
        "result": None,
        "createdAt": now_iso(),
    }
    data["tasks"][task_id] = task
    _save_pending_tasks(data)
    return task


def get_ai_task(task_id: str) -> dict[str, Any] | None:
    """获取AI任务状态"""
    data = _load_pending_tasks()
    return data["tasks"].get(task_id)


def update_ai_task(task_id: str, status: str, result: dict[str, Any] | None = None) -> None:
    """更新AI任务状态"""
    data = _load_pending_tasks()
    if task_id in data["tasks"]:
        data["tasks"][task_id]["status"] = status
        if result is not None:
            data["tasks"][task_id]["result"] = result
        _save_pending_tasks(data)


def list_pending_ai_tasks() -> list[dict[str, Any]]:
    """列出所有待处理的AI任务"""
    data = _load_pending_tasks()
    return [t for t in data["tasks"].values() if t["status"] == "pending"]


def _load_history() -> dict[str, Any]:
    return load_json(TASKS_DB_PATH, {"items": []})


def save_task_history(item: dict[str, Any]) -> None:
    data = _load_history()
    data["items"].append(item)
    save_json(TASKS_DB_PATH, data)


def _normalize_date_text(value: str) -> str:
    value = value.strip()
    value = value.replace("年", "-").replace("月", "-").replace("日", "")
    value = value.replace("/", "-").replace(".", "-")
    try:
        return pd.to_datetime(value).strftime("%Y-%m-%d")
    except Exception:
        return value


def _normalize_field(field: str) -> str:
    return FIELD_ALIASES.get(field.strip().lower(), field.strip())


def _pick_columns(message: str, available_columns: list[str]) -> list[str]:
    """根据消息内容选择要导出的列"""
    columns: list[str] = []
    
    # 基础信息列（始终包含）
    base_columns = ["姓名", "用户名", "证件姓名", "工号"]
    
    # 检查用户是否明确指定了列
    explicit_cols = []
    col_keywords = ["导出", "输出", "显示", "查看", "列出"]
    if any(kw in message for kw in col_keywords):
        # 尝试从消息中提取列名
        for col in available_columns:
            if col in message and col not in SENSITIVE_FIELDS:
                explicit_cols.append(col)
    
    # 根据消息内容推断需要的列
    inferred_cols = []
    for field in available_columns:
        if field in SENSITIVE_FIELDS:
            continue
        # 如果消息中提到这个字段名或别名
        field_lower = field.lower()
        if field in message or field_lower in message.lower():
            inferred_cols.append(field)
        # 检查别名
        for alias, target in FIELD_ALIASES.items():
            if target.lower() == field_lower and alias in message.lower():
                inferred_cols.append(field)
                break
    
    # 合并结果
    result = list(set(base_columns + explicit_cols + inferred_cols))
    # 过滤敏感字段，确保顺序正确
    result = [col for col in available_columns if col in result and col not in SENSITIVE_FIELDS]
    
    return result if result else [col for col in available_columns if col in SAFE_FIELDS]


def _extract_conditions(message: str, available_columns: list[str]) -> list[dict[str, str]]:
    """从自然语言中提取筛选条件"""
    filters: list[dict[str, str]] = []
    text = message.replace("，", " ").replace("且", " ").replace("并", " ").replace("的", " ")
    text = text.replace("为", "=").replace("是", "=").replace("等于", "=").replace("包含", "*")
    
    # 特殊处理：找出/搜索/查询/查找 + 关键词（值）
    # 这类表达通常意味着在某个字段中搜索该值
    search_patterns = [
        r"找[出寻]?\s*(?:所有)?(?:字段)?(?:带|包含|含)\s*([^\s=<>]+)(?:的)?(?:记录)?",
        r"(?:搜索|查询|查找)\s*(?:所有)?(?:带|包含|含)\s*([^\s=<>]+)的",
    ]
    
    for pattern in search_patterns:
        for match in re.finditer(pattern, text):
            value = match.group(1).strip()
            
            # 智能推断字段名：根据值的特征判断应该匹配哪个字段
            matched_field = None
            
            # 如果值包含"部"、"中心"、"线"等，很可能是部门相关
            if any(kw in value for kw in ["部", "中心", "线", "组", "团队", "部门"]):
                for col in available_columns:
                    if any(d in col for d in ["部门", "所属", "业务部", "事业部", "组织"]):
                        matched_field = col
                        break
            
            # 如果值包含"张"、"李"、"王"等姓氏或人名特征，可能是人员相关
            if not matched_field and any(kw in value for kw in ["张", "李", "王", "刘", "陈", "周", "吴", "赵"]):
                for col in available_columns:
                    if any(n in col for n in ["姓名", "HRBP", "主管", "上级"]):
                        matched_field = col
                        break
            
            # 如果值看起来像日期，匹配日期字段
            if not matched_field and re.search(r"\d{4}[-年/]\d{1,2}[-月/]\d{1,2}", value):
                for col in available_columns:
                    if "日期" in col:
                        matched_field = col
                        break
            
            # 如果值包含"合同"、"主体"，匹配合同相关字段
            if not matched_field and any(kw in value for kw in ["合同", "主体", "公司"]):
                for col in available_columns:
                    if "合同" in col or "主体" in col:
                        matched_field = col
                        break
            
            # 默认：尝试所有字段，找到最匹配的一个
            if not matched_field:
                # 检查值是否直接出现在某个字段名中（不应该）
                for col in available_columns:
                    if value in col or col in value:
                        matched_field = col
                        break
            
            if matched_field and matched_field in available_columns and matched_field not in SENSITIVE_FIELDS:
                if "日期" in matched_field:
                    value = _normalize_date_text(value)
                filters.append({"field": matched_field, "operator": "contains", "value": value})
    
    # 模式1: 字段=值 或 字段是值
    pattern1 = re.compile(r"([^\s=*<>]+?)\s*[=是]\s*([^\s,，*]+)", re.IGNORECASE)
    for match in pattern1.finditer(text):
        field_text = match.group(1).strip()
        value = match.group(2).strip()
        
        # 先尝试别名匹配
        matched_field = FIELD_ALIASES.get(field_text) or FIELD_ALIASES.get(field_text.lower())
        
        # 如果别名没匹配到，尝试模糊匹配
        if not matched_field:
            field_lower = field_text.lower().replace("_", "").replace(" ", "")
            for col in available_columns:
                col_clean = col.lower().replace("_", "").replace(" ", "")
                if field_lower == col_clean or field_lower in col_clean or col_clean in field_lower:
                    matched_field = col
                    break
        
        if matched_field and matched_field in available_columns and matched_field not in SENSITIVE_FIELDS:
            if "日期" in matched_field:
                value = _normalize_date_text(value)
            filters.append({"field": matched_field, "operator": "equals", "value": value})
    
    # 模式2: 字段*值（包含）- 处理 "业务部包含电商" 这种格式
    pattern2 = re.compile(r"([^\s=*<>]+?)\s*[*]\s*([^\s,，]+)", re.IGNORECASE)
    for match in pattern2.finditer(text):
        field_text = match.group(1).strip()
        value = match.group(2).strip()
        
        # 清理字段名（移除可能的前缀如"导出"、"查询"等）
        field_text = re.sub(r"^(导出|查询|搜索|查找|找出)", "", field_text)
        
        # 先尝试别名匹配
        matched_field = FIELD_ALIASES.get(field_text) or FIELD_ALIASES.get(field_text.lower())
        
        # 如果别名没匹配到，尝试模糊匹配
        if not matched_field:
            field_lower = field_text.lower().replace("_", "").replace(" ", "")
            for col in available_columns:
                col_clean = col.lower().replace("_", "").replace(" ", "")
                if field_lower == col_clean or field_lower in col_clean or col_clean in field_lower:
                    matched_field = col
                    break
        
        # 最后再检查别名（模糊匹配别名）
        if not matched_field:
            for alias, target in FIELD_ALIASES.items():
                alias_clean = alias.lower().replace("_", "").replace(" ", "")
                field_lower = field_text.lower().replace("_", "").replace(" ", "")
                if alias_clean == field_lower or alias_clean in field_lower or field_lower in alias_clean:
                    if target in available_columns:
                        matched_field = target
                        break
        
        if matched_field and matched_field in available_columns and matched_field not in SENSITIVE_FIELDS:
            if "日期" in matched_field:
                value = _normalize_date_text(value)
            filters.append({"field": matched_field, "operator": "contains", "value": value})
    
    # 模式3: 比较操作符（用于日期等）
    pattern3 = re.compile(r"([^\s=<>]+?)\s*(<=|>=|<|>)\s*([^\s,，]+)")
    for match in pattern3.finditer(text):
        field_text = match.group(1).strip()
        symbol = match.group(2)
        value = match.group(3).strip()
        
        # 先尝试别名匹配
        matched_field = FIELD_ALIASES.get(field_text) or FIELD_ALIASES.get(field_text.lower())
        
        # 如果别名没匹配到，尝试模糊匹配
        if not matched_field:
            field_lower = field_text.lower().replace("_", "").replace(" ", "")
            for col in available_columns:
                col_clean = col.lower().replace("_", "").replace(" ", "")
                if field_lower in col_clean or col_clean in field_lower:
                    matched_field = col
                    break
        
        if matched_field and matched_field in available_columns and matched_field not in SENSITIVE_FIELDS:
            operator = {"<": "lt", "<=": "lte", ">": "gt", ">=": "gte"}[symbol]
            if "日期" in matched_field:
                value = _normalize_date_text(value)
            filters.append({"field": matched_field, "operator": operator, "value": value})
    
    return filters


def _parse_rule_based(message: str, available_columns: list[str]) -> dict[str, Any]:
    """基于规则解析自然语言任务"""
    # 判断意图
    intent = "export" if any(kw in message for kw in ["导出", "输出excel", "excel", "下载", "生成"]) else "query"
    
    # 提取筛选条件
    filters = _extract_conditions(message, available_columns)
    
    # 选择输出列
    columns = _pick_columns(message, available_columns)
    
    return {
        "intent": intent,
        "filters": filters,
        "columns": columns,
    }


def parse_task(message: str, available_columns: list[str], llm_config: dict[str, Any] | None = None) -> dict[str, Any]:
    """解析自然语言任务（只使用规则解析，不依赖外部大模型）"""
    parsed = _parse_rule_based(message, available_columns)
    save_task_history({"message": message, "parsed": parsed, "createdAt": now_iso(), "mode": "rule"})
    return parsed

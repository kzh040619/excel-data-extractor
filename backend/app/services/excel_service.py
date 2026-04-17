from __future__ import annotations

import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from app.config import EXPORT_DIR

# 字段别名映射
FIELD_ALIASES = {
    "hrbp": "HRBP姓名",
    "bp": "HRBP姓名",
    "合同主体": "劳动合同主体",
    "合同结束日期": "劳动合同/协议结束日期",
    "合同开始日期": "劳动合同/协议开始日",
    "社保地": "社保缴纳地",
    "工作地": "工作地点名称",
}

NAME_FIELDS = ["用户名", "姓名", "证件姓名"]
MULTI_MATCH_FIELDS = ["用户名", "姓名", "证件姓名", "部门", "劳动合同主体", "工作地", "HRBP", "合同结束日期"]


def _normalize_text(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    return str(value).strip()


def _normalize_date_text(value: str) -> str:
    value = value.strip()
    value = value.replace("年", "-").replace("月", "-").replace("日", "")
    value = value.replace("/", "-").replace(".", "-")
    try:
        return pd.to_datetime(value).strftime("%Y-%m-%d")
    except Exception:
        return value


def normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    return {key: _normalize_text(value) for key, value in record.items()}


def resolve_column(df: pd.DataFrame, field: str) -> str:
    normalized = FIELD_ALIASES.get(field.strip().lower(), field.strip())
    for column in df.columns:
        if normalized == column:
            return column
    for column in df.columns:
        if normalized.lower() == str(column).lower():
            return column
    for column in df.columns:
        column_text = str(column)
        if normalized.lower() in column_text.lower() or column_text.lower() in normalized.lower():
            return column_text
    raise ValueError(f"未找到列: {field}")


def build_filter(field: str, raw_value: str) -> dict[str, str] | None:
    value = (raw_value or "").strip()
    if not value:
        return None

    operator = "equals"
    parsed_value = value
    patterns = [
        (r"^>=(.+)$", "gte"),
        (r"^<=(.+)$", "lte"),
        (r"^>(.+)$", "gt"),
        (r"^<(.+)$", "lt"),
        (r"^=(.+)$", "equals"),
        (r"^包含(.+)$", "contains"),
    ]
    for pattern, current_operator in patterns:
        match = re.match(pattern, value)
        if match:
            operator = current_operator
            parsed_value = match.group(1).strip()
            break

    if "日期" in field:
        parsed_value = _normalize_date_text(parsed_value)

    return {"field": field, "operator": operator, "value": parsed_value}


def parse_quick_query(query: str) -> tuple[str, str]:
    parts = [part for part in query.strip().split() if part]
    if len(parts) < 2:
        raise ValueError("快捷查询格式应为：姓名/用户名 字段名")
    target = " ".join(parts[:-1])
    field = parts[-1]
    return target, FIELD_ALIASES.get(field.lower(), field)


def load_workbook(file_path: str | Path, sheet_name: str | int | None = None) -> pd.DataFrame:
    target_sheet = 0 if sheet_name in (None, "", 0) else sheet_name
    return pd.read_excel(file_path, sheet_name=target_sheet)


def workbook_metadata(file_path: str | Path) -> dict[str, Any]:
    excel_file = pd.ExcelFile(file_path)
    first_sheet = excel_file.sheet_names[0]
    preview_df = pd.read_excel(file_path, sheet_name=first_sheet, nrows=1)
    return {
        "sheets": excel_file.sheet_names,
        "sheetName": first_sheet,
        "columns": [str(column) for column in preview_df.columns],
        "lastModified": datetime.fromtimestamp(Path(file_path).stat().st_mtime).isoformat(),
    }


def apply_filters(df: pd.DataFrame, filters: list[dict[str, str]]) -> pd.DataFrame:
    filtered = df.copy()
    for item in filters:
        column = fuzzy_resolve_column(filtered, item["field"])
        if not column:
            continue  # 跳过无法匹配的列，而不是报错
        operator = item["operator"]
        value = item["value"]
        series = filtered[column]

        if "日期" in column:
            left = pd.to_datetime(series, errors="coerce")
            right = pd.to_datetime(value, errors="coerce")
            if pd.notna(right):
                # 无固定期限合同的日期（>=2100年）应该被排除在日期比较之外
                # 只有当筛选条件是"lt"或"lte"时，才排除无固定期限
                indefinite_cutoff = pd.Timestamp("2100-01-01")
                if operator in ("lt", "lte"):
                    # 排除无固定期限（>=2100年）和无效日期
                    valid_mask = (left < indefinite_cutoff) & left.notna()
                elif operator in ("gt", "gte"):
                    # 大于某日期时，保留无固定期限
                    valid_mask = left.notna()
                else:
                    valid_mask = left.notna()
                
                filtered = filtered[valid_mask]
                left = pd.to_datetime(filtered[column], errors="coerce")
                
                if operator == "equals":
                    filtered = filtered[left == right]
                elif operator == "contains":
                    filtered = filtered[filtered[column].astype(str).str.contains(str(value), na=False, case=False)]
                elif operator == "gt":
                    filtered = filtered[left > right]
                elif operator == "gte":
                    filtered = filtered[left >= right]
                elif operator == "lt":
                    filtered = filtered[left < right]
                elif operator == "lte":
                    filtered = filtered[left <= right]
                continue

        if operator in {"gt", "gte", "lt", "lte"}:
            numeric_series = pd.to_numeric(series, errors="coerce")
            numeric_value = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
            if pd.notna(numeric_value):
                if operator == "gt":
                    filtered = filtered[numeric_series > numeric_value]
                elif operator == "gte":
                    filtered = filtered[numeric_series >= numeric_value]
                elif operator == "lt":
                    filtered = filtered[numeric_series < numeric_value]
                elif operator == "lte":
                    filtered = filtered[numeric_series <= numeric_value]
                continue

        text_series = series.astype(str)
        if operator == "equals":
            filtered = filtered[text_series == str(value)]
        elif operator == "contains":
            filtered = filtered[text_series.str.contains(str(value), na=False, case=False)]
        elif operator == "gt":
            filtered = filtered[text_series > str(value)]
        elif operator == "gte":
            filtered = filtered[text_series >= str(value)]
        elif operator == "lt":
            filtered = filtered[text_series < str(value)]
        elif operator == "lte":
            filtered = filtered[text_series <= str(value)]

    return filtered


def safe_columns(df: pd.DataFrame, columns: list[str] | None = None) -> list[str]:
    """返回要展示/导出的列，保留所有原始列（除了黑名单字段）"""
    from app.services.sensitive_service import get_safe_columns
    
    # 先过滤掉黑名单字段
    all_columns = get_safe_columns(list(df.columns))
    
    if not columns:
        return all_columns
    
    # 用户指定的列，尝试模糊匹配
    matched: list[str] = []
    for target in columns:
        resolved = fuzzy_resolve_column(df, target)
        if resolved and resolved not in matched and resolved in all_columns:
            matched.append(resolved)
    
    # 如果有匹配的列，优先使用；否则返回所有可用列
    return matched if matched else all_columns


def fuzzy_resolve_column(df: pd.DataFrame, field: str) -> str | None:
    """模糊匹配列名"""
    field_lower = field.lower().strip()
    
    # 1. 精确匹配
    for col in df.columns:
        if field == col:
            return col
    
    # 2. 忽略大小写精确匹配
    for col in df.columns:
        if field_lower == col.lower():
            return col
    
    # 3. 字段别名映射
    alias_target = FIELD_ALIASES.get(field_lower)
    if alias_target:
        for col in df.columns:
            if alias_target.lower() == col.lower():
                return col
    
    # 4. 包含匹配（用户输入的字段名包含在列名中，或列名包含在字段名中）
    for col in df.columns:
        col_lower = col.lower()
        if field_lower in col_lower or col_lower in field_lower:
            return col
    
    # 5. 分词匹配（支持"合同结束日期"匹配"合同结束日"等）
    for col in df.columns:
        col_lower = col.lower()
        # 检查用户输入的每个关键词是否都在列名中
        field_parts = field_lower.replace('_', '').split()
        col_clean = col_lower.replace('_', '').replace(' ', '')
        if all(part in col_clean for part in field_parts):
            return col
        # 反过来，检查列名的关键词是否在用户输入中
        col_parts = col_clean.split()
        if all(part in field_lower.replace('_', '').replace(' ', '') for part in col_parts if len(part) > 1):
            return col
    
    # 6. 别名反向匹配（列名可能是别名的扩展）
    for alias, target in FIELD_ALIASES.items():
        if alias in field_lower or field_lower in alias:
            for col in df.columns:
                if target.lower() == col.lower() or target.lower() in col.lower():
                    return col
    
    return None


def preview_table(df: pd.DataFrame, columns: list[str] | None = None, limit: int = 50) -> dict[str, Any]:
    final_columns = safe_columns(df, columns)
    prepared = df[final_columns].head(limit).copy() if final_columns else df.head(limit).copy()
    records = [normalize_record(record) for record in prepared.to_dict("records")]
    return {
        "count": int(len(df)),
        "columns": final_columns,
        "rows": records,
    }


def export_excel(df: pd.DataFrame, columns: list[str] | None = None) -> dict[str, str]:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    final_columns = safe_columns(df, columns)
    export_df = df[final_columns].copy() if final_columns else df.copy()
    file_name = f"export_{uuid.uuid4().hex[:8]}.xlsx"
    target_path = EXPORT_DIR / file_name
    export_df.to_excel(target_path, index=False)
    return {"fileName": file_name, "filePath": str(target_path)}


def quick_query(df: pd.DataFrame, query: str) -> dict[str, Any]:
    target, field = parse_quick_query(query)
    matches = df.copy()
    
    # 先尝试精确匹配
    matched = pd.Series([False] * len(matches), index=matches.index)
    for column_name in NAME_FIELDS:
        if column_name in matches.columns:
            matched = matched | matches[column_name].astype(str).str.fullmatch(target, case=False, na=False)
    
    exact_matches = matches[matched]
    
    # 如果没有精确匹配，尝试模糊匹配
    if exact_matches.empty:
        fuzzy = pd.Series([False] * len(matches), index=matches.index)
        for column_name in NAME_FIELDS:
            if column_name in matches.columns:
                fuzzy = fuzzy | matches[column_name].astype(str).str.contains(target, case=False, na=False)
        exact_matches = matches[fuzzy]
    
    if exact_matches.empty:
        return {"matchType": "none", "message": "未找到匹配员工"}
    
    # 模糊匹配用户请求的字段
    requested_column = fuzzy_resolve_column(df, field) or field
    
    # 基础信息列（始终返回）
    base_columns = ["姓名", "用户名", "证件姓名"]
    
    if len(exact_matches) == 1:
        from app.services.sensitive_service import load_sensitive_fields
        sensitive_fields = load_sensitive_fields()
        
        row = exact_matches.iloc[0]
        
        # 返回所有字段（过滤敏感字段）
        all_columns = [col for col in df.columns if col not in sensitive_fields]
        safe_row = {col: row[col] for col in all_columns if col in df.columns}
        
        return {
            "matchType": "single",
            "field": requested_column,
            "value": _normalize_text(row.get(requested_column, "")),
            "record": normalize_record(safe_row),
        }
    
    # 多条匹配时，返回所有字段（过滤敏感字段）
    from app.services.sensitive_service import load_sensitive_fields
    sensitive_fields = load_sensitive_fields()
    
    # 过滤敏感字段
    all_columns = [col for col in df.columns if col not in sensitive_fields]
    
    # 返回所有匹配记录，不限制数量
    return {
        "matchType": "multiple",
        "count": int(len(exact_matches)),
        "rows": [normalize_record(record) for record in exact_matches[all_columns].to_dict("records")],
    }


def batch_query(df: pd.DataFrame, names: list[str], fields: list[str]) -> dict[str, Any]:
    """批量查询多人信息"""
    from app.services.sensitive_service import load_sensitive_fields
    
    sensitive_fields = load_sensitive_fields()
    results = []
    
    for name in names:
        name = name.strip()
        if not name:
            continue
        
        # 查找匹配的人
        matched = pd.Series([False] * len(df), index=df.index)
        for column_name in NAME_FIELDS:
            if column_name in df.columns:
                matched = matched | df[column_name].astype(str).str.fullmatch(name, case=False, na=False)
        
        exact_matches = df[matched]
        
        if exact_matches.empty:
            results.append({
                "name": name,
                "found": False,
                "message": "未找到匹配员工"
            })
            continue
        
        if len(exact_matches) > 1:
            results.append({
                "name": name,
                "found": False,
                "message": f"找到{len(exact_matches)}个匹配，请使用更精确的姓名"
            })
            continue
        
        # 唯一匹配
        row = exact_matches.iloc[0]
        record = {}
        
        # 基础信息
        for col in ["姓名", "用户名", "证件姓名"]:
            if col in df.columns:
                record[col] = _normalize_text(row[col])
        
        # 请求的字段
        for field in fields:
            requested_column = fuzzy_resolve_column(df, field)
            if requested_column and requested_column not in sensitive_fields:
                record[field] = _normalize_text(row.get(requested_column, ""))
        
        results.append({
            "name": name,
            "found": True,
            "data": record
        })
    
    return {
        "total": len(names),
        "found": len([r for r in results if r.get("found")]),
        "results": results
    }


def fuzzy_resolve_column(df: pd.DataFrame, field: str) -> str | None:
    """模糊匹配列名（兼容版本，返回None而不抛出异常）"""
    try:
        return resolve_column(df, field)
    except ValueError:
        return None

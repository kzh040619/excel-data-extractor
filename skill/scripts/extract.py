#!/usr/bin/env python3
"""
Excel数据提取脚本
支持条件筛选、排序、多列提取
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


def parse_condition(condition_str: str) -> Dict[str, Any]:
    """
    解析自然语言条件为结构化条件

    支持的条件格式：
    - "列名=值" - 精确匹配
    - "列名包含值" - 模糊匹配
    - "列名>值" / "列名<值" - 数值比较
    - "列名>=值" / "列名<=值" - 数值比较
    """
    condition = {
        "column": None,
        "operator": None,
        "value": None,
    }

    condition_str = condition_str.strip()

    if match := re.match(r"(.+?)(?:是|=|==)\s*(.+)", condition_str):
        condition["column"] = match.group(1).strip()
        condition["operator"] = "equals"
        condition["value"] = match.group(2).strip()
    elif match := re.match(r"(.+?)包含\s*(.+)", condition_str):
        condition["column"] = match.group(1).strip()
        condition["operator"] = "contains"
        condition["value"] = match.group(2).strip()
    elif match := re.match(r"(.+?)>=\s*(.+)", condition_str):
        condition["column"] = match.group(1).strip()
        condition["operator"] = "gte"
        condition["value"] = match.group(2).strip()
    elif match := re.match(r"(.+?)<=\s*(.+)", condition_str):
        condition["column"] = match.group(1).strip()
        condition["operator"] = "lte"
        condition["value"] = match.group(2).strip()
    elif match := re.match(r"(.+?)>\s*(.+)", condition_str):
        condition["column"] = match.group(1).strip()
        condition["operator"] = "gt"
        condition["value"] = match.group(2).strip()
    elif match := re.match(r"(.+?)<\s*(.+)", condition_str):
        condition["column"] = match.group(1).strip()
        condition["operator"] = "lt"
        condition["value"] = match.group(2).strip()
    else:
        parts = condition_str.split(maxsplit=1)
        if len(parts) >= 2:
            condition["column"] = parts[0]
            condition["operator"] = "contains"
            condition["value"] = parts[1]

    return condition


def apply_condition(df: pd.DataFrame, condition: Dict[str, Any]) -> pd.DataFrame:
    """应用单个条件筛选"""
    col = condition["column"]
    op = condition["operator"]
    val = condition["value"]

    matched_col = None
    for current in df.columns:
        if col.lower() in current.lower() or current.lower() in col.lower():
            matched_col = current
            break

    if matched_col is None:
        for current in df.columns:
            if any(part in current.lower() for part in col.lower().split()):
                matched_col = current
                break

    if matched_col is None:
        raise ValueError(f"未找到列: {col}")

    if op == "equals":
        return df[df[matched_col].astype(str) == val]
    if op == "contains":
        return df[df[matched_col].astype(str).str.contains(val, na=False, case=False)]
    if op in ["gt", "lt", "gte", "lte"]:
        try:
            num_val = float(val)
            numeric_col = pd.to_numeric(df[matched_col], errors="coerce")
            if op == "gt":
                return df[numeric_col > num_val]
            if op == "lt":
                return df[numeric_col < num_val]
            if op == "gte":
                return df[numeric_col >= num_val]
            if op == "lte":
                return df[numeric_col <= num_val]
        except Exception:
            if op == "gt":
                return df[df[matched_col].astype(str) > val]
            if op == "lt":
                return df[df[matched_col].astype(str) < val]
            if op == "gte":
                return df[df[matched_col].astype(str) >= val]
            if op == "lte":
                return df[df[matched_col].astype(str) <= val]

    return df


def extract_data(
    file_path: str,
    conditions: List[str],
    columns: Optional[List[str]] = None,
    sort_by: Optional[str] = None,
    sort_ascending: bool = True,
    output_format: str = "json",
) -> Dict[str, Any]:
    """主提取函数"""
    df = pd.read_excel(file_path)

    for cond_str in conditions:
        condition = parse_condition(cond_str)
        df = apply_condition(df, condition)

    if sort_by:
        sort_col = None
        for current in df.columns:
            if sort_by.lower() in current.lower():
                sort_col = current
                break
        if sort_col:
            df = df.sort_values(by=sort_col, ascending=sort_ascending)

    if columns:
        matched_cols = []
        for col in columns:
            for current in df.columns:
                if col.lower() in current.lower():
                    matched_cols.append(current)
                    break
        if matched_cols:
            df = df[matched_cols]

    result = {
        "count": len(df),
        "columns": list(df.columns),
        "data": df.to_dict("records"),
    }

    if output_format == "table":
        result["table"] = df.to_string(index=False)
    elif output_format == "excel":
        source_path = Path(file_path)
        output_path = source_path.with_name(f"{source_path.stem}_extracted.xlsx")
        df.to_excel(output_path, index=False)
        result["output_path"] = str(output_path)

    return result


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python extract.py <config_json>")
        sys.exit(1)

    config = json.loads(sys.argv[1])
    result = extract_data(
        file_path=config["file_path"],
        conditions=config.get("conditions", []),
        columns=config.get("columns"),
        sort_by=config.get("sort_by"),
        sort_ascending=config.get("sort_ascending", True),
        output_format=config.get("output_format", "json"),
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

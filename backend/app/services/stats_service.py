"""
数据统计报表服务 - v1.0.2
"""
import pandas as pd
from typing import Any


def generate_department_stats(df: pd.DataFrame) -> dict[str, Any]:
    """生成部门统计报表"""
    stats = {
        "totalEmployees": len(df),
        "departments": [],
        "employeeStatus": {},
    }
    
    # 部门统计
    if "所属部门" in df.columns:
        dept_counts = df["所属部门"].value_counts().to_dict()
        stats["departments"] = [
            {"name": dept, "count": int(count)}
            for dept, count in dept_counts.items()
        ]
    
    # 员工状态统计
    if "员工状态" in df.columns:
        status_counts = df["员工状态"].value_counts().to_dict()
        stats["employeeStatus"] = {
            status: int(count) for status, count in status_counts.items()
        }
    
    return stats


def generate_resignation_analysis(df: pd.DataFrame) -> dict[str, Any]:
    """生成离职分析报表"""
    analysis = {
        "totalResignations": 0,
        "resignationsByMonth": [],
        "resignationsByDepartment": [],
        "resignationRate": 0.0,
    }
    
    if "员工状态" not in df.columns:
        return analysis
    
    # 离职员工
    resigned_df = df[df["员工状态"] == "离职"]
    analysis["totalResignations"] = len(resigned_df)
    
    # 离职率
    total = len(df)
    if total > 0:
        analysis["resignationRate"] = round(len(resigned_df) / total * 100, 2)
    
    # 按月统计离职
    if "离职日期" in resigned_df.columns:
        try:
            resigned_df["离职月份"] = pd.to_datetime(resigned_df["离职日期"], errors='coerce').dt.to_period('M')
            month_counts = resigned_df["离职月份"].value_counts().sort_index()
            analysis["resignationsByMonth"] = [
                {"month": str(month), "count": int(count)}
                for month, count in month_counts.items() if pd.notna(month)
            ]
        except Exception:
            pass
    
    # 按部门统计离职
    if "所属部门" in resigned_df.columns:
        dept_counts = resigned_df["所属部门"].value_counts()
        analysis["resignationsByDepartment"] = [
            {"department": dept, "count": int(count)}
            for dept, count in dept_counts.items()
        ]
    
    return analysis


def generate_contract_expiry_analysis(df: pd.DataFrame, months: int = 3) -> dict[str, Any]:
    """生成合同到期分析"""
    from datetime import datetime, timedelta
    
    analysis = {
        "expiringCount": 0,
        "expiringEmployees": [],
    }
    
    if "劳动合同/协议结束日期" not in df.columns:
        return analysis
    
    # 计算截止日期
    cutoff_date = datetime.now() + timedelta(days=months * 30)
    
    try:
        # 筛选即将到期的合同
        df["合同结束日期_解析"] = pd.to_datetime(df["劳动合同/协议结束日期"], errors='coerce')
        expiring_df = df[
            (df["合同结束日期_解析"] <= cutoff_date) &
            (df["合同结束日期_解析"] >= datetime.now()) &
            (df["合同结束日期_解析"].dt.year < 2100)  # 排除无固定期限
        ]
        
        analysis["expiringCount"] = len(expiring_df)
        
        # 返回员工信息
        if len(expiring_df) > 0:
            expiring_list = []
            for _, row in expiring_df.head(50).iterrows():  # 最多50条
                emp = {
                    "name": row.get("姓名", ""),
                    "department": row.get("所属部门", ""),
                    "expiryDate": str(row.get("劳动合同/协议结束日期", "")),
                }
                expiring_list.append(emp)
            analysis["expiringEmployees"] = expiring_list
    
    except Exception as e:
        print(f"合同到期分析错误: {e}")
    
    return analysis


def generate_comprehensive_report(df: pd.DataFrame) -> dict[str, Any]:
    """生成综合报表"""
    return {
        "departmentStats": generate_department_stats(df),
        "resignationAnalysis": generate_resignation_analysis(df),
        "contractExpiryAnalysis": generate_contract_expiry_analysis(df),
    }

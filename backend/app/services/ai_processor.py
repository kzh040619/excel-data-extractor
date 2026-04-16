"""AI任务后台处理器"""
import json
import time
import threading
import requests
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
PENDING_TASKS_FILE = DATA_DIR / "pending_ai_tasks.json"


def load_pending_tasks() -> dict:
    if PENDING_TASKS_FILE.exists():
        with open(PENDING_TASKS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"tasks": {}}


def save_pending_tasks(data: dict) -> None:
    PENDING_TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PENDING_TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def process_task(task: dict) -> dict:
    """处理单个AI任务，返回解析结果"""
    message = task.get("message", "").lower()
    available_columns = task.get("availableColumns", [])
    
    # 简单的意图识别
    intent = "export" if any(kw in message for kw in ["导出", "下载", "生成excel"]) else "query"
    
    filters = []
    columns = []
    
    # 智能解析message
    # 1. 检测部门相关查询
    dept_keywords = ["部门", "业务部", "事业部", "组织", "组", "团队", "中心", "线"]
    for col in available_columns:
        if any(kw in col for kw in ["部门", "所属", "组织"]):
            # 尝试从message中提取部门名
            for keyword in ["电商", "体验", "营销", "运营", "客服", "技术", "产品", "设计"]:
                if keyword in message:
                    filters.append({"field": col, "operator": "contains", "value": keyword})
                    if col not in columns:
                        columns.append(col)
                    break
            if filters:
                break
    
    # 2. 检测日期相关查询
    if "日期" in message or "之前" in message or "之后" in message or "结束" in message:
        import re
        date_match = re.search(r"(\d{4})[-年/](\d{1,2})[-月/](\d{1,2})?", message)
        if date_match:
            date_value = f"{date_match.group(1)}-{date_match.group(2).zfill(2)}-{date_match.group(3).zfill(2) if date_match.group(3) else '01'}"
            for col in available_columns:
                if "日期" in col:
                    if "之前" in message or "<" in message or "早于" in message:
                        filters.append({"field": col, "operator": "lt", "value": date_value})
                    else:
                        filters.append({"field": col, "operator": "gt", "value": date_value})
                    if col not in columns:
                        columns.append(col)
                    break
    
    # 3. 检测人员相关查询
    name_match = None
    import re
    chinese_names = re.findall(r"[\u4e00-\u9fa5]{2,4}", message)
    for name in chinese_names:
        if name not in ["找出", "查询", "搜索", "导出", "下载", "所有", "包含", "员工", "记录"]:
            name_match = name
            break
    
    if name_match:
        for col in available_columns:
            if any(kw in col for kw in ["姓名", "HRBP", "主管", "上级"]):
                filters.append({"field": col, "operator": "contains", "value": name_match})
                if col not in columns:
                    columns.append(col)
                break
    
    # 4. 设置默认列
    if not columns:
        default_cols = ["姓名", "用户名", "所属部门", "HRBP姓名"]
        columns = [col for col in default_cols if col in available_columns]
    
    return {"intent": intent, "filters": filters, "columns": columns}


def submit_result(task_id: str, result: dict) -> bool:
    """提交处理结果到后端"""
    try:
        response = requests.post(
            f"http://localhost:8000/api/tasks/ai-complete/{task_id}",
            json=result,
            timeout=10
        )
        return response.ok
    except Exception as e:
        print(f"提交结果失败: {e}")
        return False


def check_and_process():
    """检查并处理pending任务"""
    data = load_pending_tasks()
    pending = [t for t in data["tasks"].values() if t.get("status") == "pending"]
    
    for task in pending:
        # 标记为processing
        task["status"] = "processing"
        save_pending_tasks(data)
        
        # 处理任务
        try:
            result = process_task(task)
            submit_result(task["id"], result)
            print(f"处理任务 {task['id']}: {result}")
        except Exception as e:
            print(f"处理任务失败 {task['id']}: {e}")
            task["status"] = "failed"
            task["result"] = {"error": str(e)}
            save_pending_tasks(data)


def run_processor():
    """后台运行处理器"""
    print("AI任务处理器已启动...")
    while True:
        try:
            check_and_process()
        except Exception as e:
            print(f"处理异常: {e}")
        time.sleep(5)


if __name__ == "__main__":
    run_processor()

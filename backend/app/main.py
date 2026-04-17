from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.config import EXPORT_DIR
from app.services.excel_service import apply_filters, export_excel, load_workbook, preview_table, quick_query
from app.services.file_service import get_current_file, list_recent_files, refresh_file, save_upload, select_file
# from app.services.task_service import parse_task  # 暂时注释，v1.0.1功能
from app.services.llm_handler import get_llm_config, update_llm_config, call_llm, parse_llm_response


class SelectFileRequest(BaseModel):
    fileId: str


class RefreshFileRequest(BaseModel):
    fileId: str


class FilterItem(BaseModel):
    field: str
    operator: str
    value: str


class ExportPreviewRequest(BaseModel):
    fileId: str
    sheetName: str | int | None = None
    filters: list[FilterItem] = Field(default_factory=list)
    columns: list[str] = Field(default_factory=list)


class QuickQueryRequest(BaseModel):
    fileId: str
    query: str
    sheetName: str | int | None = None


class TaskParseRequest(BaseModel):
    fileId: str
    message: str
    sheetName: str | int | None = None
    availableColumns: list[str] = Field(default_factory=list)


class TaskExecuteRequest(BaseModel):
    fileId: str
    sheetName: str | int | None = None
    intent: str
    filters: list[FilterItem] = Field(default_factory=list)
    columns: list[str] = Field(default_factory=list)
    sortBy: str | None = None
    sortOrder: str = "desc"
    limit: int | None = None


class AiParsedRequest(BaseModel):
    """AI解析后的结果"""
    intent: str
    filters: list[FilterItem] = Field(default_factory=list)
    columns: list[str] = Field(default_factory=list)
    sortBy: str | None = None
    sortOrder: str = "desc"
    limit: int | None = None


app = FastAPI(title="Excel Data Extractor Web API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _current_or_throw(file_id: str) -> dict[str, Any]:
    current = get_current_file()
    if current and current["id"] == file_id:
        return current
    for item in list_recent_files():
        if item["id"] == file_id:
            return item
    raise HTTPException(status_code=404, detail="未找到指定文件")


@app.get("/api/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.post("/api/files/upload")
async def upload_file(file: UploadFile = File(...)) -> dict[str, Any]:
    suffix = Path(file.filename or "upload.xlsx").suffix or ".xlsx"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = Path(temp_file.name)
    try:
        record = save_upload(temp_path, file.filename or "upload.xlsx")
        return record
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        if temp_path.exists():
            temp_path.unlink()


@app.get("/api/files/current")
def current_file() -> dict[str, Any]:
    current = get_current_file()
    return current or {"fileId": None}


@app.get("/api/files/recent")
def recent_files() -> list[dict[str, Any]]:
    return list_recent_files()


@app.post("/api/files/select")
def select_current_file(payload: SelectFileRequest) -> dict[str, Any]:
    try:
        return select_file(payload.fileId)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/files/refresh")
def refresh_current_file(payload: RefreshFileRequest) -> dict[str, Any]:
    try:
        return refresh_file(payload.fileId)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/export/preview")
def export_preview(payload: ExportPreviewRequest) -> dict[str, Any]:
    record = _current_or_throw(payload.fileId)
    try:
        df = load_workbook(record["storedPath"], payload.sheetName or record.get("sheetName"))
        filtered = apply_filters(df, [item.model_dump() for item in payload.filters])
        return preview_table(filtered, payload.columns)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/export/excel")
def export_data(payload: ExportPreviewRequest) -> dict[str, Any]:
    record = _current_or_throw(payload.fileId)
    try:
        df = load_workbook(record["storedPath"], payload.sheetName or record.get("sheetName"))
        filtered = apply_filters(df, [item.model_dump() for item in payload.filters])
        export_result = export_excel(filtered, payload.columns)
        return {
            "count": int(len(filtered)),
            "fileName": export_result["fileName"],
            "downloadUrl": f"/api/downloads/{export_result['fileName']}",
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/query/quick")
def quick_query_api(payload: QuickQueryRequest) -> dict[str, Any]:
    record = _current_or_throw(payload.fileId)
    try:
        df = load_workbook(record["storedPath"], payload.sheetName or record.get("sheetName"))
        return quick_query(df, payload.query)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# 暂时注释v1.0.1的parse接口
# @app.post("/api/tasks/parse")
# def parse_task_api(payload: TaskParseRequest) -> dict[str, Any]:
#     record = _current_or_throw(payload.fileId)
#     available_columns = payload.availableColumns or record.get("columns", [])
#     try:
#         return parse_task(payload.message, available_columns)
#     except Exception as exc:
#         raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/tasks/execute")
def execute_task_api(payload: TaskExecuteRequest) -> dict[str, Any]:
    """执行查询/导出任务"""
    record = _current_or_throw(payload.fileId)
    try:
        df = load_workbook(record["storedPath"], payload.sheetName or record.get("sheetName"))
        
        if payload.filters:
            filtered = apply_filters(df, [item.model_dump() for item in payload.filters])
        else:
            filtered = df
        
        # 应用排序
        if payload.sortBy:
            # 使用模糊匹配查找列名
            from app.services.excel_service import fuzzy_resolve_column
            sort_col = fuzzy_resolve_column(filtered, payload.sortBy)
            if sort_col:
                ascending = payload.sortOrder.lower() == "asc"
                filtered = filtered.sort_values(by=sort_col, ascending=ascending)
        
        # 应用limit限制
        if payload.limit and payload.limit > 0:
            filtered = filtered.head(payload.limit)
        
        # 始终生成Excel文件供下载
        export_result = export_excel(filtered, payload.columns)
        return {
            **preview_table(filtered, payload.columns),
            "fileName": export_result["fileName"],
            "downloadUrl": f"/api/downloads/{export_result['fileName']}",
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/llm/config")
def get_llm_config_api() -> dict[str, Any]:
    """获取LLM配置"""
    return get_llm_config()


@app.post("/api/llm/config")
def save_llm_config(payload: dict[str, Any]) -> dict[str, Any]:
    """保存LLM配置"""
    return update_llm_config(payload)


class ChatRequest(BaseModel):
    message: str
    fileId: str
    availableColumns: list[str] = Field(default_factory=list)
    history: list[dict[str, str]] = Field(default_factory=list)


@app.post("/api/chat")
async def chat_api(payload: ChatRequest) -> dict[str, Any]:
    """处理对话请求"""
    record = _current_or_throw(payload.fileId)
    available_columns = payload.availableColumns or record.get("columns", [])
    
    # 构建消息历史
    messages = []
    for msg in payload.history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": payload.message})
    
    # 调用LLM
    response = await call_llm(messages, {"availableColumns": available_columns})
    
    # 解析响应
    result = parse_llm_response(response)
    
    if result.get("type") in ["query", "export"]:
        # 执行查询
        filters = result.get("filters", [])
        columns = result.get("columns", [])
        sort_by = result.get("sortBy")
        sort_order = result.get("sortOrder", "desc")
        limit = result.get("limit")
        
        df = load_workbook(record["storedPath"], record.get("sheetName"))
        
        if filters:
            filtered = apply_filters(df, filters)
        else:
            filtered = df
        
        # 应用排序
        if sort_by:
            from app.services.excel_service import fuzzy_resolve_column
            sort_col = fuzzy_resolve_column(filtered, sort_by)
            if sort_col:
                ascending = sort_order.lower() == "asc"
                filtered = filtered.sort_values(by=sort_col, ascending=ascending)
        
        # 应用limit限制
        if limit and limit > 0:
            filtered = filtered.head(limit)
        
        export_result = export_excel(filtered, columns)
        query_result = {
            **preview_table(filtered, columns),
            "fileName": export_result["fileName"],
            "downloadUrl": f"/api/downloads/{export_result['fileName']}",
        }
        
        return {
            **result,
            "count": query_result.get("count", 0),
            "columns": query_result.get("columns", columns),
            "downloadUrl": query_result.get("downloadUrl"),
        }
    
    # 普通对话
    return {"type": "chat", "message": response}


@app.get("/api/downloads/{file_name}")
def download_file(file_name: str) -> FileResponse:
    target_path = EXPORT_DIR / file_name
    if not target_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(path=target_path, filename=file_name)


# ============ v1.0.2 新增API ============

# 1. 查询历史相关
from app.services.history_service import (
    get_recent_history,
    add_history_record,
    delete_history_record,
    clear_history,
)


class AddHistoryRequest(BaseModel):
    queryType: str
    queryContent: str
    filters: list[dict[str, Any]] | None = None
    resultCount: int = 0
    fileId: str | None = None


@app.get("/api/history")
def get_history(limit: int = 20) -> list[dict[str, Any]]:
    """获取查询历史"""
    return get_recent_history(limit)


@app.post("/api/history")
def add_history(payload: AddHistoryRequest) -> dict[str, Any]:
    """添加历史记录"""
    return add_history_record(
        query_type=payload.queryType,
        query_content=payload.queryContent,
        filters=payload.filters,
        result_count=payload.resultCount,
        file_id=payload.fileId,
    )


@app.delete("/api/history/{history_id}")
def delete_history(history_id: str) -> dict[str, bool]:
    """删除历史记录"""
    success = delete_history_record(history_id)
    return {"success": success}


@app.delete("/api/history")
def clear_all_history() -> dict[str, bool]:
    """清空所有历史"""
    clear_history()
    return {"success": True}


# 2. 快捷操作相关
from app.services.shortcut_service import (
    get_all_shortcuts,
    add_shortcut,
    delete_shortcut,
    update_shortcut,
)


class AddShortcutRequest(BaseModel):
    name: str
    queryType: str
    queryContent: str
    filters: list[dict[str, Any]] | None = None
    columns: list[str] | None = None


class UpdateShortcutRequest(BaseModel):
    name: str | None = None


@app.get("/api/shortcuts")
def get_shortcuts() -> list[dict[str, Any]]:
    """获取所有快捷操作"""
    return get_all_shortcuts()


@app.post("/api/shortcuts")
def create_shortcut(payload: AddShortcutRequest) -> dict[str, Any]:
    """创建快捷操作"""
    return add_shortcut(
        name=payload.name,
        query_type=payload.queryType,
        query_content=payload.queryContent,
        filters=payload.filters,
        columns=payload.columns,
    )


@app.delete("/api/shortcuts/{shortcut_id}")
def remove_shortcut(shortcut_id: str) -> dict[str, bool]:
    """删除快捷操作"""
    success = delete_shortcut(shortcut_id)
    return {"success": success}


@app.patch("/api/shortcuts/{shortcut_id}")
def modify_shortcut(shortcut_id: str, payload: UpdateShortcutRequest) -> dict[str, Any]:
    """更新快捷操作"""
    result = update_shortcut(shortcut_id, name=payload.name)
    if result:
        return result
    raise HTTPException(status_code=404, detail="快捷操作不存在")


# 3. 敏感字段管理
from app.services.sensitive_service import (
    load_sensitive_fields,
    add_sensitive_field,
    remove_sensitive_field,
    reset_to_default,
    get_safe_columns,
)


class AddSensitiveFieldRequest(BaseModel):
    field: str


@app.get("/api/sensitive-fields")
def get_sensitive_fields() -> list[str]:
    """获取敏感字段列表"""
    return load_sensitive_fields()


@app.post("/api/sensitive-fields")
def create_sensitive_field(payload: AddSensitiveFieldRequest) -> list[str]:
    """添加敏感字段"""
    return add_sensitive_field(payload.field)


@app.delete("/api/sensitive-fields/{field}")
def remove_sensitive_field_api(field: str) -> list[str]:
    """删除敏感字段"""
    return remove_sensitive_field(field)


@app.post("/api/sensitive-fields/reset")
def reset_sensitive_fields() -> list[str]:
    """重置为默认敏感字段"""
    return reset_to_default()


# 4. 统计报表
from app.services.stats_service import (
    generate_department_stats,
    generate_resignation_analysis,
    generate_contract_expiry_analysis,
    generate_comprehensive_report,
)


class StatsRequest(BaseModel):
    fileId: str
    sheetName: str | int | None = None


@app.post("/api/stats/department")
def get_department_stats(payload: StatsRequest) -> dict[str, Any]:
    """部门统计"""
    record = _current_or_throw(payload.fileId)
    df = load_workbook(record["storedPath"], payload.sheetName or record.get("sheetName"))
    return generate_department_stats(df)


@app.post("/api/stats/resignation")
def get_resignation_stats(payload: StatsRequest) -> dict[str, Any]:
    """离职分析"""
    record = _current_or_throw(payload.fileId)
    df = load_workbook(record["storedPath"], payload.sheetName or record.get("sheetName"))
    return generate_resignation_analysis(df)


@app.post("/api/stats/contract-expiry")
def get_contract_expiry_stats(payload: StatsRequest) -> dict[str, Any]:
    """合同到期分析"""
    record = _current_or_throw(payload.fileId)
    df = load_workbook(record["storedPath"], payload.sheetName or record.get("sheetName"))
    return generate_contract_expiry_analysis(df)


@app.post("/api/stats/comprehensive")
def get_comprehensive_stats(payload: StatsRequest) -> dict[str, Any]:
    """综合报表"""
    record = _current_or_throw(payload.fileId)
    df = load_workbook(record["storedPath"], payload.sheetName or record.get("sheetName"))
    return generate_comprehensive_report(df)


# 5. 批量查询
from app.services.excel_service import batch_query


class BatchQueryRequest(BaseModel):
    fileId: str
    names: list[str]
    fields: list[str]
    sheetName: str | int | None = None


@app.post("/api/query/batch")
def batch_query_api(payload: BatchQueryRequest) -> dict[str, Any]:
    """批量查询多人信息"""
    record = _current_or_throw(payload.fileId)
    try:
        df = load_workbook(record["storedPath"], payload.sheetName or record.get("sheetName"))
        result = batch_query(df, payload.names, payload.fields)
        
        # 记录历史
        add_history_record(
            query_type="batch",
            query_content=f"批量查询{len(payload.names)}人: {', '.join(payload.fields)}",
            result_count=result.get("found", 0),
            file_id=payload.fileId,
        )
        
        return result
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# 6. 缓存管理
from app.services.cache_service import cache_service


@app.get("/api/cache/stats")
def get_cache_stats() -> dict[str, Any]:
    """获取缓存统计"""
    return cache_service.get_cache_stats()


@app.post("/api/cache/clear")
def clear_cache() -> dict[str, bool]:
    """清空所有缓存"""
    cache_service.clear_all()
    return {"success": True}


@app.delete("/api/cache/{file_id}")
def invalidate_file_cache(file_id: str) -> dict[str, bool]:
    """使特定文件缓存失效"""
    cache_service.invalidate(file_id)
    return {"success": True}


# 7. 版本更新
from app.services.version_service import check_for_updates, get_current_version


@app.get("/api/version")
def get_version() -> dict[str, str]:
    """获取当前版本"""
    return get_current_version()


@app.get("/api/version/check")
async def check_updates() -> dict[str, Any]:
    """检查更新"""
    return await check_for_updates()


# 8. 文件删除（新增）
from app.services.file_service import delete_file


@app.delete("/api/files/{file_id}")
def delete_file_api(file_id: str) -> dict[str, bool]:
    """删除文件"""
    try:
        success = delete_file(file_id)
        if success:
            # 清除缓存
            cache_service.invalidate(file_id)
        return {"success": success}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

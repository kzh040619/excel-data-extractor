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
from app.services.task_service import parse_task
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


@app.post("/api/tasks/parse")
def parse_task_api(payload: TaskParseRequest) -> dict[str, Any]:
    record = _current_or_throw(payload.fileId)
    available_columns = payload.availableColumns or record.get("columns", [])
    try:
        return parse_task(payload.message, available_columns)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

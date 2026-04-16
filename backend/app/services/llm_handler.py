"""大模型处理模块 - 支持多种API"""
import json
import httpx
from typing import Any
from pathlib import Path

# 配置文件路径
CONFIG_FILE = Path(__file__).resolve().parents[3] / "data" / "llm_config.json"

# 默认配置（可被用户覆盖）
DEFAULT_CONFIG = {
    "provider": "deepseek",
    "baseUrl": "https://api.deepseek.com",
    "model": "deepseek-chat",
    "apiKey": "",
    "configured": False
}

_current_config = DEFAULT_CONFIG.copy()


def _load_config() -> dict:
    """从文件加载配置"""
    global _current_config
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                data = json.load(f)
                _current_config.update(data)
                _current_config["configured"] = bool(data.get("apiKey"))
        except:
            pass
    return _current_config


def _save_config() -> None:
    """保存配置到文件"""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(_current_config, f, ensure_ascii=False, indent=2)


# 启动时加载配置
_load_config()


def get_llm_config() -> dict:
    return _current_config.copy()


def update_llm_config(config: dict) -> dict:
    global _current_config
    _current_config.update(config)
    _current_config["configured"] = bool(config.get("apiKey"))
    _save_config()
    return _current_config


async def call_llm(messages: list[dict], context: dict | None = None) -> str:
    """调用大模型API"""
    if not _current_config.get("configured") or not _current_config.get("apiKey"):
        return "抱歉，大模型尚未配置。请先配置API Key。"
    
    system_prompt = """你是一个专业的HR数据分析助手。用户会向你提问关于员工数据的问题。

你的任务：
1. 理解用户的意图（查询、导出、统计、对话等）
2. 如果是数据查询，生成JSON格式的查询参数
3. 如果是普通对话，友好地回复用户

当用户需要查询数据时，返回JSON格式：
```json
{
  "type": "query",
  "filters": [{"field": "字段名", "operator": "contains/equals/gt/lt", "value": "值"}],
  "sortBy": null,
  "sortOrder": "desc",
  "limit": null,
  "columns": [],
  "explanation": "简要解释你的理解"
}
```

重要规则：
1. 对于部门、团队、组等组织类查询，使用 "contains" 而不是 "equals"，因为部门名称可能包含更详细的后缀
2. 对于精确人名查询，使用 "equals"
3. 对于日期比较，使用 "gt"（大于）、"lt"（小于）
4. 字段名要从可用列中选择最接近的
5. **columns必须返回空数组[]**，表示导出所有字段，不要自己删减列！除非用户明确指定只要某些列
6. **limit参数**：当用户指定数量时（如"最近5个"、"前10条"），设置limit为对应数字；否则返回null
7. **sortBy和sortOrder**：当用户提到"最近"、"最新"、"最早"时，设置排序字段和顺序
   - "最近离职" → sortBy="离职日期", sortOrder="desc"
   - "最早入职" → sortBy="入职日期", sortOrder="asc"
   - 如果没有排序需求，sortBy=null

常见场景示例：
- "最近离职的5个人" → filters筛选员工状态=离职，sortBy="离职日期"，sortOrder="desc"，limit=5
- "合同即将到期的员工" → filters筛选合同结束日期在未来，sortBy="劳动合同/协议结束日期"，sortOrder="asc"，limit=null
- "找出电商部门的人" → filters包含电商，sortBy=null，limit=null

字段别名说明：
- hrbp / HRBP → HRBP姓名
- 业务部/部门/事业部 → 所属部门
- 合同结束日期 → 劳动合同/协议结束日期
- 合同主体 → 劳动合同主体"""

    if context:
        system_prompt += f"\n\n当前Excel的可用列：{context.get('availableColumns', [])}"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_current_config['baseUrl'].rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {_current_config['apiKey']}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": _current_config["model"],
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        *messages
                    ],
                    "temperature": 0.7
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                return f"API调用失败: {response.status_code} - {response.text}"
    except Exception as e:
        return f"调用失败: {str(e)}"


def parse_llm_response(response: str) -> dict:
    """解析LLM响应，提取查询参数"""
    # 尝试提取JSON
    import re
    json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except:
            pass
    
    # 尝试直接解析JSON
    json_match = re.search(r'\{[\s\S]*\}', response)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except:
            pass
    
    # 不是查询，是普通对话
    return {"type": "chat", "message": response}

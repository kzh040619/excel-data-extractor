"""
配置文件 - v1.0.2
"""
from pathlib import Path

# 基础目录
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
EXPORT_DIR = DATA_DIR / "exports"
CACHE_DIR = DATA_DIR / "cache"

# 文件路径
FILES_JSON = DATA_DIR / "files.json"
TASKS_JSON = DATA_DIR / "tasks.json"
PENDING_AI_TASKS_JSON = DATA_DIR / "pending_ai_tasks.json"
CONFIG_JSON = DATA_DIR / "config.json"
LLM_CONFIG_JSON = DATA_DIR / "llm_config.json"
HISTORY_JSON = DATA_DIR / "query_history.json"  # 新增：查询历史
SHORTCUTS_JSON = DATA_DIR / "shortcuts.json"  # 新增：快捷操作
SENSITIVE_FIELDS_JSON = DATA_DIR / "sensitive_fields.json"  # 新增：自定义敏感字段

# 确保目录存在
for directory in [DATA_DIR, UPLOAD_DIR, EXPORT_DIR, CACHE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# 默认敏感字段列表
DEFAULT_SENSITIVE_FIELDS = [
    "身份证号", "证件号码", "护照号码",
    "银行卡号", "银行账号", "开户行",
    "手机号", "电话号码", "联系电话", "紧急联系人电话",
    "邮箱", "电子邮箱", "个人邮箱", "公司邮箱",
    "家庭住址", "现住址", "户籍地址", "详细地址",
    "紧急联系人", "紧急联系人姓名", "紧急联系人关系",
    "社保账号", "公积金账号", "社会保险号",
    "薪资", "工资", "基本工资", "月薪", "年薪", "薪酬",
]

# 版本信息
VERSION = "1.0.2"
GITHUB_REPO = "kzh040619/excel-data-extractor"

# 性能配置
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
CHUNK_SIZE = 10000  # 大文件分块处理行数
CACHE_EXPIRY = 3600  # 缓存过期时间（秒）
MAX_PREVIEW_ROWS = 50  # 预览最大行数

# LLM配置
DEFAULT_LLM_CONFIG = {
    "provider": "deepseek",
    "baseUrl": "https://api.deepseek.com",
    "model": "deepseek-chat",
    "apiKey": "",
    "configured": False
}

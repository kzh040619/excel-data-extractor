from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "backend" / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
EXPORT_DIR = DATA_DIR / "exports"
CONFIG_PATH = DATA_DIR / "config.json"
FILES_DB_PATH = DATA_DIR / "files.json"
TASKS_DB_PATH = DATA_DIR / "tasks.json"

SAFE_FIELDS = [
    "用户名",
    "姓名",
    "证件姓名",
    "部门",
    "劳动合同主体",
    "合同开始日期",
    "合同结束日期",
    "工时性质",
    "社保地",
    "工作地",
    "HRBP",
    "HRBPhead",
]

SENSITIVE_FIELDS = [
    "身份证号",
    "证件号码",
    "银行卡号",
    "开户行",
    "银行名称",
    "银行账号",
    "账户所有人",
    "邮箱",
    "个人邮箱",
    "公司邮箱",
    "薪资",
    "手机号",
    "电话号码",
    "联系电话",
    "家庭住址",
    "现住址",
    "户籍地址",
    "紧急联系人",
    "紧急联系人电话",
    "主要联系人关系",
    "主要联系人姓名",
    "主要联系人电话",
    "社保账号",
    "公积金账号",
    "证件类型",
]

FIELD_ALIASES = {
    "hrbp": "HRBP姓名",
    "hrbphead": "HRBP Head姓名",
    "hrbp姓名": "HRBP姓名",
    "合同主体": "劳动合同主体",
    "开始日期": "合同开始日期",
    "结束日期": "合同结束日期",
    "社保": "社保缴纳地",
    "社保地": "社保缴纳地",
    "工作城市": "工作地点名称",
    "工作地": "工作地点名称",
    "业务部": "所属部门",
    "事业部": "所属部门",
    "组织": "所属部门",
    "部门": "所属部门",
    "职级": "职位名称",
    "职位": "职位名称",
    "入职": "入职日期",
    "离职": "离职日期",
    "姓名": "姓名",
    "用户名": "用户名",
    "工号": "工号",
}

DEFAULT_SHEET = 0

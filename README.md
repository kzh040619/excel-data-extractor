# Excel 数据提取工具

一个基于AI的Excel智能查询和导出工具，支持自然语言查询、条件筛选和批量导出。

## 功能特性

✨ **核心功能**
- 🤖 **AI智能查询**：使用自然语言提问，自动生成查询条件
- 📊 **条件筛选导出**：支持多字段、多条件的精确筛选
- 🔍 **快速查询**：输入"姓名+字段"快速查看员工信息
- 📥 **一键导出Excel**：自动生成Excel文件供下载
- 🔐 **敏感数据保护**：自动过滤身份证、银行卡等敏感字段

🎯 **智能特性**
- 支持数量限制（"最近5个人"、"前10条"）
- 支持日期排序（"最近离职"、"最早入职"）
- 自动排除无固定期限合同（2999年）
- 模糊匹配字段名（"合同结束日期" = "劳动合同/协议结束日期"）
- 部门名称智能匹配（自动使用contains而非equals）

## 快速开始

### 环境要求
- Python 3.10+
- Node.js 16+
- Chrome/Edge浏览器

### 安装步骤

#### 1. 克隆项目
```bash
git clone https://github.com/你的用户名/excel-data-extractor.git
cd excel-data-extractor
```

#### 2. 启动后端
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

后端启动后访问：http://127.0.0.1:8000/docs 查看API文档

#### 3. 启动前端（新开终端）
```bash
cd frontend
npm install
npm run dev
```

前端启动后访问：http://localhost:5173

## 使用说明

### 1️⃣ 上传Excel文件
- 点击"上传"按钮，选择Excel文件（.xlsx/.xls）
- 系统自动解析工作表和列名

### 2️⃣ 字段导出（第一栏）

**适用场景**：精确条件筛选导出

**操作步骤**：
1. 在对应字段输入框填入筛选条件
2. 点击"预览结果"查看筛选结果
3. 点击"导出Excel"生成文件

**筛选语法**：
- `张三` - 精确匹配
- `<2023-01-01` - 小于日期（自动排除2999年）
- `>100` - 大于数值
- `包含电商` - 模糊匹配

**示例**：
```
所属部门: 电商
劳动合同/协议结束日期: <2024-12-31
```

### 3️⃣ 信息查询（第二栏）

**适用场景**：快速查看个人信息

**语法**：`姓名 字段名`

**示例**：
- `张三 hrbp` - 查看张三的HRBP
- `李四 合同主体` - 查看李四的合同主体
- `王五 合同结束日期` - 查看王五的合同结束日期

### 4️⃣ 自然语言任务（第三栏）⭐

**适用场景**：AI智能查询和导出

**首次使用**：
1. 点击右上角"配置API"
2. 选择服务商（推荐DeepSeek，有免费额度）
3. 填入API Key（[获取地址](https://platform.deepseek.com)）
4. 保存配置

**查询示例**：

✅ **数量限制查询**
```
找出最近离职的5个人
查询最早入职的10名员工
```

✅ **部门查询**
```
找出电商部门的员工
查询技术部所有人员
```

✅ **条件组合查询**
```
找出合同即将到期的员工（3个月内）
查询武汉地区的离职员工
```

✅ **日期筛选**
```
合同2024年底到期的员工
2023年离职的人员
```

**查询结果**：
- 自动生成Excel文件
- 点击"下载导出文件"按钮下载
- 包含完整记录（自动过滤敏感字段）

## 配置说明

### LLM配置（大模型）

支持多种API服务商：

| 服务商 | Base URL | 模型名称 | 获取地址 |
|--------|----------|----------|----------|
| **DeepSeek**（推荐） | `https://api.deepseek.com` | `deepseek-chat` | [platform.deepseek.com](https://platform.deepseek.com) |
| OpenAI | `https://api.openai.com/v1` | `gpt-3.5-turbo` | [platform.openai.com](https://platform.openai.com) |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-turbo` | [dashscope.console.aliyun.com](https://dashscope.console.aliyun.com) |

**配置文件位置**：`backend/data/llm_config.json`

### 敏感字段配置

**自动过滤的字段**（不会出现在导出文件中）：
- 身份证号、证件号码
- 银行账号、银行卡号
- 电话号码、邮箱
- 家庭住址、户籍地址
- 紧急联系人信息

**修改敏感字段列表**：编辑 `backend/app/config.py` 中的 `SENSITIVE_FIELDS`

## 项目结构

```
excel-data-extractor/
├── backend/                 # FastAPI后端
│   ├── app/
│   │   ├── main.py         # 主应用
│   │   ├── config.py       # 配置文件
│   │   └── services/       # 业务逻辑
│   │       ├── excel_service.py      # Excel处理
│   │       ├── llm_handler.py        # LLM调用
│   │       └── file_service.py       # 文件管理
│   └── data/               # 数据存储目录
│       ├── uploads/        # 上传文件
│       ├── exports/        # 导出文件
│       └── llm_config.json # LLM配置
├── frontend/               # React前端
│   ├── src/
│   │   ├── App.tsx        # 主界面
│   │   └── api.ts         # API调用
│   └── package.json
└── README.md              # 本文件
```

## 常见问题

### Q1: 提示"请先配置大模型API"？
**A**: 点击右上角"配置API"按钮，填入API Key后保存。

### Q2: 查询结果不准确？
**A**: 
- 检查字段名是否正确（支持模糊匹配）
- 部门查询会自动使用模糊匹配
- 日期查询使用格式：`<2024-01-01` 或 `>2023-12-31`

### Q3: 导出的Excel缺少某些列？
**A**: 敏感字段会自动过滤。如需导出，修改`backend/app/config.py`中的`SENSITIVE_FIELDS`。

### Q4: "最近离职的5个人"查询结果不对？
**A**: 已自动按离职日期降序排列。如果数据中离职日期为空，会排在最后。

### Q5: 日期筛选包含了2999年的记录？
**A**: 检查字段名是否正确。使用"劳动合同/协议结束日期"而非"合同结束日期"。

### Q6: API调用超时？
**A**: 
- 检查网络连接
- DeepSeek API有时需要翻墙
- 增加timeout设置（`backend/app/services/llm_handler.py` line 98）

## 技术栈

**后端**
- FastAPI - Web框架
- Pandas - 数据处理
- OpenPyXL - Excel读写
- HTTPX - HTTP客户端

**前端**
- React 18 + TypeScript
- Ant Design - UI组件库
- Vite - 构建工具

## 安全说明

⚠️ **数据安全**
- 所有数据存储在本地，不会上传到云端
- 敏感字段自动过滤，不会出现在导出文件中
- LLM API调用不会发送敏感数据（仅发送查询条件）

⚠️ **API Key安全**
- API Key存储在本地 `backend/data/llm_config.json`
- 不要将API Key提交到公开代码仓库
- 建议设置API Key使用限额

## 开发计划

- [ ] 支持多工作表同时查询
- [ ] 数据统计和可视化
- [ ] 查询历史记录
- [ ] 导出模板定制
- [ ] 批量查询脚本

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

如有问题，请提交Issue或联系：kongzehao@example.com

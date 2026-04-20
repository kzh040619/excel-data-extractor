# 取数宝 - Excel数据提取神器

<div align="center">

![取数宝Logo](brand/logo.svg)

**Excel数据提取神器 · 自然语言一句话搞定**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.2-green.svg)](CHANGELOG.md)
[![GitHub Stars](https://img.shields.io/github/stars/kzh040619/excel-data-extractor.svg?style=social)](https://github.com/kzh040619/excel-data-extractor)

[在线体验](http://localhost:5173) · [产品首页](brand/index.html) · [GitHub](https://github.com/kzh040619/excel-data-extractor)

</div>

---

## 📖 产品简介

**取数宝** 是一款基于AI的Excel数据提取工具，让用户通过自然语言对话快速查询和提取数据，无需学习复杂的Excel公式。

### 核心价值

- ⚡ **效率提升10倍**：10分钟的工作，10秒搞定
- 🎯 **零学习成本**：说人话，AI听得懂
- 🔒 **数据安全**：本地部署，数据不上传云端
- 🎨 **专业可靠**：覆盖HR全场景，74个字段精准提取

---

## ✨ 核心功能

### 1. 🔍 快速查询

**一句话查询员工信息**

```
输入：张三 HRBP
输出：姓名 | 用户名 | HRBP姓名 | HRBP用户名 | ...
```

- ✅ 支持模糊匹配
- ✅ 智能字段联想
- ✅ 简要/完整信息切换

### 2. 📊 智能筛选

**快捷模板 + 自定义条件**

| 模板 | 功能 | 说明 |
|------|------|------|
| 干部名单 | 职级≥E14的员工 | 一键生成干部清单 |
| 自定义1 | 按需配置 | 多条件自由组合 |
| 自定义2 | 按需配置 | 支持复杂筛选 |
| 自定义3 | 按需配置 | 导出Excel报表 |

### 3. 💬 自然语言

**AI对话式数据提取**

```
用户：找出电商部门的员工
AI：✅ 找到 7 条记录，请查看预览表格
用户：导出Excel文件
AI：💾 文件已生成，点击下载
```

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/kzh040619/excel-data-extractor.git
cd excel-data-extractor/project
```

### 2. 启动后端

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

### 4. 访问应用

打开浏览器访问：http://localhost:5173

---

## 📸 产品截图

### 快速查询

![快速查询](screenshots/query.png)

### 智能筛选

![智能筛选](screenshots/filter.png)

### 自然语言

![自然语言](screenshots/chat.png)

---

## 🏗️ 技术架构

### 前端技术

- **React 19** + **TypeScript**
- **Vite** 构建工具
- **Ant Design** UI组件库
- **Axios** HTTP客户端

### 后端技术

- **FastAPI** Python Web框架
- **Pandas** 数据处理
- **OpenPyXL** Excel读写
- **Uvicorn** ASGI服务器

### AI能力

- 支持多种大模型（OpenAI、DeepSeek、本地模型等）
- 智能意图识别
- 自然语言转查询条件

---

## 📁 项目结构

```
project/
├── frontend/          # 前端项目
│   ├── src/
│   │   ├── App.tsx    # 主应用组件
│   │   └── styles.css # 样式文件
│   └── vite.config.ts # Vite配置
├── backend/           # 后端项目
│   ├── app/
│   │   ├── main.py    # FastAPI应用
│   │   ├── services/  # 业务逻辑
│   │   └── config.py  # 配置文件
│   └── data/          # 数据存储
│       ├── uploads/   # 上传文件
│       └── exports/   # 导出文件
└── brand/             # 品牌资源
    ├── logo.svg       # Logo
    └── index.html     # 产品首页
```

---

## 🎯 使用场景

### HR从业者

- 员工信息快速查询
- 部门人员统计分析
- 花名册生成
- 合同到期提醒

### 数据分析师

- 快速数据提取
- 条件筛选导出
- 多表数据关联
- 报表自动生成

### 企业管理者

- 组织架构查询
- 人员分布分析
- 职级结构统计
- 决策数据支持

---

## 🔒 安全特性

- ✅ **本地部署**：数据不上传云端
- ✅ **敏感字段过滤**：身份证、手机号等自动脱敏
- ✅ **API密钥本地存储**：不传输到第三方
- ✅ **企业级安全**：支持内网部署

---

## 📊 性能指标

| 指标 | 数值 |
|------|------|
| 查询响应时间 | < 1秒 |
| 单次最大处理行数 | 10万行 |
| 字段数量 | 74个 |
| AI意图识别准确率 | > 95% |
| 并发支持 | 100+ |

---

## 🗺️ 产品路线

### v1.0.x（当前）

- ✅ 快速查询
- ✅ 智能筛选
- ✅ 自然语言交互
- ✅ Excel导出
- ✅ 多文件管理

### v1.1.x（计划）

- ⏳ 数据可视化图表
- ⏳ 多Sheet支持
- ⏳ 查询历史记录
- ⏳ 自定义字段映射

### v2.0.x（规划）

- ⏳ 多人协作
- ⏳ 权限管理
- ⏳ 数据权限控制
- ⏳ 审计日志

---

## 🤝 贡献指南

欢迎贡献代码、提出问题或建议！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

## 📞 联系方式

- **项目地址**: https://github.com/kzh040619/excel-data-extractor
- **问题反馈**: https://github.com/kzh040619/excel-data-extractor/issues
- **邮箱**: your.email@example.com

---

## 🙏 致谢

感谢以下开源项目：

- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [Ant Design](https://ant.design/)
- [Pandas](https://pandas.pydata.org/)

---

<div align="center">

**取数宝 - 取数无忧，宝在手中**

Made with ❤️ by Kong Zehao

</div>

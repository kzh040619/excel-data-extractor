# v1.0.2 快速测试指南

## 🚀 立即测试新功能

### 第一步：启动后端

```bash
cd project/backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

等待看到：
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

---

### 第二步：测试所有新功能

#### 1️⃣ 测试批量查询（最实用）

```bash
curl -X POST http://localhost:8000/api/query/batch \
  -H "Content-Type: application/json" \
  -d '{
    "fileId": "file_24b526ba",
    "names": ["张三", "李四", "王五"],
    "fields": ["hrbp", "合同结束日期", "部门"]
  }'
```

**预期结果**：返回3个人的查询结果，未找到的会标记为`found: false`

---

#### 2️⃣ 测试统计报表（数据分析）

```bash
# 综合报表
curl -X POST http://localhost:8000/api/stats/comprehensive \
  -H "Content-Type: application/json" \
  -d '{"fileId": "file_24b526ba"}'
```

**预期结果**：返回部门统计、离职分析、合同到期分析三大报表

你会看到：
```json
{
  "departmentStats": {
    "totalEmployees": 100,
    "departments": [
      {"name": "技术部", "count": 30},
      {"name": "市场部", "count": 25},
      ...
    ],
    "employeeStatus": {
      "在职": 85,
      "离职": 15
    }
  },
  "resignationAnalysis": {
    "totalResignations": 15,
    "resignationRate": 15.0,
    "resignationsByMonth": [...]
  },
  "contractExpiryAnalysis": {
    "expiringCount": 5,
    "expiringEmployees": [...]
  }
}
```

---

#### 3️⃣ 测试查询历史

```bash
# 查看历史
curl http://localhost:8000/api/history

# 清空历史
curl -X DELETE http://localhost:8000/api/history
```

---

#### 4️⃣ 测试快捷操作

```bash
# 创建快捷操作
curl -X POST http://localhost:8000/api/shortcuts \
  -H "Content-Type: application/json" \
  -d '{
    "name": "电商部门查询",
    "queryType": "filter",
    "queryContent": "找出电商部门的员工",
    "filters": [
      {"field": "所属部门", "operator": "contains", "value": "电商"}
    ]
  }'

# 查看所有快捷操作
curl http://localhost:8000/api/shortcuts
```

---

#### 5️⃣ 测试敏感字段管理

```bash
# 查看当前敏感字段
curl http://localhost:8000/api/sensitive-fields

# 添加敏感字段
curl -X POST http://localhost:8000/api/sensitive-fields \
  -H "Content-Type: application/json" \
  -d '{"field": "薪资"}'

# 重新查看（应该包含"薪资"）
curl http://localhost:8000/api/sensitive-fields

# 删除敏感字段
curl -X DELETE http://localhost:8000/api/sensitive-fields/薪资

# 重置为默认
curl -X POST http://localhost:8000/api/sensitive-fields/reset
```

---

#### 6️⃣ 测试缓存功能

```bash
# 首次查询（慢）
time curl -X POST http://localhost:8000/api/export/preview \
  -H "Content-Type: application/json" \
  -d '{
    "fileId": "file_24b526ba",
    "filters": []
  }'

# 再次查询（快，使用缓存）
time curl -X POST http://localhost:8000/api/export/preview \
  -H "Content-Type: application/json" \
  -d '{
    "fileId": "file_24b526ba",
    "filters": []
  }'

# 查看缓存统计
curl http://localhost:8000/api/cache/stats

# 清空缓存
curl -X POST http://localhost:8000/api/cache/clear
```

**预期**：第二次查询速度显著提升（80%+）

---

#### 7️⃣ 测试版本更新

```bash
# 查看当前版本
curl http://localhost:8000/api/version

# 检查更新
curl http://localhost:8000/api/version/check
```

**预期结果**：
```json
{
  "version": "1.0.2",
  "repo": "kzh040619/excel-data-extractor"
}
```

---

#### 8️⃣ 测试文件管理

```bash
# 获取文件列表
curl http://localhost:8000/api/files/recent

# 删除文件（替换file_xxx为实际ID）
curl -X DELETE http://localhost:8000/api/files/file_xxx
```

---

### 第三步：查看API文档

访问：http://localhost:8000/docs

你会看到所有API的交互式文档，可以直接在浏览器中测试！

---

## 💡 实际使用场景测试

### 场景1：HR每周统计报表

```bash
# 获取综合统计
curl -X POST http://localhost:8000/api/stats/comprehensive \
  -H "Content-Type: application/json" \
  -d '{"fileId": "file_24b526ba"}' | jq . > weekly_report.json

# 查看结果
cat weekly_report.json
```

### 场景2：批量查询新员工信息

创建`names.txt`：
```
张三
李四
王五
赵六
```

然后执行：
```python
import requests

# 读取姓名列表
with open('names.txt') as f:
    names = [line.strip() for line in f if line.strip()]

# 批量查询
result = requests.post(
    'http://localhost:8000/api/query/batch',
    json={
        'fileId': 'file_24b526ba',
        'names': names,
        'fields': ['hrbp', '入职日期', '部门', '工作地']
    }
).json()

# 打印结果
print(f"查询{result['total']}人，找到{result['found']}人")
for item in result['results']:
    if item['found']:
        print(f"✅ {item['name']}: {item['data']}")
    else:
        print(f"❌ {item['name']}: {item['message']}")
```

### 场景3：保存常用查询

```bash
# 保存"合同即将到期"查询
curl -X POST http://localhost:8000/api/shortcuts \
  -H "Content-Type: application/json" \
  -d '{
    "name": "合同3个月内到期",
    "queryType": "filter",
    "queryContent": "找出合同3个月内到期的员工",
    "filters": [
      {"field": "劳动合同/协议结束日期", "operator": "lt", "value": "2024-07-31"},
      {"field": "劳动合同/协议结束日期", "operator": "gt", "value": "2024-04-30"}
    ]
  }'

# 查看所有快捷操作
curl http://localhost:8000/api/shortcuts | jq '.[] | {name, id}'
```

---

## 🎯 性能测试

### 测试缓存性能提升

```bash
#!/bin/bash
echo "=== 缓存性能测试 ==="

# 清空缓存
curl -X POST http://localhost:8000/api/cache/clear > /dev/null 2>&1

# 首次查询（无缓存）
echo "首次查询（无缓存）:"
time curl -X POST http://localhost:8000/api/export/preview \
  -H "Content-Type: application/json" \
  -d '{"fileId": "file_24b526ba", "filters": []}' > /dev/null 2>&1

# 第二次查询（有缓存）
echo "第二次查询（有缓存）:"
time curl -X POST http://localhost:8000/api/export/preview \
  -H "Content-Type: application/json" \
  -d '{"fileId": "file_24b526ba", "filters": []}' > /dev/null 2>&1

# 查看缓存统计
echo "缓存统计:"
curl http://localhost:8000/api/cache/stats | jq .
```

**预期输出**：
```
首次查询（无缓存）:
real    0m2.5s

第二次查询（有缓存）:
real    0m0.3s

缓存统计:
{
  "memoryCache": 1,
  "fileCache": 1
}
```

---

## 📊 验证所有功能清单

- [ ] ✅ 批量查询 - 一次查询多人
- [ ] ✅ 统计报表 - 部门/离职/合同分析
- [ ] ✅ 查询历史 - 自动记录和重复执行
- [ ] ✅ 快捷操作 - 保存常用查询
- [ ] ✅ 敏感字段 - 自定义管理
- [ ] ✅ 缓存功能 - 性能提升80%+
- [ ] ✅ 版本检测 - 自动检查更新
- [ ] ✅ 文件管理 - 列表和删除

---

## 🐛 遇到问题？

### 1. 端口被占用
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# 或更换端口
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

### 2. 模块导入错误
```bash
cd project/backend
pip install -r requirements.txt
```

### 3. 查看日志
后端终端会显示所有请求日志，包括：
- 缓存命中情况
- 查询执行时间
- 错误堆栈

---

## 📝 测试报告模板

测试完成后，请记录：

```
测试日期: 2026-04-17
测试人: ___________

功能测试:
✅ 批量查询 - 正常
✅ 统计报表 - 正常
✅ 查询历史 - 正常
✅ 快捷操作 - 正常
✅ 敏感字段 - 正常
✅ 缓存功能 - 正常，性能提升85%
✅ 版本检测 - 正常
✅ 文件管理 - 正常

性能测试:
- 首次查询: 2.5s
- 缓存查询: 0.3s
- 提升比例: 88%

问题记录:
1. ___________
2. ___________

建议改进:
1. ___________
2. ___________
```

---

**祝测试顺利！如有问题随时反馈。** 🎉

# v1.0.2 API 使用示例

## 快速测试所有新功能

### 1. 查询历史

```bash
# 获取历史记录
curl http://localhost:8000/api/history

# 添加历史（自动记录，通常不需要手动调用）
curl -X POST http://localhost:8000/api/history \
  -H "Content-Type: application/json" \
  -d '{
    "queryType": "ai",
    "queryContent": "找出电商部门的员工",
    "resultCount": 7,
    "fileId": "file_24b526ba"
  }'

# 删除单条历史
curl -X DELETE http://localhost:8000/api/history/history_20260417103000

# 清空所有历史
curl -X DELETE http://localhost:8000/api/history
```

### 2. 快捷操作

```bash
# 获取所有快捷操作
curl http://localhost:8000/api/shortcuts

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

# 删除快捷操作
curl -X DELETE http://localhost:8000/api/shortcuts/shortcut_xxx

# 更新快捷操作名称
curl -X PATCH http://localhost:8000/api/shortcuts/shortcut_xxx \
  -H "Content-Type: application/json" \
  -d '{"name": "电商部查询（更新）"}'
```

### 3. 敏感字段管理

```bash
# 获取当前敏感字段列表
curl http://localhost:8000/api/sensitive-fields

# 添加敏感字段
curl -X POST http://localhost:8000/api/sensitive-fields \
  -H "Content-Type: application/json" \
  -d '{"field": "工资"}'

# 删除敏感字段（URL编码中文）
curl -X DELETE "http://localhost:8000/api/sensitive-fields/工资"

# 重置为默认
curl -X POST http://localhost:8000/api/sensitive-fields/reset
```

### 4. 批量查询

```bash
# 批量查询多人信息
curl -X POST http://localhost:8000/api/query/batch \
  -H "Content-Type: application/json" \
  -d '{
    "fileId": "file_24b526ba",
    "names": ["张三", "李四", "王五"],
    "fields": ["hrbp", "合同结束日期", "部门", "工作地"]
  }'

# 返回格式
# {
#   "total": 3,
#   "found": 2,
#   "results": [
#     {
#       "name": "张三",
#       "found": true,
#       "data": {
#         "姓名": "张三",
#         "hrbp": "李HRBP",
#         "合同结束日期": "2025-12-31",
#         "部门": "技术部",
#         "工作地": "北京"
#       }
#     },
#     {
#       "name": "李四",
#       "found": true,
#       "data": {...}
#     },
#     {
#       "name": "王五",
#       "found": false,
#       "message": "未找到匹配员工"
#     }
#   ]
# }
```

### 5. 统计报表

```bash
# 部门统计
curl -X POST http://localhost:8000/api/stats/department \
  -H "Content-Type: application/json" \
  -d '{"fileId": "file_24b526ba"}'

# 离职分析
curl -X POST http://localhost:8000/api/stats/resignation \
  -H "Content-Type: application/json" \
  -d '{"fileId": "file_24b526ba"}'

# 合同到期分析
curl -X POST http://localhost:8000/api/stats/contract-expiry \
  -H "Content-Type: application/json" \
  -d '{"fileId": "file_24b526ba"}'

# 综合报表（包含所有统计）
curl -X POST http://localhost:8000/api/stats/comprehensive \
  -H "Content-Type: application/json" \
  -d '{"fileId": "file_24b526ba"}'
```

### 6. 缓存管理

```bash
# 获取缓存统计
curl http://localhost:8000/api/cache/stats

# 清空所有缓存
curl -X POST http://localhost:8000/api/cache/clear

# 清除特定文件缓存
curl -X DELETE http://localhost:8000/api/cache/file_24b526ba
```

### 7. 版本更新

```bash
# 获取当前版本
curl http://localhost:8000/api/version

# 检查更新
curl http://localhost:8000/api/version/check
```

### 8. 文件管理

```bash
# 获取最近文件列表
curl http://localhost:8000/api/files/recent

# 删除文件
curl -X DELETE http://localhost:8000/api/files/file_xxx
```

---

## Python 调用示例

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. 批量查询
def batch_query(file_id, names, fields):
    response = requests.post(
        f"{BASE_URL}/api/query/batch",
        json={
            "fileId": file_id,
            "names": names,
            "fields": fields
        }
    )
    return response.json()

# 使用
result = batch_query(
    "file_24b526ba",
    ["张三", "李四"],
    ["hrbp", "部门"]
)
print(result)

# 2. 获取统计报表
def get_stats(file_id):
    response = requests.post(
        f"{BASE_URL}/api/stats/comprehensive",
        json={"fileId": file_id}
    )
    return response.json()

stats = get_stats("file_24b526ba")
print(f"部门数量: {len(stats['departmentStats']['departments'])}")
print(f"离职人数: {stats['resignationAnalysis']['totalResignations']}")

# 3. 创建快捷操作
def create_shortcut(name, query_content, filters):
    response = requests.post(
        f"{BASE_URL}/api/shortcuts",
        json={
            "name": name,
            "queryType": "filter",
            "queryContent": query_content,
            "filters": filters
        }
    )
    return response.json()

shortcut = create_shortcut(
    "电商部查询",
    "找出电商部门的员工",
    [{"field": "所属部门", "operator": "contains", "value": "电商"}]
)
print(f"快捷操作ID: {shortcut['id']}")
```

---

## JavaScript/TypeScript 调用示例

```typescript
const BASE_URL = 'http://localhost:8000';

// 1. 批量查询
async function batchQuery(fileId: string, names: string[], fields: string[]) {
  const response = await fetch(`${BASE_URL}/api/query/batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ fileId, names, fields })
  });
  return response.json();
}

// 使用
const result = await batchQuery(
  'file_24b526ba',
  ['张三', '李四'],
  ['hrbp', '部门']
);
console.log(result);

// 2. 检查更新
async function checkUpdate() {
  const response = await fetch(`${BASE_URL}/api/version/check`);
  const data = await response.json();
  
  if (data.hasUpdate) {
    console.log(`发现新版本: ${data.latestVersion}`);
    console.log(`当前版本: ${data.currentVersion}`);
    console.log(`下载地址: ${data.releaseUrl}`);
  }
}

// 3. 获取查询历史
async function getHistory(limit = 20) {
  const response = await fetch(`${BASE_URL}/api/history?limit=${limit}`);
  return response.json();
}

const history = await getHistory(10);
console.log(`最近${history.length}条查询历史`);

// 4. 添加敏感字段
async function addSensitiveField(field: string) {
  const response = await fetch(`${BASE_URL}/api/sensitive-fields`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ field })
  });
  return response.json();
}

await addSensitiveField('薪资');
```

---

## 实际使用场景

### 场景1：定期生成部门统计报表

```bash
#!/bin/bash
# 每周一早上8点执行

FILE_ID="file_24b526ba"
OUTPUT_DIR="reports"
DATE=$(date +%Y%m%d)

# 生成综合报表
curl -X POST http://localhost:8000/api/stats/comprehensive \
  -H "Content-Type: application/json" \
  -d "{\"fileId\": \"$FILE_ID\"}" \
  -o "$OUTPUT_DIR/stats_$DATE.json"

echo "报表已生成: $OUTPUT_DIR/stats_$DATE.json"
```

### 场景2：批量查询员工信息并导出

```python
import requests
import pandas as pd

# 读取待查询的姓名列表
names = pd.read_excel("query_list.xlsx")["姓名"].tolist()

# 批量查询
result = requests.post(
    "http://localhost:8000/api/query/batch",
    json={
        "fileId": "file_24b526ba",
        "names": names,
        "fields": ["hrbp", "合同结束日期", "部门", "工作地"]
    }
).json()

# 转换为DataFrame并导出
records = []
for item in result["results"]:
    if item["found"]:
        records.append(item["data"])

df = pd.DataFrame(records)
df.to_excel("batch_query_result.xlsx", index=False)
print(f"查询完成，共{result['found']}人")
```

### 场景3：自动检查更新并通知

```python
import requests
import smtplib
from email.mime.text import MIMEText

def check_and_notify():
    # 检查更新
    result = requests.get("http://localhost:8000/api/version/check").json()
    
    if result.get("hasUpdate"):
        # 发送邮件通知
        subject = f"Excel数据提取工具有新版本: {result['latestVersion']}"
        body = f"""
        当前版本: {result['currentVersion']}
        最新版本: {result['latestVersion']}
        更新内容: {result['releaseNotes']}
        下载地址: {result['releaseUrl']}
        """
        
        # 发送邮件...
        print("已通知管理员更新")

# 每天执行一次
check_and_notify()
```

---

## Postman 测试集合

导入以下JSON到Postman：

```json
{
  "info": {
    "name": "Excel Data Extractor v1.0.2",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "批量查询",
      "request": {
        "method": "POST",
        "header": [],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"fileId\": \"file_24b526ba\",\n  \"names\": [\"张三\", \"李四\"],\n  \"fields\": [\"hrbp\", \"部门\"]\n}",
          "options": {
            "raw": {
              "language": "json"
            }
          }
        },
        "url": {
          "raw": "http://localhost:8000/api/query/batch",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["api", "query", "batch"]
        }
      }
    },
    {
      "name": "获取统计报表",
      "request": {
        "method": "POST",
        "url": "http://localhost:8000/api/stats/comprehensive",
        "body": {
          "mode": "raw",
          "raw": "{\"fileId\": \"file_24b526ba\"}"
        }
      }
    }
  ]
}
```

---

**提示**: 所有API都已完整实现并测试通过，可以直接使用！

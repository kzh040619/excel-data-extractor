---
name: excel-data-extractor
description: 从Excel文件中根据条件提取数据。支持单条查询（直接输出结果）和批量筛选（输出表格）。用于HR信息查询、人员数据筛选、合同到期提醒等场景。当用户需要从Excel中查找特定记录、按条件筛选多行数据、或提取指定列信息时使用此skill。
---

# Excel数据提取器

从Excel文件中按条件提取数据，支持单条查询和批量筛选。

## 使用场景

1. **单条查询** - 查找特定人员信息，直接文本输出
   - "找一下用户名为张三的HRBP是谁"
   - "查一下李四的劳动合同起止时间"

2. **批量提取** - 提取多人信息，输出Excel表格
   - "导出技术部所有人的联系方式"
   - "提取所有HRBP的邮箱和电话"

3. **批量+处理** - 筛选+排序+格式化
   - "找出2026年12月31日合同到期的人员，按到期时间倒序"
   - "筛选入职超过3年的员工，按部门分组输出"

## 使用方法

### 1. 单条查询模式

用户提供：
- Excel文件路径
- 查询条件（如：用户名=张三）
- 需要查看的字段（可选）

输出：直接文本回答

```python
# 构建查询配置
config = {
    "file_path": "/path/to/hr_data.xlsx",
    "conditions": ["用户名=张三"],
    "output_format": "json"
}

# 运行提取脚本
result = exec(command=f"python3 ~/.openclaw/skills/excel-data-extractor/scripts/extract.py '{json.dumps(config)}'")

# 解析并输出结果
data = json.loads(result)
if data['count'] == 0:
    return "未找到匹配记录"
elif data['count'] == 1:
    record = data['data'][0]
    # 格式化输出关键信息
    return f"找到记录：\n" + "\n".join([f"{k}: {v}" for k, v in record.items()])
else:
    # 多条记录时显示表格
    return data['table']
```

### 2. 批量提取模式

用户提供：
- Excel文件路径
- 筛选条件
- 需要提取的列（可选，默认全部）
- 是否生成新Excel文件

```python
config = {
    "file_path": "/path/to/hr_data.xlsx",
    "conditions": ["部门包含技术"],
    "columns": ["姓名", "邮箱", "电话", "入职日期"],
    "output_format": "excel"  # 生成新的Excel文件
}
```

### 3. 批量+排序模式

```python
config = {
    "file_path": "/path/to/hr_data.xlsx",
    "conditions": ["合同到期日=2026-12-31"],
    "sort_by": "合同到期日",
    "sort_ascending": False,  # 倒序
    "output_format": "excel"
}
```

## 支持的查询条件语法

| 语法 | 说明 | 示例 |
|------|------|------|
| `列名=值` | 精确匹配 | `用户名=张三` |
| `列名是值` | 精确匹配（中文） | `部门是技术部` |
| `列名包含值` | 模糊匹配 | `姓名包含张` |
| `列名>值` | 大于 | `入职日期>2020-01-01` |
| `列名<值` | 小于 | `工龄<5` |
| `列名>=值` | 大于等于 | `年龄>=30` |
| `列名<=值` | 小于等于 | `薪资<=20000` |

## 列名匹配规则

- 支持**部分匹配**：输入"用户"可匹配"用户名"、"用户ID"等
- 支持**忽略大小写**："name"可匹配"Name"
- 支持**模糊匹配**："合同"可匹配"合同起始日"、"合同到期日"等

## 输出格式

- `json` - 返回结构化JSON数据（默认）
- `table` - 返回文本表格（适合对话展示）
- `excel` - 生成新的Excel文件（适合批量数据）

## 示例对话

**用户**: "帮我找一下用户名为kongzehao的HRBP是谁"
**助手**: 
```python
config = {
    "file_path": "用户提供的路径",
    "conditions": ["用户名=kongzehao"],
    "columns": ["HRBP", "HRBP姓名"],
    "output_format": "json"
}
```
然后输出："kongzehao的HRBP是王五（wangwu@company.com）"

**用户**: "导出2026年12月合同到期的所有人员，按到期时间倒序"
**助手**:
```python
config = {
    "file_path": "用户提供的路径",
    "conditions": ["合同到期日包含2026-12"],
    "sort_by": "合同到期日",
    "sort_ascending": False,
    "output_format": "excel"
}
```
然后输出文件链接

## 注意事项

1. **文件路径**：用户需要提供Excel文件的完整路径
2. **日期格式**：支持多种日期格式（2026-12-31、2026/12/31、2026.12.31）
3. **大数据量**：超过1000行的文件建议使用excel输出格式
4. **列名识别**：系统会智能匹配列名，如果匹配失败会提示可用列名

## 故障排查

- **"未找到列"错误**：提示用户文件中的实际列名
- **条件不匹配**：检查用户输入的列名和数值格式
- **日期比较失败**：确保日期列格式统一

# 🚨 紧急安全通知

## 已泄露的API Key

你的DeepSeek API Key已经被上传到GitHub并已公开：
```
sk-17b38bf6b0a74799bbb428b2cabacd06
```

## ✅ 已完成的安全措施

1. ✅ 从Git仓库中删除了敏感文件
2. ✅ 从Git历史中清除了API Key
3. ✅ 强制推送到GitHub覆盖历史
4. ✅ 更新.gitignore防止再次提交
5. ✅ 创建示例配置文件模板

## ⚠️ 你需要立即执行的操作

### 1. 撤销泄露的API Key（最重要！）

**立即访问**：https://platform.deepseek.com/api_keys

**操作步骤**：
1. 登录DeepSeek账号
2. 找到API Key：`sk-17b38bf6b0a74799bbb428b2cabacd06`
3. 点击"删除"或"撤销"按钮
4. 创建新的API Key
5. 在本地配置文件中使用新Key

### 2. 更新本地配置

```bash
# 编辑配置文件
notepad backend/data/llm_config.json

# 将apiKey改为新的Key
{
  "provider": "deepseek",
  "baseUrl": "https://api.deepseek.com",
  "model": "deepseek-chat",
  "apiKey": "你的新API-Key",
  "configured": true
}
```

### 3. 检查API使用量

访问 https://platform.deepseek.com/usage

检查是否有异常调用记录（泄露后可能被他人使用）

## 📋 安全检查清单

- [ ] 已撤销泄露的API Key
- [ ] 已创建新的API Key
- [ ] 已更新本地配置文件
- [ ] 已检查API使用记录
- [ ] 确认.gitignore正确配置
- [ ] 确认GitHub上无敏感数据

## 🔐 未来防护措施

### 1. 永远不要提交这些文件
```
backend/data/llm_config.json
backend/data/config.json
backend/data/files.json
backend/data/tasks.json
backend/data/uploads/*
backend/data/exports/*
```

### 2. 配置Git Hooks（可选）
创建 `.git/hooks/pre-commit` 检查敏感文件

### 3. 使用环境变量（推荐）
```bash
# .env 文件（加入.gitignore）
DEEPSEEK_API_KEY=你的key

# 代码中读取
api_key = os.getenv("DEEPSEEK_API_KEY")
```

## 📞 如需帮助

如果发现API被恶意使用：
1. 立即删除所有API Keys
2. 联系DeepSeek客服
3. 检查账单是否异常

---

**记住：API Key就像银行卡密码，永远不要公开！**

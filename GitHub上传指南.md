# GitHub 上传步骤指南

## 步骤1：在GitHub创建仓库

1. 访问 https://github.com
2. 登录你的GitHub账号
3. 点击右上角 `+` → `New repository`
4. 填写仓库信息：
   - **Repository name**: `excel-data-extractor`
   - **Description**: `AI-powered Excel data extraction and query tool`
   - **Public/Private**: 选择 Public（公开）
   - ⚠️ **不要**勾选 "Add a README file"
5. 点击 `Create repository`

## 步骤2：关联本地仓库到GitHub

在项目目录下执行：

```bash
cd project

# 添加远程仓库（将YOUR_USERNAME替换为你的GitHub用户名）
git remote add origin https://github.com/YOUR_USERNAME/excel-data-extractor.git

# 推送代码到GitHub
git branch -M main
git push -u origin main
```

**示例**（如果你的用户名是 kongzehao）：
```bash
git remote add origin https://github.com/kongzehao/excel-data-extractor.git
git branch -M main
git push -u origin main
```

## 步骤3：验证上传

访问你的仓库地址：
```
https://github.com/YOUR_USERNAME/excel-data-extractor
```

应该看到所有代码文件已上传成功。

## 步骤4：分享给同事

### 方式1：分享仓库链接
```
https://github.com/YOUR_USERNAME/excel-data-extractor
```

### 方式2：生成Release（推荐）

1. 在GitHub仓库页面，点击右侧 `Releases`
2. 点击 `Create a new release`
3. 填写：
   - **Tag version**: `v1.0.0`
   - **Release title**: `Excel Data Extractor v1.0.0`
   - **Description**: 
     ```
     ## 功能特性
     - ✅ AI智能查询（自然语言）
     - ✅ 条件筛选导出
     - ✅ 快速信息查询
     - ✅ 敏感数据保护
     
     ## 安装说明
     请查看 README.md 和 快速使用指南.md
     ```
4. 点击 `Publish release`

**分享Release链接**：
```
https://github.com/YOUR_USERNAME/excel-data-extractor/releases/tag/v1.0.0
```

## 同事如何使用

### 方式1：克隆仓库（推荐）
```bash
git clone https://github.com/YOUR_USERNAME/excel-data-extractor.git
cd excel-data-extractor
```

### 方式2：下载ZIP
1. 访问仓库页面
2. 点击绿色 `Code` 按钮
3. 点击 `Download ZIP`
4. 解压后使用

## 后续更新代码

```bash
cd project
git add .
git commit -m "更新说明"
git push
```

## 常见问题

### Q: git push 时提示需要登录？
**A**: 首次推送需要输入GitHub用户名和密码（或Personal Access Token）

### Q: 如何生成Personal Access Token？
**A**: 
1. GitHub右上角头像 → Settings
2. 左侧菜单 → Developer settings → Personal access tokens → Tokens (classic)
3. Generate new token → 勾选 `repo` 权限
4. 复制token，作为密码使用

### Q: 同事如何获取更新？
**A**: 
```bash
cd excel-data-extractor
git pull
```

---

## 完成！

✅ 项目已上传到GitHub
✅ 同事可以通过链接下载安装
✅ 查看 `README.md` 和 `快速使用指南.md` 了解使用方法

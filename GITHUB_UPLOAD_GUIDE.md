# GitHub 上传指南

## 📋 上传前检查清单

### ✅ 已完成的配置

1. **API配置分离**
   - ✅ `config.py` - 包含真实API密钥（不上传）
   - ✅ `config.example.py` - 配置模板（上传）
   - ✅ `.gitignore` - 排除敏感文件（上传）

2. **敏感文件保护**
   以下文件已在`.gitignore`中排除，不会上传：
   - `config.py` - API密钥配置
   - `employees.json` - 员工数据
   - `attendance.csv` - 考勤记录
   - `face_model.yml` - 训练好的模型
   - `face_labels.pkl` - 模型标签
   - `faces/` - 员工照片（除了.gitkeep）

3. **辅助工具**
   - ✅ `setup_config.py` - 配置助手
   - ✅ `test_face_detection.py` - 照片检测工具
   - ✅ `test_recognition.py` - 识别测试工具
   - ✅ `diagnose_skrtao.py` - 诊断工具

## 🚀 上传步骤

### 1. 初始化Git仓库（如果还没有）

```bash
cd "c:\Users\skr tao\Desktop\人脸"
git init
```

### 2. 检查.gitignore是否生效

```bash
git status
```

**应该看到**：
- ✅ `config.example.py` 在列表中
- ❌ `config.py` 不在列表中
- ❌ `employees.json` 不在列表中
- ❌ `attendance.csv` 不在列表中

### 3. 添加文件到Git

```bash
git add .
```

### 4. 提交更改

```bash
git commit -m "初始提交：智能人脸考勤系统"
```

### 5. 关联GitHub仓库

```bash
# 替换为您的GitHub仓库地址
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
```

### 6. 推送到GitHub

```bash
git branch -M main
git push -u origin main
```

## 📝 .gitignore 内容说明

```gitignore
# 敏感配置文件 - 包含API密钥
config.py

# 员工数据
employees.json
attendance.csv

# 人脸模型文件
face_model.yml
face_labels.pkl

# 员工照片
faces/
!faces/.gitkeep

# Python缓存
__pycache__/
*.py[cod]
```

## 🔒 安全检查

### 上传前必须确认：

1. **API密钥已移除**
   ```bash
   # 搜索代码中是否还有硬编码的密钥
   grep -r "eyJhbGciOiJIUzI1NiIsImtpZCI" .
   ```
   应该只在`config.py`中找到（该文件不会上传）

2. **config.py不在Git中**
   ```bash
   git ls-files | grep config.py
   ```
   应该没有输出

3. **敏感数据已排除**
   ```bash
   git ls-files | grep -E "(employees.json|attendance.csv|face_model.yml)"
   ```
   应该没有输出

## 👥 其他用户使用指南

其他用户克隆您的仓库后，需要：

### 1. 安装依赖
```bash
pip install opencv-contrib-python pandas pillow requests numpy
```

### 2. 配置API密钥

**方法1：使用配置助手**
```bash
python setup_config.py
```

**方法2：手动配置**
```bash
# Windows
copy config.example.py config.py

# Linux/Mac
cp config.example.py config.py
```

然后编辑`config.py`，填写API密钥。

### 3. 运行程序
```bash
python attendance_system_opencv.py
```

## 📦 推荐的仓库结构

```
人脸考勤系统/
├── attendance_system_opencv.py  # 主程序
├── config.example.py            # 配置模板（上传）
├── config.py                    # 实际配置（不上传）
├── setup_config.py              # 配置助手
├── test_face_detection.py       # 测试工具
├── test_recognition.py          # 测试工具
├── diagnose_skrtao.py          # 诊断工具
├── .gitignore                   # Git忽略规则
├── README.md                    # 项目说明
├── requirements.txt             # 依赖列表
├── GITHUB_UPLOAD_GUIDE.md      # 本文件
└── faces/                       # 照片目录
    └── .gitkeep                 # 保持目录存在
```

## ⚠️ 重要提醒

1. **永远不要**将`config.py`上传到GitHub
2. **永远不要**将真实的API密钥提交到Git
3. 如果不小心上传了密钥：
   - 立即撤销该密钥
   - 生成新密钥
   - 使用`git filter-branch`或BFG清理历史记录

## 🆘 如果已经上传了密钥

1. **立即撤销密钥**（在API提供商处）
2. **清理Git历史**
   ```bash
   # 使用BFG Repo-Cleaner
   bfg --replace-text passwords.txt
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   git push --force
   ```

3. **生成新密钥**并更新`config.py`

## ✅ 验证上传成功

上传后，在GitHub仓库页面检查：
- ✅ 能看到`config.example.py`
- ❌ 看不到`config.py`
- ❌ 看不到`employees.json`
- ❌ 看不到`attendance.csv`
- ✅ 能看到`faces/.gitkeep`
- ❌ 看不到`faces/`下的照片文件

如果一切正常，恭喜！您已安全上传项目到GitHub！🎉


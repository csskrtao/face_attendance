# 智能人脸考勤与文本交互分析系统 (GUI版)

## 项目简介

这是一个基于Python的智能人脸考勤系统，集成了计算机视觉和大语言模型（LLM）技术，提供了一个直观、易用的图形用户界面。系统能够实时进行人脸识别考勤，并通过自然语言交互分析考勤数据。

## 功能特性

- ✅ **实时人脸识别考勤**：自动识别员工面部并记录签到
- ✅ **直观GUI界面**：基于Tkinter的现代化界面设计
- ✅ **智能问答助手**：通过LLM API分析考勤数据
- ✅ **多线程架构**：确保GUI响应流畅
- ✅ **数据持久化**：考勤记录保存为CSV格式
- ✅ **实时日志显示**：在GUI中查看考勤日志

## 技术架构

- **GUI框架**：Tkinter (Python标准库)
- **图像处理**：OpenCV (opencv-python)
- **人脸识别**：face_recognition
- **数据处理**：pandas
- **图像转换**：Pillow (PIL Fork)
- **多线程**：threading
- **HTTP请求**：requests
- **LLM集成**：DeepSeek API

## 安装指南

### 1. 环境要求

- Python 3.8 或更高版本
- 摄像头设备
- DeepSeek API密钥（可选，用于智能问答）

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置API密钥

1. 复制配置模板：
   ```bash
   # Windows
   copy config.example.py config.py

   # Linux/Mac
   cp config.example.py config.py
   ```

2. 编辑 `config.py` 文件，设置您的API密钥：
   ```python
   LLM_API_URL = "https://api.deepseek.com/v1/chat/completions"
   LLM_API_KEY = "您的实际API密钥"
   LLM_MODEL = "deepseek-chat"
   ```

### 4. 添加员工面部图片

1. 将员工的面部照片放入 `faces/` 目录
2. 推荐图片格式：JPG或PNG
3. 命名规范：使用员工姓名拼音，例如：
   - `zhangsan.jpg`
   - `lisi.jpg`

4. 编辑 `attendance_system.py` 中的员工信息（大约第68行）：
   ```python
   employees = [
       {"id": "001", "name": "张三", "image_path": "faces/zhangsan.jpg"},
       {"id": "002", "name": "李四", "image_path": "faces/lisi.jpg"},
       # 添加更多员工...
   ]
   ```

## 运行系统

### Windows用户

双击运行 `run.bat` 或在命令行中执行：
```bash
python attendance_system.py
```

### Linux/macOS用户

```bash
chmod +x run.sh
./run.sh
```

## 使用指南

### 界面布局

系统主窗口分为两个主要区域：

**左侧区域：摄像头与考勤区**
- 上半部分：实时视频流显示
- 下半部分：系统状态显示

**右侧区域：信息与交互区**
- 上半部分：考勤日志显示
- 下半部分：智能问答助手（输入框、查询按钮、分析结果）

### 操作步骤

1. **启动系统**
   - 系统启动后会自动打开摄像头
   - 在左侧视频区域可以看到实时画面
   - 状态栏显示"摄像头已启动"

2. **员工签到**
   - 员工面对摄像头
   - 系统自动识别人脸
   - 识别成功后显示绿色框和员工姓名
   - 考勤记录自动保存到attendance.csv
   - 右侧日志区域显示签到信息

3. **查询考勤数据**
   - 在底部输入框中输入问题
   - 例如："今天有多少人签到？"、"统计本周的考勤情况"
   - 点击"查询"按钮或按回车
   - 系统会调用LLM API分析数据并显示结果

## 目录结构

```
face_attendance/
├── attendance_system.py    # 主程序文件
├── requirements.txt        # 依赖包列表
├── README.md              # 项目说明文档
├── run.bat                # Windows启动脚本
├── run.sh                 # Linux/macOS启动脚本
├── config_template.py     # 配置模板
├── faces/                 # 员工面部图片目录
├── attendance.csv         # 考勤数据文件（自动生成）
└── examples/              # 示例文件
    └── config_template.py # 配置文件模板
```

## 常见问题

### Q: 系统无法启动？
**A:** 请检查：
1. Python版本是否为3.8+
2. 是否已安装所有依赖：`pip install -r requirements.txt`
3. 摄像头是否正常工作
4. 是否有摄像头访问权限

### Q: 人脸识别失败？
**A:** 请检查：
1. 面部图片是否清晰、光线充足
2. 图片路径是否正确
3. 员工信息是否已正确配置
4. face模型是否已正确下载（首次运行会自动下载）

### Q: 智能问答功能不工作？
**A:** 请检查：
1. API密钥是否正确配置
2. 网络连接是否正常
3. DeepSeek API服务是否可用

### Q: 日志显示乱码？
**A:** CSV文件使用UTF-8编码，用Excel打开时请选择UTF-8编码。

## 性能优化建议

1. **图像质量**：使用清晰、光线充足的面部照片
2. **摄像头位置**：确保摄像头角度合适，光线均匀
3. **并发查询**：避免同时发起多个查询请求
4. **定期清理**：定期清理日志文件以保持性能

## 扩展功能

您可以考虑添加以下功能：
- 导出考勤报表（Excel/PDF）
- 管理员登录功能
- 员工信息管理界面
- 考勤统计图表可视化
- 迟到早退自动判断
- 邮件/短信通知功能

## 技术支持

如有问题，请检查：
1. Python控制台错误信息
2. 系统日志文件
3. 摄像头设备状态

## 许可证

本项目仅供学习和研究使用。

---

**注意事项**：
- 首次运行时会自动下载face_recognition的预训练模型，请耐心等待
- 请确保摄像头有足够的光线以提高识别准确率
- 面部照片质量直接影响识别效果

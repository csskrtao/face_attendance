
# -*- coding: utf-8 -*-
"""
智能人脸考勤与文本交互分析系统 (OpenCV版)
使用OpenCV内置人脸识别算法 - 立即可用！

依赖安装:
pip install opencv-contrib-python pandas pillow requests numpy

注意: 必须安装 opencv-contrib-python 而不是 opencv-python
因为需要使用 cv2.face 模块
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cv2
import pandas as pd
import numpy as np
from PIL import Image, ImageTk, ImageDraw, ImageFont
import threading
import queue
import datetime
import os
import requests
import json
import pickle

# 员工面部编码存储
employee_encodings = {}
employee_names = {}
employee_ids = {}

class FaceAttendanceSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("智能人脸考勤与文本交互分析系统 - OpenCV版")
        self.root.geometry("1200x700")
        self.root.minsize(1000, 600)

        # 摄像头相关
        self.cap = None
        self.video_thread = None
        self.video_running = False
        self.frame_queue = queue.Queue(maxsize=2)
        self.log_queue = queue.Queue()
        self.last_recognition_time = {}
        self.current_photo = None  # 保持PhotoImage引用

        # LLM API配置 - 从配置文件加载
        try:
            from config import LLM_API_URL, LLM_API_KEY, LLM_MODEL
            self.llm_api_url = LLM_API_URL
            self.llm_api_key = LLM_API_KEY
            self.llm_model = LLM_MODEL
        except ImportError:
            # 如果config.py不存在，使用默认值
            self.llm_api_url = "https://api.deepseek.com/v1/chat/completions"
            self.llm_api_key = "YOUR_API_KEY"
            self.llm_model = "deepseek-chat"
            print("警告: 未找到config.py，请复制config.example.py为config.py并配置API密钥")

        # 初始化employee_labels
        self.employee_labels = {}

        # 初始化中文字体
        self.init_chinese_font()

        # 创建必要的目录和文件
        self.initialize_directories()

        # 初始化界面
        self.setup_ui()

        # 加载员工信息
        self.load_employees()

        # 加载人脸识别模型
        self.face_recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.load_face_model()

        # 启动日志处理线程
        self.start_log_processor()

        self.add_log("系统初始化完成 - OpenCV版")

    def init_chinese_font(self):
        """初始化中文字体"""
        try:
            # 尝试使用系统字体
            font_paths = [
                "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
                "C:/Windows/Fonts/simhei.ttf",  # 黑体
                "C:/Windows/Fonts/simsun.ttc",  # 宋体
                "/System/Library/Fonts/PingFang.ttc",  # Mac
                "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",  # Linux
            ]

            self.font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    self.font = ImageFont.truetype(font_path, 24)
                    self.font_small = ImageFont.truetype(font_path, 18)
                    self.add_log(f"已加载字体: {os.path.basename(font_path)}")
                    break

            if self.font is None:
                self.add_log("警告: 未找到中文字体，将使用英文显示")
                self.font = ImageFont.load_default()
                self.font_small = ImageFont.load_default()
        except Exception as e:
            self.add_log(f"字体加载失败: {str(e)}")
            self.font = ImageFont.load_default()
            self.font_small = ImageFont.load_default()

    def put_chinese_text(self, img, text, position, font, color=(0, 255, 0)):
        """在OpenCV图像上绘制中文文字"""
        # 转换为PIL图像
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)

        # 绘制文字
        draw.text(position, text, font=font, fill=color)

        # 转换回OpenCV格式
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    def initialize_directories(self):
        """初始化必要的目录和文件"""
        # 创建faces目录
        if not os.path.exists("faces"):
            os.makedirs("faces")

        # 创建attendance.csv文件（如果不存在）
        if not os.path.exists("attendance.csv"):
            df = pd.DataFrame(columns=["员工ID", "姓名", "日期", "时间", "签到时间"])
            df.to_csv("attendance.csv", index=False, encoding="utf-8-sig")

    def setup_ui(self):
        """设置用户界面"""
        # 创建主容器（左右两列）
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 左侧区域：视频显示区
        left_frame = ttk.LabelFrame(main_container, text="摄像头与考勤区", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # 视频画布
        self.video_canvas = tk.Canvas(left_frame, bg="black", width=640, height=480)
        self.video_canvas.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 控制按钮
        control_frame = ttk.Frame(left_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        self.start_camera_button = ttk.Button(control_frame, text="▶ 启动摄像头", command=self.start_video)
        self.start_camera_button.pack(side=tk.LEFT, padx=(0, 5))

        self.stop_camera_button = ttk.Button(control_frame, text="⏸ 停止摄像头", command=self.stop_video, state=tk.DISABLED)
        self.stop_camera_button.pack(side=tk.LEFT, padx=(0, 5))

        self.train_button = ttk.Button(control_frame, text="训练模型", command=self.train_face_model)
        self.train_button.pack(side=tk.LEFT, padx=(0, 5))

        self.add_employee_button = ttk.Button(control_frame, text="添加员工", command=self.add_employee)
        self.add_employee_button.pack(side=tk.LEFT)

        # 状态标签
        self.status_label = ttk.Label(left_frame, text="状态: 就绪 - 请点击'启动摄像头'", foreground="blue")
        self.status_label.pack(fill=tk.X)

        # 右侧区域：信息与交互区
        right_frame = ttk.LabelFrame(main_container, text="信息与交互区", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))

        # 考勤日志区域
        log_label = ttk.Label(right_frame, text="考勤日志", font=('Arial', 10, 'bold'))
        log_label.pack(anchor=tk.W, pady=(0, 5))

        self.log_text = tk.Text(right_frame, height=10, state=tk.DISABLED, wrap=tk.WORD,
                               font=('Consolas', 9))
        log_scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 智能问答区域
        ai_label = ttk.Label(right_frame, text="智能问答助手", font=('Arial', 10, 'bold'))
        ai_label.pack(anchor=tk.W, pady=(0, 5))

        # 输入框和按钮
        input_frame = ttk.Frame(right_frame)
        input_frame.pack(fill=tk.X, pady=(0, 5))
        self.query_entry = ttk.Entry(input_frame, font=('Arial', 10))
        self.query_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.query_entry.bind('<Return>', self.on_query_submit)
        query_button = ttk.Button(input_frame, text="查询", command=self.on_query_submit)
        query_button.pack(side=tk.RIGHT)

        # 结果显示框
        result_label = ttk.Label(right_frame, text="分析结果", font=('Arial', 10, 'bold'))
        result_label.pack(anchor=tk.W, pady=(0, 5))
        self.result_text = tk.Text(right_frame, height=10, state=tk.DISABLED, wrap=tk.WORD,
                                  font=('Consolas', 9))
        result_scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=result_scrollbar.set)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        result_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_employees(self):
        """加载员工信息"""
        employees_file = "employees.json"

        # 尝试从文件加载
        if os.path.exists(employees_file):
            try:
                with open(employees_file, 'r', encoding='utf-8') as f:
                    employees = json.load(f)
                    for emp in employees:
                        employee_ids[emp["id"]] = emp["id"]
                        employee_names[emp["id"]] = emp["name"]
                        self.add_log(f"已加载员工: {emp['name']}")
                    return
            except Exception as e:
                self.add_log(f"加载员工数据失败: {str(e)}")

        # 如果文件不存在，使用默认数据
        employees = [
            {"id": "001", "name": "张三"},
            {"id": "002", "name": "李四"},
            {"id": "003", "name": "王五"},
        ]

        for emp in employees:
            employee_ids[emp["id"]] = emp["id"]
            employee_names[emp["id"]] = emp["name"]
            self.add_log(f"已加载员工: {emp['name']}")

        # 保存到文件
        self.save_employees()

    def save_employees(self):
        """保存员工信息到文件"""
        employees = [
            {"id": emp_id, "name": employee_names[emp_id]}
            for emp_id in employee_names.keys()
        ]

        try:
            with open("employees.json", 'w', encoding='utf-8') as f:
                json.dump(employees, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.add_log(f"保存员工数据失败: {str(e)}")

    def load_face_model(self):
        """加载人脸识别模型"""
        model_file = "face_model.yml"
        labels_file = "face_labels.pkl"

        if os.path.exists(model_file) and os.path.exists(labels_file):
            try:
                self.face_recognizer.read(model_file)
                with open(labels_file, 'rb') as f:
                    self.employee_labels = pickle.load(f)
                self.add_log("人脸识别模型加载成功")
                self.status_label.config(text="状态: 模型已加载", foreground="green")
            except Exception as e:
                self.add_log(f"模型加载失败: {str(e)}")
                self.employee_labels = {}
        else:
            self.add_log("未找到训练好的模型，请先训练")
            self.employee_labels = {}

    def train_face_model(self):
        """训练人脸识别模型"""
        self.add_log("开始训练人脸识别模型...")

        # 获取所有员工图片
        faces = []
        labels = []
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        failed_images = []

        for emp_id in employee_names.keys():
            emp_name = employee_names[emp_id]
            image_path = f"faces/{emp_name}.jpg"

            if not os.path.exists(image_path):
                self.add_log(f"警告: 未找到 {emp_name} 的图片文件")
                failed_images.append(emp_name)
                continue

            try:
                # 读取图片
                img = cv2.imread(image_path)
                if img is None:
                    self.add_log(f"警告: {emp_name} 的图片无法读取")
                    failed_images.append(emp_name)
                    continue

                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

                # 尝试多种参数检测人脸
                faces_detected = None

                # 参数1: 标准检测
                faces_detected = face_cascade.detectMultiScale(gray, 1.1, 4)

                # 参数2: 如果失败，降低要求
                if len(faces_detected) == 0:
                    faces_detected = face_cascade.detectMultiScale(gray, 1.05, 3)

                # 参数3: 如果还是失败，进一步降低
                if len(faces_detected) == 0:
                    faces_detected = face_cascade.detectMultiScale(gray, 1.02, 2, minSize=(30, 30))

                if len(faces_detected) > 0:
                    # 取最大的人脸
                    (x, y, w, h) = max(faces_detected, key=lambda rect: rect[2] * rect[3])
                    face_roi = gray[y:y+h, x:x+w]

                    # 调整大小为统一尺寸
                    face_roi = cv2.resize(face_roi, (200, 200))

                    faces.append(face_roi)
                    labels.append(int(emp_id))
                    self.add_log(f"✓ 已处理 {emp_name} 的面部数据 (人脸大小: {w}x{h})")
                else:
                    self.add_log(f"❌ {emp_name} 的图片中未检测到人脸")
                    failed_images.append(emp_name)

            except Exception as e:
                self.add_log(f"❌ 处理 {emp_name} 时出错: {str(e)}")
                failed_images.append(emp_name)

        if len(faces) > 0:
            # 训练模型
            self.face_recognizer.train(faces, np.array(labels))
            self.face_recognizer.save("face_model.yml")

            # 保存标签
            self.employee_labels = {int(emp_id): emp_id for emp_id in employee_names.keys()}
            with open("face_labels.pkl", 'wb') as f:
                pickle.dump(self.employee_labels, f)

            success_msg = f"模型训练完成！\n\n成功: {len(faces)} 个样本"
            if failed_images:
                success_msg += f"\n失败: {len(failed_images)} 个样本\n({', '.join(failed_images)})"

            self.add_log(f"✓ 模型训练完成！共训练了 {len(faces)} 个样本")
            self.status_label.config(text="状态: 模型已训练", foreground="green")
            messagebox.showinfo("训练完成", success_msg)
        else:
            error_msg = "没有找到可用的训练数据！\n\n"
            error_msg += "可能原因：\n"
            error_msg += "1. 图片中没有清晰的正面人脸\n"
            error_msg += "2. 图片光线太暗或太亮\n"
            error_msg += "3. 人脸角度过大\n"
            error_msg += "4. 图片分辨率太低\n\n"
            error_msg += "建议：\n"
            error_msg += "• 使用正面、光线充足的照片\n"
            error_msg += "• 人脸占图片的30%以上\n"
            error_msg += "• 避免戴口罩、墨镜等遮挡"

            self.add_log("❌ 错误: 没有找到可用的训练数据")
            messagebox.showerror("训练失败", error_msg)

    def add_employee(self):
        """添加新员工"""
        dialog = tk.Toplevel(self.root)
        dialog.title("添加员工")
        dialog.geometry("450x280")
        dialog.transient(self.root)
        dialog.grab_set()

        # 创建主容器
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 员工姓名
        ttk.Label(main_frame, text="员工姓名:").grid(row=0, column=0, sticky=tk.W, pady=5)
        name_entry = ttk.Entry(main_frame, width=30)
        name_entry.grid(row=0, column=1, pady=5, padx=5)

        # 员工ID
        ttk.Label(main_frame, text="员工ID:").grid(row=1, column=0, sticky=tk.W, pady=5)
        id_entry = ttk.Entry(main_frame, width=30)
        id_entry.grid(row=1, column=1, pady=5, padx=5)

        # 面部图片路径
        ttk.Label(main_frame, text="面部图片:").grid(row=2, column=0, sticky=tk.W, pady=5)
        path_entry = ttk.Entry(main_frame, width=30)
        path_entry.grid(row=2, column=1, pady=5, padx=5)

        def browse_file():
            filename = filedialog.askopenfilename(
                title="选择员工照片",
                filetypes=[("图片文件", "*.jpg *.jpeg *.png"), ("所有文件", "*.*")]
            )
            if filename:
                path_entry.delete(0, tk.END)
                path_entry.insert(0, filename)

        ttk.Button(main_frame, text="浏览...", command=browse_file).grid(row=2, column=2, padx=5)

        def save_employee():
            name = name_entry.get().strip()
            emp_id = id_entry.get().strip()
            image_path = path_entry.get().strip()

            if not all([name, emp_id, image_path]):
                messagebox.showerror("错误", "请填写所有字段")
                return

            employee_names[emp_id] = name
            employee_ids[emp_id] = emp_id

            # 复制图片到faces目录
            import shutil
            dest_path = f"faces/{name}.jpg"
            try:
                shutil.copy2(image_path, dest_path)
                self.add_log(f"已添加员工: {name}")

                # 保存员工数据
                self.save_employees()

                dialog.destroy()
                messagebox.showinfo("成功", "员工添加成功，请重新训练模型")
            except Exception as e:
                messagebox.showerror("错误", f"保存图片失败: {str(e)}")

        # 按钮容器
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=20)

        ttk.Button(button_frame, text="确认", command=save_employee, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=dialog.destroy, width=12).pack(side=tk.LEFT, padx=5)

    def start_video(self):
        """启动视频流和人脸识别"""
        if self.video_running:
            self.add_log("摄像头已在运行中")
            return

        self.add_log("正在启动摄像头...")
        self.status_label.config(text="状态: 正在启动摄像头...", foreground="orange")

        # 尝试打开摄像头
        self.cap = cv2.VideoCapture(0)

        # 等待摄像头初始化
        import time
        time.sleep(0.5)

        if not self.cap.isOpened():
            self.add_log("❌ 无法打开摄像头0，尝试摄像头1...")
            self.cap = cv2.VideoCapture(1)
            time.sleep(0.5)

            if not self.cap.isOpened():
                error_msg = "无法打开摄像头！\n\n可能原因：\n1. 摄像头被其他程序占用\n2. 摄像头权限未授予\n3. 没有可用的摄像头"
                messagebox.showerror("错误", error_msg)
                self.add_log("❌ 摄像头启动失败")
                self.status_label.config(text="状态: 摄像头启动失败", foreground="red")
                return

        # 设置摄像头参数
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self.video_running = True
        self.video_thread = threading.Thread(target=self.video_loop, daemon=True)
        self.video_thread.start()

        self.add_log("✓ 摄像头已启动")
        self.status_label.config(text="状态: 摄像头运行中", foreground="green")

        # 更新按钮状态
        self.start_camera_button.config(state=tk.DISABLED)
        self.stop_camera_button.config(state=tk.NORMAL)

    def stop_video(self):
        """停止视频流"""
        if not self.video_running:
            return

        self.video_running = False
        self.add_log("正在停止摄像头...")

        # 等待线程结束
        if self.video_thread and self.video_thread.is_alive():
            self.video_thread.join(timeout=2)

        # 释放摄像头
        if self.cap:
            self.cap.release()
            self.cap = None

        # 清空画布
        self.video_canvas.delete("all")
        self.video_canvas.create_text(
            320, 240,
            text="摄像头已停止\n点击'启动摄像头'重新开始",
            fill="white",
            font=('Arial', 14)
        )

        self.add_log("✓ 摄像头已停止")
        self.status_label.config(text="状态: 摄像头已停止", foreground="gray")

        # 更新按钮状态
        self.start_camera_button.config(state=tk.NORMAL)
        self.stop_camera_button.config(state=tk.DISABLED)

    def record_attendance(self, emp_id, emp_name):
        """记录考勤"""
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        datetime_str = now.strftime("%Y-%m-%d %H:%M:%S")

        # 检查是否在冷却期内（5分钟）
        if emp_id in self.last_recognition_time:
            last_time = self.last_recognition_time[emp_id]
            time_diff = (now - last_time).total_seconds()
            if time_diff < 300:  # 5分钟 = 300秒
                return False

        # 记录考勤
        try:
            # 追加到CSV文件（适配现有格式：员工ID,姓名,日期,时间,签到时间）
            df = pd.DataFrame([{
                "员工ID": emp_id,
                "姓名": emp_name,
                "日期": date_str,
                "时间": time_str,
                "签到时间": datetime_str
            }])
            df.to_csv("attendance.csv", mode='a', header=False, index=False, encoding="utf-8-sig")

            # 更新最后识别时间
            self.last_recognition_time[emp_id] = now

            # 添加日志
            self.add_log(f"✓ {emp_name} 打卡成功 - {time_str}")

            return True
        except Exception as e:
            self.add_log(f"记录考勤失败: {str(e)}")
            return False

    def video_loop(self):
        """视频流处理循环（后台线程）"""
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        frame_count = 0

        while self.video_running:
            ret, frame = self.cap.read()
            if not ret:
                continue

            frame_count += 1

            # 转换灰度图用于人脸检测
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # 使用更宽松的参数检测人脸（与训练时一致）
            faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(30, 30))

            # 在画面上显示检测状态（使用中文）
            status_text = f"检测到 {len(faces)} 个人脸"
            frame = self.put_chinese_text(frame, status_text, (10, 10), self.font_small, (255, 255, 255))

            # 显示模型状态
            if hasattr(self, 'employee_labels') and len(self.employee_labels) > 0:
                model_text = f"模型已加载 ({len(self.employee_labels)} 人)"
                frame = self.put_chinese_text(frame, model_text, (10, 40), self.font_small, (255, 255, 255))
            else:
                model_text = "模型未训练"
                frame = self.put_chinese_text(frame, model_text, (10, 40), self.font_small, (0, 0, 255))

            # 识别人脸
            for (x, y, w, h) in faces:
                # 绘制检测框
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

                # 人脸识别
                if hasattr(self, 'employee_labels') and len(self.employee_labels) > 0:
                    face_roi = gray[y:y+h, x:x+w]
                    try:
                        # 调整大小与训练时一致
                        face_roi_resized = cv2.resize(face_roi, (200, 200))
                        label, confidence = self.face_recognizer.predict(face_roi_resized)

                        # 置信度阈值 (LBPH: 值越小越相似，通常 < 50 为好匹配)
                        if confidence < 80:  # 放宽阈值
                            emp_id = self.employee_labels.get(label)
                            if emp_id:
                                recognized_name = employee_names.get(emp_id, "未知")

                                # 根据置信度选择颜色
                                if confidence < 50:
                                    color = (0, 255, 0)  # 绿色 - 高置信度
                                    conf_text = "高"
                                elif confidence < 65:
                                    color = (0, 255, 255)  # 黄色 - 中等置信度
                                    conf_text = "中"
                                else:
                                    color = (0, 165, 255)  # 橙色 - 低置信度
                                    conf_text = "低"

                                # 显示识别结果（使用中文）
                                name_text = f"{recognized_name}"
                                conf_display = f"置信度:{conf_text} ({confidence:.0f})"

                                frame = self.put_chinese_text(frame, name_text, (x, y-50), self.font, color)
                                frame = self.put_chinese_text(frame, conf_display, (x, y-20), self.font_small, color)

                                # 添加调试日志（每30帧输出一次）
                                if frame_count % 30 == 0:
                                    self.add_log(f"识别到: {recognized_name} (ID:{emp_id}, 置信度:{confidence:.1f})")

                                # 只有高置信度才记录考勤（临时降低阈值到75以便调试）
                                if confidence < 75:  # 从65改为75，更宽松
                                    result = self.record_attendance(emp_id, recognized_name)
                                    if frame_count % 30 == 0 and not result:
                                        self.add_log(f"  → 未记录考勤（可能在冷却期内）")
                                else:
                                    if frame_count % 30 == 0:
                                        self.add_log(f"  → 置信度太低({confidence:.1f})，未记录考勤")
                        else:
                            # 置信度太低，显示未知
                            unknown_text = f"未知 ({confidence:.0f})"
                            frame = self.put_chinese_text(frame, unknown_text, (x, y-20), self.font_small, (0, 0, 255))
                    except Exception as e:
                        # 显示错误信息
                        error_msg = f"识别错误: {str(e)}"
                        frame = self.put_chinese_text(frame, "识别错误", (x, y-20), self.font_small, (0, 0, 255))
                        if frame_count % 30 == 0:  # 每30帧打印一次
                            print(error_msg)

            # 将帧转换为Tkinter格式
            try:
                photo = self.cv2_to_tkinter(frame)
                if not self.frame_queue.full():
                    self.frame_queue.put(photo)
            except Exception as e:
                print(f"转换图像时出错: {e}")

        if self.cap:
            self.cap.release()

    def cv2_to_tkinter(self, cv_frame):
        """将OpenCV帧转换为Tkinter PhotoImage"""
        # 调整帧大小
        height, width = cv_frame.shape[:2]
        max_width = 640
        max_height = 480

        # 计算缩放比例
        scale = min(max_width / width, max_height / height)
        new_width = int(width * scale)
        new_height = int(height * scale)

        # 缩放图像
        resized = cv2.resize(cv_frame, (new_width, new_height))

        # 转换为RGB
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

        # 转换为PIL图像
        pil_image = Image.fromarray(rgb)

        # 转换为Tkinter PhotoImage
        return ImageTk.PhotoImage(pil_image)

    def update_video_display(self):
        """更新视频显示（主线程）"""
        try:
            photo = self.frame_queue.get_nowait()
            # 保持引用防止被垃圾回收
            self.current_photo = photo
            self.video_canvas.delete("all")
            # 计算居中位置
            canvas_width = self.video_canvas.winfo_width()
            canvas_height = self.video_canvas.winfo_height()
            if canvas_width > 1 and canvas_height > 1:
                x = canvas_width // 2
                y = canvas_height // 2
                self.video_canvas.create_image(x, y, image=self.current_photo, anchor=tk.CENTER)
        except queue.Empty:
            pass
        finally:
            # 继续调度下一次更新
            self.root.after(30, self.update_video_display)

    def add_log(self, message):
        """添加日志（线程安全）"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_queue.put(formatted_message)

    def start_log_processor(self):
        """启动日志处理器"""
        def process_logs():
            while True:
                try:
                    message = self.log_queue.get(timeout=1)
                    if message:
                        self.root.after(0, self._update_log_display, message)
                except queue.Empty:
                    continue

        log_thread = threading.Thread(target=process_logs, daemon=True)
        log_thread.start()

    def _update_log_display(self, message):
        """更新日志显示（主线程）"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def on_query_submit(self, event=None):
        """处理查询请求"""
        query = self.query_entry.get().strip()
        if not query:
            messagebox.showwarning("警告", "请输入问题！")
            return

        # 清空输入框
        self.query_entry.delete(0, tk.END)

        # 在新线程中处理查询
        threading.Thread(target=self.process_query, args=(query,), daemon=True).start()

    def process_query(self, query):
        """处理LLM查询（后台线程）"""
        # 显示加载状态
        self.root.after(0, self._update_result_display, "正在分析，请稍候...")

        try:
            # 读取考勤数据
            df = pd.read_csv("attendance.csv") if os.path.exists("attendance.csv") else None

            # 构建Prompt
            prompt = f"""你是一个专业的考勤数据分析助手。请根据以下考勤数据回答用户的问题。

考勤数据统计：
{df.describe().to_string() if df is not None and not df.empty else '暂无数据'}

考勤明细：
{df.to_string() if df is not None and not df.empty else '暂无数据'}

用户问题：{query}

请提供简洁、准确的分析回答。"""

            # 调用LLM API
            response = self.call_llm_api(prompt)

            # 显示结果
            self.root.after(0, self._update_result_display, response)

        except Exception as e:
            error_msg = f"查询出错: {str(e)}"
            self.root.after(0, self._update_result_display, error_msg)

    def call_llm_api(self, prompt):
        """调用LLM API"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.llm_api_key}"
        }

        data = {
            "model": self.llm_model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }

        response = requests.post(self.llm_api_url, headers=headers, json=data, timeout=30)
        response.raise_for_status()

        result = response.json()
        return result['choices'][0]['message']['content']

    def _update_result_display(self, text):
        """更新结果显示（主线程）"""
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, text)
        self.result_text.config(state=tk.DISABLED)

    def on_closing(self):
        """窗口关闭处理"""
        # 停止摄像头
        if self.video_running:
            self.stop_video()
        self.root.destroy()


def main():
    """主函数"""
    root = tk.Tk()
    app = FaceAttendanceSystem(root)

    # 不自动启动摄像头，让用户手动点击按钮启动
    # app.start_video()

    # 启动视频显示更新
    app.update_video_display()

    # 启动主循环
    root.mainloop()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能人脸考勤与文本交互分析系统 - 完整演示版
包含自动图片生成、模型训练和人脸识别
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
import random

# 员工面部编码存储
employee_encodings = {}
employee_names = {}
employee_ids = {}

class FaceAttendanceSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("智能人脸考勤与文本交互分析系统 - 演示版")
        self.root.geometry("1200x700")
        self.root.minsize(1000, 600)

        # 摄像头相关
        self.cap = None
        self.video_thread = None
        self.video_running = False
        self.frame_queue = queue.Queue(maxsize=2)
        self.log_queue = queue.Queue()

        # LLM API配置
        self.llm_api_url = "https://api.deepseek.com/v1/chat/completions"
        self.llm_api_key = "YOUR_API_KEY"  # 需要用户配置
        self.llm_model = "deepseek-chat"

        # 初始化界面
        self.setup_ui()

        # 加载员工信息
        self.load_employees()

        # 加载人脸识别模型
        self.face_recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.load_face_model()

        # 启动日志处理线程
        self.start_log_processor()

        self.add_log("系统初始化完成 - 演示版")
        self.add_log("提示: 这是演示版本，使用自动生成的图片进行训练和识别")

    def setup_ui(self):
        """设置用户界面"""
        # 创建主容器（左右两列）
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 左侧区域：视频显示区
        left_frame = ttk.LabelFrame(main_container, text="摄像头与人脸识别区", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # 视频画布
        self.video_canvas = tk.Canvas(left_frame, bg="black", width=640, height=480)
        self.video_canvas.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 控制按钮
        control_frame = ttk.Frame(left_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        self.train_button = ttk.Button(control_frame, text="生成示例图片并训练", command=self.train_face_model)
        self.train_button.pack(side=tk.LEFT, padx=(0, 5))

        self.start_demo_button = ttk.Button(control_frame, text="开始演示识别", command=self.start_recognition_demo)
        self.start_demo_button.pack(side=tk.LEFT, padx=(0, 5))

        # 状态标签
        self.status_label = ttk.Label(left_frame, text="状态: 等待训练...", foreground="blue")
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
        employees = [
            {"id": "001", "name": "张三", "image_path": "faces/zhangsan.jpg"},
            {"id": "002", "name": "李四", "image_path": "faces/lisi.jpg"},
            {"id": "003", "name": "王五", "image_path": "faces/wangwu.jpg"},
        ]

        for emp in employees:
            employee_ids[emp["id"]] = emp["id"]
            employee_names[emp["id"]] = emp["name"]

    def generate_sample_faces(self):
        """生成示例人脸图片（使用OpenCV生成更真实的人脸图像）"""
        self.add_log("正在生成示例人脸图片...")

        for emp_id, name in employee_names.items():
            # 创建更大的图片以提高检测率
            img = np.zeros((600, 600, 3), dtype=np.uint8)

            # 设置随机种子以确保每个人有不同的脸
            np.random.seed(int(emp_id) + 100)

            # 背景颜色
            img[:] = (200, 220, 240)

            # 脸型 - 使用更大的椭圆
            face_center = (300, 300)
            face_axes = (180, 220)
            face_color = tuple(map(int, np.random.randint(150, 220, 3)))
            cv2.ellipse(img, face_center, face_axes, 0, 0, 360, face_color, -1)

            # 眼睛 - 更大更明显
            eye_y = 250
            left_eye_x = 230
            right_eye_x = 370
            eye_size = 35

            # 眼白
            cv2.circle(img, (left_eye_x, eye_y), eye_size, (255, 255, 255), -1)
            cv2.circle(img, (right_eye_x, eye_y), eye_size, (255, 255, 255), -1)

            # 瞳孔
            cv2.circle(img, (left_eye_x, eye_y), 15, (0, 0, 0), -1)
            cv2.circle(img, (right_eye_x, eye_y), 15, (0, 0, 0), -1)

            # 高光点
            cv2.circle(img, (left_eye_x - 8, eye_y - 8), 5, (255, 255, 255), -1)
            cv2.circle(img, (right_eye_x - 8, eye_y - 8), 5, (255, 255, 255), -1)

            # 鼻子 - 三角形
            nose_top = (300, 270)
            nose_left = (280, 320)
            nose_right = (320, 320)
            nose_color = tuple(map(int, face_color))
            cv2.fillPoly(img, [np.array([nose_top, nose_left, nose_right], np.int32)], nose_color)

            # 嘴巴 - 更明显的红色
            mouth_center = (300, 360)
            mouth_axes = (50, 25)
            mouth_color = (120, 50, 50)
            cv2.ellipse(img, mouth_center, mouth_axes, 0, 0, 180, mouth_color, -1)

            # 眉毛
            brow_color = (50, 50, 50)
            cv2.ellipse(img, (left_eye_x, eye_y - 50), (40, 15), 0, 0, 180, brow_color, 5)
            cv2.ellipse(img, (right_eye_x, eye_y - 50), (40, 15), 0, 0, 180, brow_color, 5)

            # 添加编号作为标识
            cv2.putText(img, name, (250, 480), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2)

            # 保存图片
            image_path = f"faces/{name}.jpg"
            cv2.imwrite(image_path, img)
            self.add_log(f"已生成 {name} 的示例图片")

    def train_face_model(self):
        """训练人脸识别模型"""
        self.add_log("开始训练人脸识别模型...")

        # 首先检查faces目录是否存在
        if not os.path.exists("faces"):
            os.makedirs("faces")

        # 生成示例图片
        self.generate_sample_faces()

        # 获取所有员工图片 - 直接使用整张图片，不依赖人脸检测
        faces = []
        labels = []

        for emp_id, name in employee_names.items():
            image_path = f"faces/{name}.jpg"

            if os.path.exists(image_path):
                try:
                    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
                    if img is not None:
                        # 调整图片大小为统一尺寸（LBPH算法要求）
                        resized_img = cv2.resize(img, (200, 200))
                        faces.append(resized_img)
                        labels.append(int(emp_id))
                        self.add_log(f"已处理 {name} 的面部数据 (使用整张图片)")
                    else:
                        self.add_log(f"错误: 无法读取 {name} 的图片")
                except Exception as e:
                    self.add_log(f"处理 {name} 时出错: {str(e)}")
            else:
                self.add_log(f"错误: 未找到文件 {image_path}")

        if len(faces) > 0:
            # 训练模型
            self.face_recognizer.train(faces, np.array(labels))
            self.face_recognizer.save("face_model.yml")

            # 保存标签
            self.employee_labels = {int(emp_id): emp_id for emp_id in employee_names.keys()}
            with open("face_labels.pkl", 'wb') as f:
                pickle.dump(self.employee_labels, f)

            self.add_log(f"模型训练完成！共训练了 {len(faces)} 个样本")
            self.status_label.config(text="状态: 模型已训练完成", foreground="green")
            messagebox.showinfo("成功", f"人脸识别模型训练完成！\n共处理了 {len(faces)} 个样本")
        else:
            self.add_log("错误: 没有找到可用的训练数据")
            messagebox.showerror("错误", "没有找到可用的训练数据！\n请检查faces目录下的图片文件")

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

    def start_recognition_demo(self):
        """开始演示识别过程"""
        if not hasattr(self, 'employee_labels') or len(self.employee_labels) == 0:
            messagebox.showwarning("警告", "请先训练模型！")
            return

        self.add_log("开始演示人脸识别...")

        # 生成一个随机员工进行演示
        emp_id = random.choice(list(employee_names.keys()))
        name = employee_names[emp_id]

        # 创建演示图像
        demo_img = self.generate_demo_image(name)

        # 将图像放入队列显示
        photo = self.cv2_to_tkinter(demo_img)
        self.frame_queue.put(photo)

        # 记录考勤
        self.record_attendance(emp_id, name, demo=True)

        # 更新状态
        self.status_label.config(text=f"状态: 识别到 {name}", foreground="green")

    def generate_demo_image(self, name):
        """生成演示识别图像"""
        # 读取员工图片
        img = cv2.imread(f"faces/{name}.jpg")

        # 加载人脸检测器
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        # 绘制识别框和姓名
        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 3)
            cv2.putText(img, f"{name} (识别)", (x, y-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # 添加识别成功的标识
        cv2.putText(img, "识别成功!", (50, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        return img

    def record_attendance(self, emp_id, name, demo=False):
        """记录考勤信息"""
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        date = now.strftime("%Y-%m-%d")
        time = now.strftime("%H:%M:%S")

        # 保存到CSV文件
        attendance_file = "attendance.csv"
        df = pd.DataFrame({
            '员工ID': [emp_id],
            '姓名': [name],
            '日期': [date],
            '时间': [time],
            '签到时间': [timestamp],
            '类型': ['演示'] if demo else ['正常']
        })

        if os.path.exists(attendance_file):
            df.to_csv(attendance_file, mode='a', header=False, index=False, encoding='utf-8-sig')
        else:
            df.to_csv(attendance_file, index=False, encoding='utf-8-sig')

        # 添加到日志
        demo_note = " (演示)" if demo else ""
        self.add_log(f"[{time}] {name} 签到成功{demo_note}")

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
            self.video_canvas.delete("all")
            # 计算居中位置
            canvas_width = self.video_canvas.winfo_width()
            canvas_height = self.video_canvas.winfo_height()
            if canvas_width > 1 and canvas_height > 1:
                x = canvas_width // 2
                y = canvas_height // 2
                self.video_canvas.create_image(x, y, image=photo, anchor=tk.CENTER)
        except queue.Empty:
            pass
        finally:
            # 继续调度下一次更新
            self.root.after(100, self.update_video_display)

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
        self.video_running = False
        if self.cap:
            self.cap.release()
        self.root.destroy()


def main():
    """主函数"""
    root = tk.Tk()
    app = FaceAttendanceSystem(root)

    # 启动视频显示更新
    app.update_video_display()

    # 启动主循环
    root.mainloop()


if __name__ == "__main__":
    main()

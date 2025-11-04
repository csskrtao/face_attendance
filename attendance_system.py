
# -*- coding: utf-8 -*-
"""
智能人脸考勤与文本交互分析系统 (GUI版)
基于Tkinter + OpenCV + face_recognition + LLM API
"""

import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import face_recognition
import pandas as pd
import numpy as np
from PIL import Image, ImageTk
import threading
import queue
import datetime
import os
import requests
import json

# 员工面部编码存储字典（生产环境中应持久化存储）
employee_encodings = {}
employee_names = {}


class FaceAttendanceSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("智能人脸考勤与文本交互分析系统")
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

        # 启动日志处理线程
        self.start_log_processor()

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

        # 状态标签
        self.status_label = ttk.Label(left_frame, text="状态: 初始化中...", foreground="blue")
        self.status_label.pack(fill=tk.X)

        # 右侧区域：信息与交互区
        right_frame = ttk.LabelFrame(main_container, text="信息与交互区", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))

        # 考勤日志区域
        log_label = ttk.Label(right_frame, text="考勤日志", font=('Arial', 10, 'bold'))
        log_label.pack(anchor=tk.W, pady=(0, 5))

        self.log_text = tk.Text(right_frame, height=12, state=tk.DISABLED, wrap=tk.WORD,
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
        """加载员工信息和面部编码"""
        # 示例员工数据（生产环境中应从数据库或配置文件读取）
        employees = [
            {"id": "001", "name": "张三", "image_path": "faces/zhangsan.jpg"},
            {"id": "002", "name": "李四", "image_path": "faces/lisi.jpg"},
            {"id": "003", "name": "王五", "image_path": "faces/wangwu.jpg"},
        ]

        for emp in employees:
            employee_names[emp["id"]] = emp["name"]
            # 尝试加载面部编码
            if os.path.exists(emp["image_path"]):
                try:
                    image = face_recognition.load_image_file(emp["image_path"])
                    encoding = face_recognition.face_encodings(image)[0]
                    employee_encodings[emp["id"]] = encoding
                    self.add_log(f"已加载员工: {emp['name']}")
                except Exception as e:
                    self.add_log(f"加载员工 {emp['name']} 面部数据失败: {str(e)}")
            else:
                self.add_log(f"警告: 未找到员工 {emp['name']} 的面部图片: {emp['image_path']}")

    def start_video(self):
        """启动视频流和人脸识别"""
        if self.video_running:
            return

        self.video_running = True
        self.cap = cv2.VideoCapture(0)

        if not self.cap.isOpened():
            messagebox.showerror("错误", "无法打开摄像头！")
            self.video_running = False
            return

        self.video_thread = threading.Thread(target=self.video_loop, daemon=True)
        self.video_thread.start()
        self.add_log("摄像头已启动")

    def video_loop(self):
        """视频流处理循环（后台线程）"""
        while self.video_running:
            ret, frame = self.cap.read()
            if not ret:
                continue

            # 人脸识别
            recognized_name = self.recognize_face(frame)

            # 绘制识别框
            if recognized_name:
                self.draw_face_box(frame, recognized_name)

            # 将帧转换为Tkinter格式
            try:
                photo = self.cv2_to_tkinter(frame)
                if not self.frame_queue.full():
                    self.frame_queue.put(photo)
            except Exception as e:
                print(f"转换图像时出错: {e}")

        if self.cap:
            self.cap.release()

    def recognize_face(self, frame):
        """识别人脸"""
        # 转换颜色空间
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 检测人脸位置
        face_locations = face_recognition.face_locations(rgb_frame)
        if not face_locations:
            return None

        # 获取面部编码
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        # 与已知员工面部编码对比
        for encoding in face_encodings:
            for emp_id, known_encoding in employee_encodings.items():
                match = face_recognition.compare_faces([known_encoding], encoding, tolerance=0.5)
                if match[0]:
                    name = employee_names[emp_id]
                    # 记录考勤
                    self.record_attendance(emp_id, name)
                    return name

        return None

    def draw_face_box(self, frame, name):
        """在人脸上绘制识别框和姓名"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)

        for (top, right, bottom, left) in face_locations:
            # 绘制边框
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            # 绘制姓名标签
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
            cv2.putText(frame, name, (left + 6, bottom - 6),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

    def record_attendance(self, emp_id, name):
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
            '签到时间': [timestamp]
        })

        if os.path.exists(attendance_file):
            df.to_csv(attendance_file, mode='a', header=False, index=False, encoding='utf-8-sig')
        else:
            df.to_csv(attendance_file, index=False, encoding='utf-8-sig')

        # 添加到日志
        self.add_log(f"[{time}] {name} 签到成功")

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
        self.video_running = False
        if self.cap:
            self.cap.release()
        self.root.destroy()


def main():
    """主函数"""
    root = tk.Tk()
    app = FaceAttendanceSystem(root)

    # 启动视频流
    app.start_video()

    # 启动视频显示更新
    app.update_video_display()

    # 启动主循环
    root.mainloop()


if __name__ == "__main__":
    main()

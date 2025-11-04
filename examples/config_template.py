#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件模板
复制此文件为config.py并修改相关配置
"""

# LLM API配置
LLM_API_URL = "https://api.deepseek.com/v1/chat/completions"
LLM_API_KEY = "YOUR_API_KEY_HERE"  # 请替换为您的实际API密钥
LLM_MODEL = "deepseek-chat"

# 摄像头配置
CAMERA_INDEX = 0  # 摄像头索引，通常为0（第一个摄像头）
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# 人脸识别配置
FACE_TOLERANCE = 0.5  # 人脸匹配阈值，范围0-1，越小越严格
MODEL_SIZE = "small"  # 人脸识别模型大小：small, large

# 考勤配置
ATTENDANCE_FILE = "attendance.csv"

# 员工数据配置
EMPLOYEES = [
    {"id": "001", "name": "张三", "image_path": "faces/zhangsan.jpg"},
    {"id": "002", "name": "李四", "image_path": "faces/lisi.jpg"},
    {"id": "003", "name": "王五", "image_path": "faces/wangwu.jpg"},
    # 添加更多员工...
]

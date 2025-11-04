# -*- coding: utf-8 -*-
"""
测试人脸识别效果
"""

import cv2
import pickle
import os
import json

def test_recognition():
    """测试训练好的模型识别效果"""
    print("=" * 60)
    print("人脸识别测试工具")
    print("=" * 60)
    
    # 检查模型文件
    if not os.path.exists("face_model.yml"):
        print("\n✗ 模型文件不存在，请先训练模型")
        return
    
    if not os.path.exists("face_labels.pkl"):
        print("\n✗ 标签文件不存在，请先训练模型")
        return
    
    # 加载模型
    print("\n加载模型...")
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read("face_model.yml")
    
    with open("face_labels.pkl", 'rb') as f:
        employee_labels = pickle.load(f)
    
    # 加载员工名称
    employee_names = {}
    if os.path.exists("employees.json"):
        with open("employees.json", 'r', encoding='utf-8') as f:
            employees = json.load(f)
            for emp in employees:
                employee_names[emp["id"]] = emp["name"]
    
    print(f"✓ 模型已加载，包含 {len(employee_labels)} 个标签")
    print(f"  员工: {list(employee_names.values())}")
    
    # 加载人脸检测器
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # 测试faces目录下的所有图片
    print("\n测试识别效果...")
    print("-" * 60)
    
    if not os.path.exists("faces"):
        print("✗ faces目录不存在")
        return
    
    image_files = [f for f in os.listdir("faces") 
                   if f.lower().endswith(('.jpg', '.jpeg', '.png')) 
                   and '_detected' not in f]
    
    if not image_files:
        print("✗ faces目录下没有图片")
        return
    
    for img_file in image_files:
        img_path = os.path.join("faces", img_file)
        print(f"\n测试: {img_file}")
        
        # 读取图片
        img = cv2.imread(img_path)
        if img is None:
            print("  ✗ 无法读取图片")
            continue
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 检测人脸
        faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(30, 30))
        
        if len(faces) == 0:
            print("  ✗ 未检测到人脸")
            continue
        
        print(f"  检测到 {len(faces)} 个人脸")
        
        # 识别每个人脸
        for i, (x, y, w, h) in enumerate(faces):
            face_roi = gray[y:y+h, x:x+w]
            face_roi_resized = cv2.resize(face_roi, (200, 200))
            
            try:
                label, confidence = recognizer.predict(face_roi_resized)
                emp_id = employee_labels.get(label)
                emp_name = employee_names.get(emp_id, "未知") if emp_id else "未知"
                
                # 评估置信度
                if confidence < 50:
                    quality = "✓ 优秀"
                elif confidence < 65:
                    quality = "○ 良好"
                elif confidence < 80:
                    quality = "△ 一般"
                else:
                    quality = "✗ 较差"
                
                print(f"  人脸 {i+1}: {emp_name} | 置信度: {confidence:.1f} | {quality}")
                
            except Exception as e:
                print(f"  人脸 {i+1}: 识别失败 - {str(e)}")
    
    print("\n" + "=" * 60)
    print("置信度说明:")
    print("  < 50  : 优秀匹配，可以放心使用")
    print("  50-65 : 良好匹配，基本可用")
    print("  65-80 : 一般匹配，建议重新训练")
    print("  > 80  : 较差匹配，需要更换照片")
    print("=" * 60)
    
    print("\n提示:")
    print("1. 如果识别效果不好，请检查照片质量")
    print("2. 使用 test_face_detection.py 检查照片")
    print("3. 确保照片光线充足、正面、清晰")
    print("4. 重新训练模型")

if __name__ == "__main__":
    test_recognition()


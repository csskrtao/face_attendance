# -*- coding: utf-8 -*-
"""
测试修复后的代码逻辑
"""

import os
import json
import pandas as pd

def test_directory_creation():
    """测试目录创建"""
    print("测试1: 检查目录和文件创建...")

    # 检查faces目录
    if os.path.exists("faces"):
        print("✓ faces目录存在")
    else:
        print("✗ faces目录不存在")

    # 检查attendance.csv
    if os.path.exists("attendance.csv"):
        print("✓ attendance.csv文件存在")
        df = pd.read_csv("attendance.csv", encoding="utf-8-sig")
        expected_columns = ["员工ID", "姓名", "日期", "时间", "签到时间"]
        actual_columns = list(df.columns)
        print(f"  列名: {actual_columns}")

        # 验证列名是否匹配
        if actual_columns == expected_columns:
            print("  ✓ CSV格式正确")
        else:
            print(f"  ✗ CSV格式不匹配，期望: {expected_columns}")
    else:
        print("✗ attendance.csv文件不存在")

def test_employee_persistence():
    """测试员工数据持久化"""
    print("\n测试2: 检查员工数据持久化...")
    
    if os.path.exists("employees.json"):
        print("✓ employees.json文件存在")
        with open("employees.json", 'r', encoding='utf-8') as f:
            employees = json.load(f)
            print(f"  员工数量: {len(employees)}")
            for emp in employees:
                print(f"  - {emp['name']} (ID: {emp['id']})")
    else:
        print("✗ employees.json文件不存在（首次运行后会创建）")

def test_attendance_record():
    """测试考勤记录"""
    print("\n测试3: 检查考勤记录...")
    
    if os.path.exists("attendance.csv"):
        df = pd.read_csv("attendance.csv", encoding="utf-8-sig")
        if len(df) > 0:
            print(f"✓ 已有 {len(df)} 条考勤记录")
            print("\n最近5条记录:")
            print(df.tail(5).to_string(index=False))
        else:
            print("○ 暂无考勤记录（等待人脸识别）")
    else:
        print("✗ attendance.csv文件不存在")

def test_model_files():
    """测试模型文件"""
    print("\n测试4: 检查模型文件...")
    
    if os.path.exists("face_model.yml"):
        print("✓ face_model.yml存在（模型已训练）")
    else:
        print("○ face_model.yml不存在（需要训练模型）")
    
    if os.path.exists("face_labels.pkl"):
        print("✓ face_labels.pkl存在")
    else:
        print("○ face_labels.pkl不存在（需要训练模型）")

def test_code_structure():
    """测试代码结构"""
    print("\n测试5: 检查代码结构...")
    
    with open("attendance_system_opencv.py", 'r', encoding='utf-8') as f:
        content = f.read()
        
        checks = [
            ("initialize_directories", "初始化目录方法"),
            ("record_attendance", "考勤记录方法"),
            ("save_employees", "员工数据保存方法"),
            ("self.current_photo", "PhotoImage引用保持"),
            ("last_recognition_time", "防重复打卡机制"),
            ("opencv-contrib-python", "依赖说明"),
        ]
        
        for keyword, description in checks:
            if keyword in content:
                print(f"✓ {description}存在")
            else:
                print(f"✗ {description}缺失")

if __name__ == "__main__":
    print("=" * 60)
    print("attendance_system_opencv.py 修复验证测试")
    print("=" * 60)
    
    test_directory_creation()
    test_employee_persistence()
    test_attendance_record()
    test_model_files()
    test_code_structure()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    print("\n提示:")
    print("1. 如果是首次运行，请先运行主程序创建初始文件")
    print("2. 运行主程序: python attendance_system_opencv.py")
    print("3. 点击'训练模型'按钮训练人脸识别模型")
    print("4. 摄像头会自动识别并记录考勤")


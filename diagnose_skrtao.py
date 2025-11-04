# -*- coding: utf-8 -*-
"""
诊断 skrtao 考勤记录问题
"""

import json
import pandas as pd
import os
import pickle

print("=" * 60)
print("skrtao 考勤问题诊断工具")
print("=" * 60)

# 1. 检查员工数据
print("\n1. 检查员工数据...")
if os.path.exists("employees.json"):
    with open("employees.json", 'r', encoding='utf-8') as f:
        employees = json.load(f)
    
    skrtao_found = False
    for emp in employees:
        if emp['name'] == 'skrtao':
            print(f"  ✓ 找到员工: {emp['name']}, ID: {emp['id']}")
            skrtao_id = emp['id']
            skrtao_found = True
            break
    
    if not skrtao_found:
        print("  ✗ 未找到 skrtao 员工")
else:
    print("  ✗ employees.json 不存在")

# 2. 检查照片文件
print("\n2. 检查照片文件...")
photo_path = "faces/skrtao.jpg"
if os.path.exists(photo_path):
    print(f"  ✓ 照片存在: {photo_path}")
else:
    print(f"  ✗ 照片不存在: {photo_path}")

# 3. 检查模型标签
print("\n3. 检查模型标签...")
if os.path.exists("face_labels.pkl"):
    with open("face_labels.pkl", 'rb') as f:
        labels = pickle.load(f)
    
    print(f"  模型包含 {len(labels)} 个标签")
    
    # 查找 skrtao 的标签
    skrtao_label = None
    for label, emp_id in labels.items():
        if emp_id == skrtao_id:
            skrtao_label = label
            print(f"  ✓ skrtao 在模型中: label={label}, emp_id={emp_id}")
            break
    
    if skrtao_label is None:
        print(f"  ✗ skrtao (ID:{skrtao_id}) 不在模型中")
        print("  → 需要重新训练模型！")
else:
    print("  ✗ face_labels.pkl 不存在")

# 4. 检查考勤记录
print("\n4. 检查考勤记录...")
if os.path.exists("attendance.csv"):
    df = pd.read_csv("attendance.csv", encoding='utf-8-sig')
    
    skrtao_records = df[df['姓名'] == 'skrtao']
    
    if len(skrtao_records) > 0:
        print(f"  ✓ 找到 {len(skrtao_records)} 条 skrtao 的考勤记录")
        print("\n  最近的记录:")
        print(skrtao_records.tail(5).to_string(index=False))
    else:
        print("  ✗ 没有 skrtao 的考勤记录")
        
        # 检查是否有该ID的记录
        id_records = df[df['员工ID'] == skrtao_id]
        if len(id_records) > 0:
            print(f"  ! 但找到了 ID={skrtao_id} 的记录（姓名可能不匹配）")
            print(id_records.tail(5).to_string(index=False))
else:
    print("  ✗ attendance.csv 不存在")

# 5. 总结和建议
print("\n" + "=" * 60)
print("诊断总结")
print("=" * 60)

if skrtao_found and os.path.exists(photo_path) and skrtao_label is not None:
    print("\n✓ 员工数据完整，模型已训练")
    print("\n可能的问题：")
    print("1. 实时识别时置信度太低（> 65）")
    print("2. 在5分钟冷却期内")
    print("3. 摄像头画面质量与训练照片差异大")
    
    print("\n建议操作：")
    print("1. 重新运行程序，启动摄像头")
    print("2. 对着摄像头，观察画面上显示的置信度")
    print("3. 查看考勤日志区域的提示信息")
    print("4. 如果置信度 > 65，需要：")
    print("   - 改善光线条件")
    print("   - 调整摄像头角度")
    print("   - 或降低置信度阈值")
else:
    print("\n✗ 数据不完整")
    if not skrtao_found:
        print("  → 需要添加 skrtao 员工")
    if not os.path.exists(photo_path):
        print("  → 需要添加 skrtao 的照片")
    if skrtao_label is None:
        print("  → 需要重新训练模型")

print("\n" + "=" * 60)


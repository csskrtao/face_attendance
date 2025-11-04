# -*- coding: utf-8 -*-
"""
测试人脸检测 - 检查照片是否适合训练
"""

import cv2
import os
import sys

def test_face_detection(image_path):
    """测试单张图片的人脸检测"""
    print(f"\n检测图片: {image_path}")
    
    if not os.path.exists(image_path):
        print("  ✗ 文件不存在")
        return False
    
    # 读取图片
    img = cv2.imread(image_path)
    if img is None:
        print("  ✗ 无法读取图片（可能格式不支持）")
        return False
    
    height, width = img.shape[:2]
    print(f"  图片尺寸: {width}x{height}")
    
    # 转换为灰度图
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 加载人脸检测器
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # 尝试多种参数检测
    print("  尝试检测人脸...")
    
    # 参数1: 标准检测
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    if len(faces) > 0:
        print(f"  ✓ 检测到 {len(faces)} 个人脸 (标准参数)")
    else:
        # 参数2: 降低要求
        faces = face_cascade.detectMultiScale(gray, 1.05, 3)
        if len(faces) > 0:
            print(f"  ✓ 检测到 {len(faces)} 个人脸 (宽松参数)")
        else:
            # 参数3: 进一步降低
            faces = face_cascade.detectMultiScale(gray, 1.02, 2, minSize=(30, 30))
            if len(faces) > 0:
                print(f"  ✓ 检测到 {len(faces)} 个人脸 (最宽松参数)")
    
    if len(faces) == 0:
        print("  ✗ 未检测到人脸")
        print("\n  建议:")
        print("    • 使用正面照片")
        print("    • 确保光线充足")
        print("    • 人脸占图片30%以上")
        print("    • 避免遮挡（口罩、墨镜等）")
        return False
    
    # 显示检测到的人脸信息
    for i, (x, y, w, h) in enumerate(faces):
        face_percent = (w * h) / (width * height) * 100
        print(f"  人脸 {i+1}: 位置({x},{y}) 大小{w}x{h} 占比{face_percent:.1f}%")
        
        # 在图片上标记人脸
        cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
    
    # 保存标记后的图片
    output_path = image_path.replace('.jpg', '_detected.jpg').replace('.png', '_detected.png')
    cv2.imwrite(output_path, img)
    print(f"  ✓ 已保存标记图片: {output_path}")
    
    return True

def test_faces_directory():
    """测试faces目录下的所有图片"""
    print("=" * 60)
    print("人脸检测测试工具")
    print("=" * 60)
    
    if not os.path.exists("faces"):
        print("\n✗ faces目录不存在")
        return
    
    # 获取所有图片文件
    image_files = [f for f in os.listdir("faces") if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not image_files:
        print("\n✗ faces目录下没有图片文件")
        return
    
    print(f"\n找到 {len(image_files)} 个图片文件\n")
    
    success_count = 0
    failed_files = []
    
    for img_file in image_files:
        if '_detected' in img_file:
            continue  # 跳过已标记的图片
        
        img_path = os.path.join("faces", img_file)
        if test_face_detection(img_path):
            success_count += 1
        else:
            failed_files.append(img_file)
    
    print("\n" + "=" * 60)
    print("检测结果汇总:")
    print("=" * 60)
    print(f"✓ 成功: {success_count} 个")
    print(f"✗ 失败: {len(failed_files)} 个")
    
    if failed_files:
        print(f"\n失败的文件:")
        for f in failed_files:
            print(f"  - {f}")
    
    print("\n提示: 标记后的图片已保存为 *_detected.jpg，可以查看人脸检测位置")
    print("=" * 60)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 测试指定的图片
        test_face_detection(sys.argv[1])
    else:
        # 测试faces目录
        test_faces_directory()


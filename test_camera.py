# -*- coding: utf-8 -*-
"""
测试摄像头是否可用
"""

import cv2
import sys

def test_camera(camera_index):
    """测试指定索引的摄像头"""
    print(f"\n测试摄像头 {camera_index}...")
    
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print(f"  ✗ 摄像头 {camera_index} 无法打开")
        return False
    
    # 尝试读取一帧
    ret, frame = cap.read()
    
    if ret:
        height, width = frame.shape[:2]
        print(f"  ✓ 摄像头 {camera_index} 可用")
        print(f"    分辨率: {width}x{height}")
        cap.release()
        return True
    else:
        print(f"  ✗ 摄像头 {camera_index} 无法读取画面")
        cap.release()
        return False

def main():
    print("=" * 60)
    print("摄像头测试工具")
    print("=" * 60)
    
    # 测试前5个摄像头索引
    available_cameras = []
    
    for i in range(5):
        if test_camera(i):
            available_cameras.append(i)
    
    print("\n" + "=" * 60)
    print("测试结果:")
    print("=" * 60)
    
    if available_cameras:
        print(f"✓ 找到 {len(available_cameras)} 个可用摄像头: {available_cameras}")
        print(f"\n建议使用摄像头索引: {available_cameras[0]}")
    else:
        print("✗ 没有找到可用的摄像头")
        print("\n可能的原因:")
        print("1. 摄像头被其他程序占用（如Zoom、Teams、Skype等）")
        print("2. 摄像头驱动未安装或损坏")
        print("3. 摄像头权限未授予Python")
        print("4. 没有连接摄像头")
        print("\n解决方法:")
        print("1. 关闭所有使用摄像头的程序")
        print("2. 检查设备管理器中的摄像头状态")
        print("3. 重新插拔USB摄像头（如果是外接摄像头）")
    
    print("=" * 60)

if __name__ == "__main__":
    main()


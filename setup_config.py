# -*- coding: utf-8 -*-
"""
配置文件设置助手
帮助用户快速创建config.py文件
"""

import os
import shutil

def setup_config():
    """设置配置文件"""
    print("=" * 60)
    print("配置文件设置助手")
    print("=" * 60)
    
    # 检查config.py是否已存在
    if os.path.exists("config.py"):
        print("\n⚠️  config.py 已存在")
        choice = input("是否覆盖现有配置？(y/N): ").strip().lower()
        if choice != 'y':
            print("已取消设置")
            return
    
    # 检查config.example.py是否存在
    if not os.path.exists("config.example.py"):
        print("\n❌ 错误: config.example.py 不存在")
        print("请确保您在正确的目录中运行此脚本")
        return
    
    print("\n请输入您的LLM API配置信息：")
    print("(直接按回车使用默认值)")
    
    # 获取用户输入
    api_url = input("\nAPI URL [https://api.deepseek.com/v1/chat/completions]: ").strip()
    if not api_url:
        api_url = "https://api.deepseek.com/v1/chat/completions"
    
    api_key = input("API Key [YOUR_API_KEY_HERE]: ").strip()
    if not api_key:
        api_key = "YOUR_API_KEY_HERE"
    
    model = input("Model [deepseek-chat]: ").strip()
    if not model:
        model = "deepseek-chat"
    
    # 创建config.py
    config_content = f'''# -*- coding: utf-8 -*-
"""
配置文件 - 包含API密钥等敏感信息
注意：此文件不应上传到GitHub
"""

# LLM API 配置
LLM_API_URL = "{api_url}"
LLM_API_KEY = "{api_key}"
LLM_MODEL = "{model}"
'''
    
    try:
        with open("config.py", 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print("\n✅ config.py 创建成功！")
        print("\n配置内容：")
        print(f"  API URL: {api_url}")
        print(f"  API Key: {api_key[:20]}..." if len(api_key) > 20 else f"  API Key: {api_key}")
        print(f"  Model: {model}")
        
        print("\n⚠️  重要提示：")
        print("  1. config.py 包含敏感信息，不会被上传到GitHub")
        print("  2. 请妥善保管您的API密钥")
        print("  3. 如需修改配置，可直接编辑 config.py 文件")
        
    except Exception as e:
        print(f"\n❌ 创建配置文件失败: {str(e)}")

if __name__ == "__main__":
    setup_config()


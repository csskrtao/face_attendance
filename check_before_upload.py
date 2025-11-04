# -*- coding: utf-8 -*-
"""
上传前安全检查工具
"""

import subprocess
import os

def run_command(cmd):
    """运行命令并返回输出"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8')
        return result.stdout.strip()
    except Exception as e:
        return f"错误: {str(e)}"

def check_git_files():
    """检查Git暂存的文件"""
    print("=" * 60)
    print("Git暂存文件检查")
    print("=" * 60)
    
    output = run_command("git ls-files")
    files = output.split('\n') if output else []
    
    # 敏感文件列表（这些文件不应该被上传）
    sensitive_files = [
        'config.py',  # 包含真实API密钥
        'employees.json',  # 员工数据
        'attendance.csv',  # 考勤记录
        'face_model.yml',  # 训练好的模型
        'face_labels.pkl'  # 模型标签
    ]

    # 注意：config.example.py 和 setup_config.py 应该上传
    
    # 敏感目录
    sensitive_dirs = ['faces/']
    
    found_sensitive = []
    
    for file in files:
        # 检查敏感文件（精确匹配，避免误判）
        if file in sensitive_files:
            found_sensitive.append(file)

        # 检查敏感目录（排除.gitkeep）
        if any(file.startswith(sd) for sd in sensitive_dirs):
            if not file.endswith('.gitkeep'):
                found_sensitive.append(file)
    
    if found_sensitive:
        print("\n❌ 发现敏感文件将被上传：")
        for f in found_sensitive:
            print(f"  - {f}")
        print("\n请运行以下命令移除：")
        for f in found_sensitive:
            print(f"  git rm --cached {f}")
        return False
    else:
        print("\n✅ 未发现敏感文件")
        return True

def check_api_key_in_code():
    """检查代码中是否有硬编码的API密钥"""
    print("\n" + "=" * 60)
    print("API密钥检查")
    print("=" * 60)
    
    # 检查主程序文件
    if os.path.exists("attendance_system_opencv.py"):
        with open("attendance_system_opencv.py", 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否有长字符串（可能是API密钥）
        if 'eyJhbGciOiJIUzI1NiIsImtpZCI' in content:
            print("\n❌ 在代码中发现疑似API密钥！")
            print("请确保API密钥只在config.py中")
            return False
        
        # 检查是否正确导入config
        if 'from config import' in content:
            print("\n✅ 代码正确使用config.py导入配置")
            return True
        else:
            print("\n⚠️  代码中未找到config导入")
            return False
    else:
        print("\n⚠️  未找到主程序文件")
        return False

def check_config_files():
    """检查配置文件"""
    print("\n" + "=" * 60)
    print("配置文件检查")
    print("=" * 60)
    
    checks = []
    
    # 检查config.example.py存在
    if os.path.exists("config.example.py"):
        print("✅ config.example.py 存在")
        checks.append(True)
    else:
        print("❌ config.example.py 不存在")
        checks.append(False)
    
    # 检查config.py存在（本地）
    if os.path.exists("config.py"):
        print("✅ config.py 存在（本地）")
        checks.append(True)
    else:
        print("⚠️  config.py 不存在（用户需要创建）")
        checks.append(True)  # 这是正常的
    
    # 检查.gitignore存在
    if os.path.exists(".gitignore"):
        with open(".gitignore", 'r', encoding='utf-8') as f:
            gitignore_content = f.read()
        
        if 'config.py' in gitignore_content:
            print("✅ .gitignore 包含 config.py")
            checks.append(True)
        else:
            print("❌ .gitignore 未包含 config.py")
            checks.append(False)
    else:
        print("❌ .gitignore 不存在")
        checks.append(False)
    
    return all(checks)

def main():
    """主函数"""
    print("\n🔒 GitHub上传前安全检查\n")
    
    results = []
    
    # 执行检查
    results.append(("Git暂存文件", check_git_files()))
    results.append(("API密钥", check_api_key_in_code()))
    results.append(("配置文件", check_config_files()))
    
    # 总结
    print("\n" + "=" * 60)
    print("检查总结")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("✅ 所有检查通过！可以安全上传到GitHub")
        print("\n下一步：")
        print("  git commit -m '您的提交信息'")
        print("  git push")
    else:
        print("❌ 检查未通过，请修复上述问题后再上传")
    
    print("=" * 60)

if __name__ == "__main__":
    main()


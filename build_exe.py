#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
打包脚本 - 将群晖NAS文件管理器打包为EXE可执行文件
使用PyInstaller进行打包

安装要求:
pip install pyinstaller

使用方法:
python build_exe.py
"""

import os
import sys
import subprocess
import shutil

def check_requirements():
    """检查打包环境"""
    print("检查打包环境...")
    
    # 检查PyInstaller是否安装
    try:
        import PyInstaller
        print("✓ PyInstaller已安装")
    except ImportError:
        print("✗ PyInstaller未安装，正在安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller安装完成")
    
    # 检查主程序文件
    if not os.path.exists("synology_nas_manager.py"):
        print("✗ 找不到主程序文件 synology_nas_manager.py")
        return False
    
    # 检查requirements.txt
    if not os.path.exists("requirements.txt"):
        print("✗ 找不到 requirements.txt")
        return False
    
    print("✓ 环境检查完成")
    return True

def install_dependencies():
    """安装所有依赖"""
    print("安装项目依赖...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ 依赖安装完成")
    except subprocess.CalledProcessError as e:
        print(f"✗ 依赖安装失败: {e}")
        return False
    return True

def build_exe():
    """构建EXE文件"""
    print("开始构建EXE文件...")
    
    # PyInstaller命令参数
    cmd = [
        "pyinstaller",
        "--onefile",                    # 打包成单个exe文件
        "--windowed",                   # 不显示控制台窗口
        "--name=群晖NAS文件管理器",       # 可执行文件名称
        "--hidden-import=tkinter",      # 确保tkinter被包含
        "--hidden-import=requests",     # 确保requests被包含
        "--hidden-import=cryptography", # 确保cryptography被包含
        "--clean",                      # 清理缓存
        "synology_nas_manager.py"       # 主程序文件
    ]
    
    # 添加图标文件（如果存在）
    if os.path.exists("app.ico"):
        icon_path = os.path.abspath("app.ico")
        cmd.append(f"--icon={icon_path}")
        cmd.append(f"--add-data=app.ico;.")  # 同时将图标文件包含到资源中
        print(f"使用图标文件: {icon_path}")
    else:
        print("未找到图标文件，将使用默认图标")
    
    # 添加配置文件（如果存在）
    if os.path.exists("nas_config.ini"):
        cmd.append("--add-data=nas_config.ini;.")
    
    # 添加images文件夹（如果存在）
    if os.path.exists("images"):
        cmd.append("--add-data=images;images")  # 将images文件夹包含到资源中
        print("✓ 包含images文件夹")
    else:
        print("⚠ 未找到images文件夹")
    
    try:
        print(f"执行命令: {' '.join(cmd)}")
        subprocess.check_call(cmd)
        print("✓ EXE构建完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ EXE构建失败: {e}")
        return False

def create_spec_file():
    """创建自定义的spec文件以获得更好的控制"""
    # 检查图标文件是否存在
    icon_path = None
    if os.path.exists('app.ico'):
        icon_path = os.path.abspath('app.ico')
        print(f"找到图标文件: {icon_path}")
    else:
        print("未找到图标文件 app.ico，将使用默认图标")
    
    # 准备数据文件列表
    datas = []
    if os.path.exists('app.ico'):
        datas.append(('app.ico', '.'))
    if os.path.exists('images'):
        datas.append(('images', 'images'))
        print("✓ 包含images文件夹到spec文件")
    if os.path.exists('nas_config.ini'):
        datas.append(('nas_config.ini', '.'))
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['synology_nas_manager.py'],
    pathex=[],
    binaries=[],
    datas={datas},
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.simpledialog',
        'requests',
        'cryptography',
        'cryptography.fernet',
        'configparser',
        'threading',
        'datetime',
        'json',
        'os',
        'time',
        'urllib.parse',
        'hashlib',
        'base64'
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='群晖NAS文件管理器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon={repr(icon_path)},
)
'''
    
    with open('synology_nas_manager.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print("✓ 创建了自定义spec文件")

def build_with_spec():
    """使用spec文件构建"""
    print("使用spec文件构建EXE...")
    
    try:
        cmd = ["pyinstaller", "--clean", "synology_nas_manager.spec"]
        print(f"执行命令: {' '.join(cmd)}")
        subprocess.check_call(cmd)
        print("✓ 使用spec文件构建完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ spec文件构建失败: {e}")
        return False

def cleanup_and_organize():
    """清理临时文件并组织输出"""
    print("清理和组织文件...")
    
    # 创建发布目录
    release_dir = "release"
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
    os.makedirs(release_dir)
    
    # 移动EXE文件
    exe_path = os.path.join("dist", "群晖NAS文件管理器.exe")
    if os.path.exists(exe_path):
        target_path = os.path.join(release_dir, "群晖NAS文件管理器.exe")
        shutil.move(exe_path, target_path)
        print(f"✓ EXE文件已移动到: {target_path}")
        
        # 获取文件大小
        size_mb = os.path.getsize(target_path) / (1024 * 1024)
        print(f"✓ EXE文件大小: {size_mb:.1f} MB")
    else:
        print("✗ 找不到生成的EXE文件")
        return False
    
    # 复制README和其他文档
    docs_to_copy = ["README.md", "requirements.txt"]
    for doc in docs_to_copy:
        if os.path.exists(doc):
            shutil.copy2(doc, release_dir)
            print(f"✓ 复制文档: {doc}")
    
    # 创建使用说明
    usage_text = """
群晖NAS文件管理器 使用说明
================================

这是一个可以直接运行的可执行文件，无需安装Python环境。

使用方法：
1. 双击运行 "群晖NAS文件管理器.exe"
2. 输入您的群晖NAS连接信息
3. 开始管理您的NAS文件

功能特点：
- 多用户配置管理
- 加密密码保存
- 文件上传下载
- 目录浏览
- 进度显示

注意事项：
- 首次运行可能需要几秒钟启动时间
- 确保网络连接正常
- 确保NAS地址和端口正确

如有问题，请参考 README.md 文件。
"""
    
    with open(os.path.join(release_dir, "使用说明.txt"), 'w', encoding='utf-8') as f:
        f.write(usage_text)
    
    # 清理临时文件
    temp_dirs = ["build", "dist", "__pycache__"]
    for temp_dir in temp_dirs:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"✓ 清理临时目录: {temp_dir}")
    
    # 清理spec文件
    if os.path.exists("synology_nas_manager.spec"):
        os.remove("synology_nas_manager.spec")
        print("✓ 清理spec文件")
    
    print(f"✓ 发布文件已准备完成，位于: {release_dir}/")
    return True

def main():
    """主函数"""
    print("=" * 50)
    print("群晖NAS文件管理器 EXE打包工具")
    print("=" * 50)
    
    # 检查环境
    if not check_requirements():
        print("环境检查失败，退出...")
        return False
    
    # 安装依赖
    if not install_dependencies():
        print("依赖安装失败，退出...")
        return False
    
    # 创建spec文件
    create_spec_file()
    
    # 构建EXE
    if not build_with_spec():
        print("EXE构建失败，尝试简单构建...")
        if not build_exe():
            print("所有构建方法都失败了，退出...")
            return False
    
    # 清理和组织
    if not cleanup_and_organize():
        print("文件组织失败...")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 EXE打包完成！")
    print("=" * 50)
    print("可执行文件位置: release/群晖NAS文件管理器.exe")
    print("您现在可以将此文件复制到任何Windows电脑上运行")
    print("无需安装Python环境！")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
创建应用程序图标
使用PIL生成一个简单的应用图标
"""

try:
    from PIL import Image, ImageDraw, ImageFont
    print("PIL库可用，创建图标...")
    
    # 创建图标
    size = 256
    image = Image.new('RGBA', (size, size), (70, 130, 180, 255))  # 钢蓝色背景
    draw = ImageDraw.Draw(image)
    
    # 绘制文件夹图标
    folder_color = (255, 255, 255, 255)  # 白色
    margin = size // 8
    
    # 文件夹主体
    folder_width = size - 2 * margin
    folder_height = folder_width * 3 // 4
    folder_x = margin
    folder_y = margin + size // 8
    
    # 绘制文件夹
    draw.rectangle([folder_x, folder_y, folder_x + folder_width, folder_y + folder_height], 
                  fill=folder_color, outline=(200, 200, 200, 255), width=2)
    
    # 文件夹标签
    tab_width = folder_width // 3
    tab_height = folder_height // 4
    draw.rectangle([folder_x, folder_y - tab_height, folder_x + tab_width, folder_y], 
                  fill=folder_color, outline=(200, 200, 200, 255), width=2)
    
    # 添加NAS标识
    try:
        # 尝试使用系统字体
        font_size = size // 8
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        # 如果找不到字体，使用默认字体
        font = ImageFont.load_default()
    
    text = "NAS"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (size - text_width) // 2
    text_y = folder_y + folder_height + margin
    
    draw.text((text_x, text_y), text, fill=(255, 255, 255, 255), font=font)
    
    # 保存为ICO文件，包含多个尺寸
    # 首先创建不同尺寸的图标
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    images = []
    
    for size in sizes:
        # 为每个尺寸创建图标
        resized = image.resize(size, Image.Resampling.LANCZOS)
        images.append(resized)
    
    # 保存为真正的ICO文件
    images[0].save('app.ico', format='ICO', sizes=[img.size for img in images], append_images=images[1:])
    print("✓ 图标文件 app.ico 创建成功")
    print(f"✓ 包含 {len(sizes)} 个尺寸: {', '.join([f'{s[0]}x{s[1]}' for s in sizes])}")
    
except ImportError:
    print("PIL库未安装，正在安装...")
    import subprocess
    import sys
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
        print("✓ Pillow安装完成，请重新运行此脚本")
    except subprocess.CalledProcessError:
        print("✗ Pillow安装失败")
        print("提示：您可以从网上下载一个 .ico 图标文件并重命名为 app.ico")
        
        # 创建一个简单的文本说明
        with open('icon_instructions.txt', 'w', encoding='utf-8') as f:
            f.write("""
图标文件说明
===========

如果您想为应用程序添加自定义图标：

1. 准备一个 ICO 格式的图标文件
2. 将文件重命名为 app.ico
3. 放在与主程序相同的目录中
4. 重新运行打包脚本

推荐图标尺寸：256x256 像素
文件格式：ICO

您也可以不添加图标，程序将使用默认图标。
""")
        print("✓ 创建了图标使用说明文件")

except Exception as e:
    print(f"✗ 创建图标时出错: {e}")
    print("提示：您可以跳过图标创建，直接进行打包") 
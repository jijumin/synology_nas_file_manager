import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import requests
import json
import threading
import os
import sys
from urllib.parse import quote, urljoin
import time
from datetime import datetime
import configparser
import base64
from cryptography.fernet import Fernet
import hashlib
import tempfile


class ImagePreviewWindow:
    """图片预览窗口"""
    def __init__(self, parent, image_path, filename):
        self.window = tk.Toplevel(parent)
        self.window.title(f"图片预览 - {filename}")
        self.window.geometry("800x600")
        self.window.minsize(400, 300)
        
        # 设置窗口图标
        self.set_window_icon()
        
        # 创建界面
        self.create_widgets(image_path, filename)
        
        # 居中显示
        self.window.transient(parent)
        self.window.grab_set()
        self.center_window()
    
    def set_window_icon(self):
        """设置窗口图标"""
        icon_paths = [
            "app.ico",                    # 开发环境
            os.path.join(os.path.dirname(__file__), "app.ico"),  # 同目录
        ]
        
        for icon_path in icon_paths:
            try:
                if os.path.exists(icon_path):
                    self.window.iconbitmap(icon_path)
                    print(f"✓ 图片预览窗口图标已设置: {icon_path}")
                    return
            except Exception as e:
                print(f"⚠ 尝试设置图片预览窗口图标 {icon_path} 失败: {e}")
                continue
        
        print("⚠ 未找到可用的图片预览窗口图标文件")
        
    def center_window(self):
        """居中显示窗口"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        
    def create_widgets(self, image_path, filename):
        """创建预览界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题栏
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(title_frame, text=f"文件名: {filename}", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        
        # 关闭按钮
        ttk.Button(title_frame, text="关闭", command=self.window.destroy).pack(side=tk.RIGHT)
        
        # 图片显示区域
        self.image_frame = ttk.Frame(main_frame, relief='sunken', borderwidth=1)
        self.image_frame.pack(fill=tk.BOTH, expand=True)
        
        # 等待窗口完全加载后再显示图片
        self.window.after(100, lambda: self.load_image(image_path))
        
        # 绑定窗口大小改变事件
        self.window.bind('<Configure>', self.on_window_resize)
        
    def load_image(self, image_path):
        """加载并显示图片"""
        try:
            from PIL import Image, ImageTk
            
            # 保存原始图片路径
            self.original_image_path = image_path
            
            # 检查文件是否存在
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"图片文件不存在: {image_path}")
            
            # 打开图片
            image = Image.open(image_path)
            
            # 获取窗口大小
            self.window.update()
            window_width = self.image_frame.winfo_width()
            window_height = self.image_frame.winfo_height()
            
            if window_width <= 1 or window_height <= 1:
                # 如果窗口还没完全加载，使用默认大小
                window_width, window_height = 780, 580
            
            # 计算缩放比例
            img_width, img_height = image.size
            scale_x = window_width / img_width
            scale_y = window_height / img_height
            scale = min(scale_x, scale_y, 1.0)  # 不放大，只缩小
            
            # 缩放图片
            if scale < 1.0:
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 转换为PhotoImage并保存引用
            self.photo = ImageTk.PhotoImage(image)
            
            # 清除现有内容
            for widget in self.image_frame.winfo_children():
                widget.destroy()
            
            # 创建标签显示图片
            self.image_label = ttk.Label(self.image_frame, image=self.photo)
            self.image_label.pack(expand=True)
            
            # 保存图片引用，防止被垃圾回收
            self.image_label.image = self.photo
            
            # 保存图片对象引用
            self.current_image = image
            
            print(f"✓ 图片加载成功: {image_path} ({img_width}x{img_height})")
            
        except ImportError:
            # 如果没有PIL，显示错误信息
            error_label = ttk.Label(self.image_frame, text="无法预览图片\n请安装Pillow库: pip install Pillow", 
                                   font=('Arial', 12), foreground='red')
            error_label.pack(expand=True)
            print("⚠ PIL库未安装，无法预览图片")
        except Exception as e:
            # 显示错误信息
            error_label = ttk.Label(self.image_frame, text=f"加载图片失败:\n{str(e)}", 
                                   font=('Arial', 12), foreground='red')
            error_label.pack(expand=True)
            print(f"⚠ 图片加载失败: {str(e)}")
    
    def on_window_resize(self, event):
        """窗口大小改变时重新加载图片"""
        # 防止频繁重新加载
        if hasattr(self, '_resize_timer'):
            self.window.after_cancel(self._resize_timer)
        
        self._resize_timer = self.window.after(200, self._delayed_resize)
    
    def _delayed_resize(self):
        """延迟重新加载图片，避免频繁刷新"""
        if hasattr(self, 'original_image_path'):
            self.load_image(self.original_image_path)


class VideoPreviewWindow:
    """视频预览窗口"""
    def __init__(self, parent, video_path, filename):
        self.window = tk.Toplevel(parent)
        self.window.title(f"视频预览 - {filename}")
        self.window.geometry("900x700")
        self.window.minsize(600, 400)
        
        # 设置窗口图标
        self.set_window_icon()
        
        # 创建界面
        self.create_widgets(video_path, filename)
        
        # 居中显示
        self.window.transient(parent)
        self.window.grab_set()
        self.center_window()
    
    def set_window_icon(self):
        """设置窗口图标"""
        icon_paths = [
            "app.ico",                    # 开发环境
            os.path.join(os.path.dirname(__file__), "app.ico"),  # 同目录
        ]
        
        for icon_path in icon_paths:
            try:
                if os.path.exists(icon_path):
                    self.window.iconbitmap(icon_path)
                    print(f"✓ 视频预览窗口图标已设置: {icon_path}")
                    return
            except Exception as e:
                print(f"⚠ 尝试设置视频预览窗口图标 {icon_path} 失败: {e}")
                continue
        
        print("⚠ 未找到可用的视频预览窗口图标文件")
        
    def center_window(self):
        """居中显示窗口"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        
    def create_widgets(self, video_path, filename):
        """创建预览界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题栏
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(title_frame, text=f"文件名: {filename}", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        
        # 关闭按钮
        ttk.Button(title_frame, text="关闭", command=self.window.destroy).pack(side=tk.RIGHT)
        
        # 视频播放区域
        self.video_frame = ttk.Frame(main_frame, relief='sunken', borderwidth=1)
        self.video_frame.pack(fill=tk.BOTH, expand=True)
        
        # 等待窗口完全加载后再播放视频
        self.window.after(100, lambda: self.play_video(video_path))
        
    def play_video(self, video_path):
        """播放视频"""
        try:
            # 尝试使用系统默认播放器播放视频
            import subprocess
            import platform
            
            system = platform.system()
            
            if system == "Windows":
                # Windows系统使用默认程序播放
                os.startfile(video_path)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", video_path])
            else:  # Linux
                subprocess.run(["xdg-open", video_path])
            
            # 显示成功信息
            success_label = ttk.Label(self.video_frame, 
                                     text=f"视频已使用系统默认播放器打开\n文件路径: {video_path}", 
                                     font=('Arial', 12), foreground='green')
            success_label.pack(expand=True)
            
            print(f"✓ 视频播放成功: {video_path}")
            
        except Exception as e:
            # 显示错误信息
            error_label = ttk.Label(self.video_frame, 
                                   text=f"无法播放视频:\n{str(e)}\n\n请确保系统已安装视频播放器", 
                                   font=('Arial', 12), foreground='red')
            error_label.pack(expand=True)
            print(f"⚠ 视频播放失败: {str(e)}")


class SynologyNASManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("群辉NAS文件管理器")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
        # 配置变量
        self.nas_url = tk.StringVar()
        self.username = tk.StringVar()
        self.password = tk.StringVar()
        self.session_id = None
        self.api_info = {}
        self.last_login_info = None  # 保存最后一次成功登录的信息
        self.session = requests.Session()  # 使用Session保持cookie
        
        # 当前路径
        self.current_path = "/"
        
        # 显示模式
        self.view_mode = tk.StringVar()
        self.view_mode.set("列表视图")  # 默认为列表视图
        
        # 配置文件路径
        self.config_file = "nas_config.ini"
        self.remember_password = tk.BooleanVar()
        self.selected_profile = tk.StringVar()
        self.profiles = {}  # 存储多个用户配置
        
        # 创建GUI
        self.create_widgets()
        
        # 加载保存的配置（在UI创建完成后）
        self.root.after(100, self.load_config)  # 延迟加载配置
        
        # 设置样式
        self.setup_styles()
        
    def setup_styles(self):
        """设置UI样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置样式
        style.configure('Title.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Header.TLabel', font=('Arial', 10, 'bold'))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
    
    def get_resource_path(self, relative_path):
        """获取资源文件的绝对路径，兼容打包后的环境"""
        try:
            # PyInstaller创建的临时文件夹
            base_path = sys._MEIPASS
        except Exception:
            # 开发环境
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)
    
    def set_window_icon(self):
        """设置窗口图标"""
        icon_paths = [
            "app.ico",                    # 开发环境
            self.get_resource_path("app.ico"),  # 打包环境
            os.path.join(os.path.dirname(__file__), "app.ico"),  # 同目录
        ]
        
        for icon_path in icon_paths:
            try:
                if os.path.exists(icon_path):
                    self.root.iconbitmap(icon_path)
                    print(f"✓ 已设置窗口图标: {icon_path}")
                    return
            except Exception as e:
                print(f"⚠ 尝试设置图标 {icon_path} 失败: {e}")
                continue
        
        print("⚠ 未找到可用的图标文件")
    
    def load_folder_icons(self):
        """加载文件夹图标"""
        self.folder_icons = {}
        try:
            from PIL import Image, ImageTk
            
            # 图标文件路径和目标尺寸
            icon_configs = [
                # 目录树用的小图标
                ('folder_closed_tree', 'images/icons8-文件夹-50.png', (16, 16)),
                ('folder_open_tree', 'images/icons8-打开文件夹-50.png', (16, 16)),
                # 列表视图用的图标
                ('folder_closed_list', 'images/icons8-文件夹-50.png', (20, 20)),
                ('folder_open_list', 'images/icons8-打开文件夹-50.png', (20, 20)),
                # 小图标视图
                ('folder_closed_small', 'images/icons8-文件夹-50.png', (24, 24)),
                ('folder_open_small', 'images/icons8-打开文件夹-50.png', (24, 24)),
                # 中图标视图
                ('folder_closed_medium', 'images/icons8-文件夹-100.png', (32, 32)),
                ('folder_open_medium', 'images/icons8-打开文件夹-100.png', (32, 32)),
                # 大图标视图
                ('folder_closed_large', 'images/icons8-文件夹-100.png', (48, 48)),
                ('folder_open_large', 'images/icons8-打开文件夹-100.png', (48, 48)),
                # 平铺视图
                ('folder_closed_tile', 'images/icons8-文件夹-100.png', (40, 40)),
                ('folder_open_tile', 'images/icons8-打开文件夹-100.png', (40, 40)),
            ]
            
            for key, filename, size in icon_configs:
                try:
                    # 尝试多种路径查找图标文件
                    icon_paths = [
                        filename,  # 开发环境
                        self.get_resource_path(filename),  # 打包环境
                        os.path.join(os.path.dirname(__file__), filename),  # 同目录
                    ]
                    
                    icon_loaded = False
                    for icon_path in icon_paths:
                        if os.path.exists(icon_path):
                            image = Image.open(icon_path)
                            image = image.resize(size, Image.Resampling.LANCZOS)
                            self.folder_icons[key] = ImageTk.PhotoImage(image)
                            print(f"✓ 已加载图标: {icon_path} -> {key} ({size[0]}x{size[1]})")
                            icon_loaded = True
                            break
                    
                    if not icon_loaded:
                        print(f"⚠ 未找到图标文件: {filename}")
                        
                except Exception as e:
                    print(f"⚠ 加载图标 {filename} 失败: {e}")
                    
        except ImportError:
            print("⚠ PIL库未安装，无法加载文件夹图标")
            # 尝试安装PIL
            try:
                import subprocess
                import sys
                subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
                print("✓ Pillow安装完成，请重新启动程序以加载图标")
            except:
                print("⚠ Pillow安装失败，将使用文本标识")
        except Exception as e:
            print(f"⚠ 加载文件夹图标失败: {e}")
        
    def create_widgets(self):
        """创建主界面组件"""
        # 设置窗口图标
        self.set_window_icon()
        
        # 加载文件夹图标
        self.load_folder_icons()
        
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 创建登录区域
        self.create_login_frame(main_frame)
        
        # 创建主工作区域
        self.create_main_workspace(main_frame)
        
        # 创建状态栏
        self.create_status_bar(main_frame)
        
    def create_login_frame(self, parent):
        """创建登录界面"""
        login_frame = ttk.LabelFrame(parent, text="NAS连接设置", padding="10")
        login_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        # 设置列权重，让NAS地址列可以拉伸
        login_frame.columnconfigure(3, weight=1)
        
        # 第一行：配置选择和登录信息
        # 配置选择
        ttk.Label(login_frame, text="配置:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.profile_combo = ttk.Combobox(login_frame, textvariable=self.selected_profile, width=15, state="readonly")
        self.profile_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        self.profile_combo.bind('<<ComboboxSelected>>', self.on_profile_selected)
        
        # NAS地址
        ttk.Label(login_frame, text="NAS地址:").grid(row=0, column=2, sticky=tk.W, padx=(10, 5))
        self.nas_entry = ttk.Entry(login_frame, textvariable=self.nas_url, width=25)
        self.nas_entry.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # 用户名
        ttk.Label(login_frame, text="用户名:").grid(row=0, column=4, sticky=tk.W, padx=(10, 5))
        self.username_entry = ttk.Entry(login_frame, textvariable=self.username, width=12)
        self.username_entry.grid(row=0, column=5, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # 密码
        ttk.Label(login_frame, text="密码:").grid(row=0, column=6, sticky=tk.W, padx=(10, 5))
        self.password_entry = ttk.Entry(login_frame, textvariable=self.password, show="*", width=12)
        self.password_entry.grid(row=0, column=7, sticky=(tk.W, tk.E), padx=(0, 10))
        # 绑定密码变化事件
        self.password.trace('w', self.on_password_changed)
        
        # 登录按钮
        self.login_btn = ttk.Button(login_frame, text="连接", command=self.login)
        self.login_btn.grid(row=0, column=8, padx=(10, 5))
        
        # 登出按钮
        self.logout_btn = ttk.Button(login_frame, text="断开", command=self.logout, state='disabled')
        self.logout_btn.grid(row=0, column=9, padx=(0, 0))
        
        # 第二行：功能选项和状态
        # 记住密码复选框
        remember_cb = ttk.Checkbutton(login_frame, text="记住配置", variable=self.remember_password, 
                                    command=self.on_remember_password_changed)
        remember_cb.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(8, 0))
        
        # 保存配置按钮
        save_btn = ttk.Button(login_frame, text="保存配置", command=self.save_current_profile)
        save_btn.grid(row=1, column=2, pady=(8, 0), padx=(10, 5))
        
        # 删除配置按钮
        delete_btn = ttk.Button(login_frame, text="删除配置", command=self.delete_current_profile)
        delete_btn.grid(row=1, column=3, pady=(8, 0), padx=(0, 10))
        
        # 连接状态标签
        self.connection_status = ttk.Label(login_frame, text="未连接", style='Error.TLabel')
        self.connection_status.grid(row=1, column=4, columnspan=4, sticky=tk.W, pady=(8, 0), padx=(10, 0))
        
        # 清除所有配置按钮
        clear_btn = ttk.Button(login_frame, text="清除所有", command=self.clear_all_profiles)
        clear_btn.grid(row=1, column=8, columnspan=2, sticky=tk.E, pady=(8, 0), padx=(10, 0))
        
    def create_main_workspace(self, parent):
        """创建主工作区域"""
        # 创建PanedWindow来分割左右区域
        paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        paned.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 左侧目录树区域
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)
        
        # 右侧文件列表区域
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)
        
        self.create_directory_tree(left_frame)
        self.create_file_list(right_frame)
        
    def create_directory_tree(self, parent):
        """创建目录树"""
        # 目录树标题
        ttk.Label(parent, text="文件夹", style='Header.TLabel').pack(anchor=tk.W, pady=(0, 5))
        
        # 创建Treeview用于显示目录
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.dir_tree = ttk.Treeview(tree_frame, selectmode='browse')
        self.dir_tree.heading('#0', text='文件夹', anchor=tk.W)
        
        # 添加滚动条
        dir_scrollbar_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.dir_tree.yview)
        dir_scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.dir_tree.xview)
        self.dir_tree.configure(yscrollcommand=dir_scrollbar_y.set, xscrollcommand=dir_scrollbar_x.set)
        
        # 布局
        self.dir_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        dir_scrollbar_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        dir_scrollbar_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # 绑定事件
        self.dir_tree.bind('<<TreeviewSelect>>', self.on_directory_select)
        self.dir_tree.bind('<<TreeviewOpen>>', self.on_directory_expand)
        
    def create_file_list(self, parent):
        """创建文件列表"""
        # 文件列表区域
        file_frame = ttk.Frame(parent)
        file_frame.pack(fill=tk.BOTH, expand=True)
        
        # 顶部工具栏
        toolbar = ttk.Frame(file_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        # 左侧区域：当前路径
        left_frame = ttk.Frame(toolbar)
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(left_frame, text="当前路径:", style='Header.TLabel').pack(side=tk.LEFT, padx=(0, 5))
        self.path_label = ttk.Label(left_frame, text="/", relief='sunken', padding="2", anchor=tk.W)
        self.path_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # 中间区域：视图模式选择
        middle_frame = ttk.Frame(toolbar)
        middle_frame.pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Label(middle_frame, text="视图:").pack(side=tk.LEFT, padx=(0, 5))
        view_options = ["列表视图", "平铺视图", "小图标", "中图标", "大图标"]
        self.view_combo = ttk.Combobox(middle_frame, textvariable=self.view_mode, values=view_options, 
                                       state='readonly', width=8)
        self.view_combo.pack(side=tk.LEFT)
        self.view_combo.bind('<<ComboboxSelected>>', self.on_view_mode_changed)
        
        # 右侧区域：操作按钮
        right_frame = ttk.Frame(toolbar)
        right_frame.pack(side=tk.RIGHT)
        
        # 下载按钮
        self.download_btn = ttk.Button(right_frame, text="下载文件", command=self.download_file, state='disabled')
        self.download_btn.pack(side=tk.RIGHT, padx=(0, 5))
        
        # 上传按钮
        self.upload_btn = ttk.Button(right_frame, text="上传文件", command=self.upload_file, state='disabled')
        self.upload_btn.pack(side=tk.RIGHT, padx=(0, 5))
        
        # 预览按钮
        self.preview_btn = ttk.Button(right_frame, text="预览", command=self.preview_selected_file, state='disabled')
        self.preview_btn.pack(side=tk.RIGHT, padx=(0, 5))
        
        # 刷新按钮
        self.refresh_btn = ttk.Button(right_frame, text="刷新", command=self.refresh_file_list, state='disabled')
        self.refresh_btn.pack(side=tk.RIGHT)
        
        # 文件列表
        list_frame = ttk.Frame(file_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建Treeview显示文件
        columns = ('name', 'type', 'size', 'modified')
        self.file_list = ttk.Treeview(list_frame, columns=columns, show='headings', selectmode='browse')
        
        # 设置列标题
        self.file_list.heading('name', text='文件名')
        self.file_list.heading('type', text='类型')
        self.file_list.heading('size', text='大小')
        self.file_list.heading('modified', text='修改时间')
        
        # 设置列宽
        self.file_list.column('name', width=350, minwidth=200)
        self.file_list.column('type', width=100, minwidth=80)
        self.file_list.column('size', width=120, minwidth=80)
        self.file_list.column('modified', width=180, minwidth=120)
        
        # 添加滚动条
        file_scrollbar_y = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_list.yview)
        file_scrollbar_x = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.file_list.xview)
        self.file_list.configure(yscrollcommand=file_scrollbar_y.set, xscrollcommand=file_scrollbar_x.set)
        
        # 布局
        self.file_list.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        file_scrollbar_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        file_scrollbar_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # 绑定事件
        self.file_list.bind('<Double-1>', self.on_file_double_click)
        self.file_list.bind('<Button-3>', self.on_file_right_click)  # 右键菜单
        
        # 创建右键菜单
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="预览", command=self.preview_selected_file)
        self.context_menu.add_command(label="下载", command=self.download_selected_file)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="刷新", command=self.refresh_file_list)
        
        # 配置默认视图模式
        self.configure_file_list_view("列表视图")
        
    def create_status_bar(self, parent):
        """创建状态栏"""
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        status_frame.columnconfigure(0, weight=1)
        
        # 状态标签
        self.status_label = ttk.Label(status_frame, text="就绪")
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        # 进度条 (初始隐藏)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100)
        
    def show_progress(self, show=True):
        """显示或隐藏进度条"""
        if show:
            self.progress_bar.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
            self.status_label.grid(row=0, column=0, sticky=tk.W)
        else:
            self.progress_bar.grid_remove()
            
    def login(self):
        """登录到NAS"""
        nas_url = self.nas_url.get().strip()
        username = self.username.get().strip()
        password = self.password.get().strip()
        

        
        if not nas_url:
            messagebox.showerror("错误", "请输入NAS地址")
            return
        if not username:
            messagebox.showerror("错误", "请输入用户名")
            return
        if not password:
            messagebox.showerror("错误", "请输入密码")
            return
            
        # 在新线程中执行登录
        threading.Thread(target=self._login_thread, daemon=True).start()
        
    def _login_thread(self):
        """登录线程"""
        try:
            self.update_status("正在连接到NAS...")
            self.login_btn.configure(state='disabled')
            
            # 第一步：获取API信息
            api_url = f"{self.nas_url.get()}/webapi/query.cgi"
            params = {
                'api': 'SYNO.API.Info',
                'version': '1',
                'method': 'query',
                'query': 'SYNO.API.Auth,SYNO.FileStation.List,SYNO.FileStation.Upload,SYNO.FileStation.Download'
            }
            
            response = self.session.get(api_url, params=params, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if not result.get('success'):
                raise Exception(f"获取API信息失败: {result.get('error', {})}")
                
            self.api_info = result['data']
            
            # 第二步：登录认证 - 使用Cookie格式
            auth_url = f"{self.nas_url.get()}/webapi/auth.cgi"
            auth_params = {
                'api': 'SYNO.API.Auth',
                'version': '7',  # 使用最高版本
                'method': 'login',
                'account': self.username.get(),
                'passwd': self.password.get(),
                'session': 'FileStation',
                'format': 'cookie'  # 使用cookie格式而不是sid
            }
            
            auth_response = self.session.get(auth_url, params=auth_params, timeout=10)
            auth_response.raise_for_status()
            
            auth_result = auth_response.json()
            if not auth_result.get('success'):
                error_code = auth_result.get('error', {}).get('code', 'unknown')
                error_messages = {
                    400: "账号或密码错误",
                    401: "账号已被禁用",
                    402: "权限不足",
                    403: "需要双重验证",
                    404: "双重验证码错误"
                }
                error_msg = error_messages.get(error_code, f"登录失败，错误代码: {error_code}")
                raise Exception(error_msg)
                
            # Cookie认证不需要保存SID，Session会自动管理
            self.session_id = "cookie_auth"  # 标记使用cookie认证
            
            # 验证登录后的会话是否有效
            if not self.verify_session():
                raise Exception("登录成功但会话验证失败，请检查账户权限")
            
            # 登录成功，更新UI
            self.root.after(0, self._on_login_success)
            
        except requests.exceptions.Timeout:
            self.root.after(0, lambda: self._on_login_error("连接超时，请检查NAS地址"))
        except requests.exceptions.ConnectionError:
            self.root.after(0, lambda: self._on_login_error("无法连接到NAS，请检查地址和端口"))
        except Exception as e:
            self.root.after(0, lambda: self._on_login_error(str(e)))
            
    def _on_login_success(self):
        """登录成功回调"""
        # 保存登录信息以便自动重连
        self.last_login_info = {
            'nas_url': self.nas_url.get(),
            'username': self.username.get(),
            'password': self.password.get()
        }
        
        # 如果已选择配置，则自动保存当前配置
        if self.selected_profile.get() and self.selected_profile.get() != "新建配置...":
            self.auto_save_current_profile()
        
        # 保存全局配置
        self.save_config()
        
        self.update_status("连接成功")
        self.connection_status.configure(text=f"已连接到 {self.nas_url.get()}", style='Success.TLabel')
        self.login_btn.configure(state='disabled')
        self.logout_btn.configure(state='normal')
        self.upload_btn.configure(state='normal')
        self.download_btn.configure(state='normal')
        self.refresh_btn.configure(state='normal')
        self.preview_btn.configure(state='normal')
        self.view_combo.configure(state='readonly')
        
        # 加载共享文件夹
        self.load_shared_folders()
        
    def _on_login_error(self, error_msg):
        """登录失败回调"""
        self.update_status("连接失败")
        self.connection_status.configure(text="连接失败", style='Error.TLabel')
        self.login_btn.configure(state='normal')
        messagebox.showerror("登录失败", error_msg)
        
    def verify_session(self):
        """验证会话是否有效"""
        if not self.session_id:
            return False
            
        try:
            # 使用一个简单的API调用来验证会话
            list_api_path = self.api_info.get('SYNO.FileStation.List', {}).get('path', 'entry.cgi')
            url = f"{self.nas_url.get()}/webapi/{list_api_path}"
            params = {
                'api': 'SYNO.FileStation.List',
                'version': '2',
                'method': 'list_share',
                'limit': '1'  # 只获取1个项目用于验证
                # 不传_sid，使用session的cookie
            }
            
            response = self.session.get(url, params=params, timeout=5)
            result = response.json()
            
            # 如果返回成功，说明会话有效
            return result.get('success', False)
            
        except:
            return False
    
    def refresh_session_if_needed(self):
        """验证会话，如果需要则刷新SID"""
        if not self.session_id or not self.last_login_info:
            return False
            
        # 先验证当前会话
        if self.verify_session():
            return True
            
        # 会话无效，尝试重新登录
        try:
            auth_url = f"{self.nas_url.get()}/webapi/auth.cgi"
            auth_params = {
                'api': 'SYNO.API.Auth',
                'version': '7',
                'method': 'login',
                'account': self.last_login_info['username'],
                'passwd': self.last_login_info['password'],
                'session': 'FileStation',
                'format': 'cookie'
            }
            
            auth_response = self.session.get(auth_url, params=auth_params, timeout=10)
            auth_result = auth_response.json()
            
            if auth_result.get('success'):
                self.session_id = "cookie_auth"  # 标记使用cookie认证
                return True
            else:
                return False
                
        except:
            return False
    
    def try_auto_login(self):
        """尝试自动重新登录"""
        if not self.last_login_info:
            messagebox.showerror("错误", "无法自动重新登录，请手动重新连接")
            return False
            
        try:
            self.update_status("正在自动重新登录...")
            
            # 恢复登录信息
            self.nas_url.set(self.last_login_info['nas_url'])
            self.username.set(self.last_login_info['username'])
            self.password.set(self.last_login_info['password'])
            
            # 禁用登录按钮，避免重复点击
            self.login_btn.configure(state='disabled')
            
            # 尝试重新登录
            threading.Thread(target=self._login_thread, daemon=True).start()
            return True
        except Exception as e:
            self.update_status(f"自动重新登录失败: {str(e)}")
            messagebox.showerror("自动登录失败", f"自动重新登录失败，请手动重新连接\n错误: {str(e)}")
            self.login_btn.configure(state='normal')
            return False
    
    def generate_key(self, password_hash):
        """根据密码哈希生成加密密钥"""
        # 使用密码哈希的前32位作为密钥
        key = base64.urlsafe_b64encode(password_hash[:32])
        return key
    
    def get_machine_key(self):
        """获取机器唯一密钥"""
        try:
            # 使用用户名和当前工作目录生成唯一标识
            machine_id = f"{os.getlogin()}:{os.getcwd()}"
            key_material = hashlib.sha256(machine_id.encode('utf-8')).digest()
            return base64.urlsafe_b64encode(key_material)
        except Exception as e:
            print(f"生成机器密钥失败: {e}")
            # 使用默认密钥作为备选方案
            default_key = hashlib.sha256(b"default_nas_app_key").digest()
            return base64.urlsafe_b64encode(default_key)
    
    def encrypt_password(self, password):
        """加密密码"""
        if not password:
            return ""
        try:
            key = self.get_machine_key()
            fernet = Fernet(key)
            encrypted = fernet.encrypt(password.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted).decode('utf-8')
        except Exception as e:
            print(f"加密密码失败: {e}")
            return ""
    
    def decrypt_password(self, encrypted_password):
        """解密密码"""
        if not encrypted_password:
            return ""
        try:
            key = self.get_machine_key()
            fernet = Fernet(key)
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_password.encode('utf-8'))
            decrypted = fernet.decrypt(encrypted_bytes)
            return decrypted.decode('utf-8')
        except Exception as e:
            print(f"解密密码失败: {e}")
            return ""
    
    def save_config(self):
        """保存所有配置到文件"""
        try:
            config = configparser.ConfigParser()
            
            # 保存最后选择的配置
            config['SETTINGS'] = {
                'last_profile': self.selected_profile.get(),
                'remember_password': str(self.remember_password.get())
            }
            
            # 保存所有用户配置
            for profile_name, profile_data in self.profiles.items():
                config[f'PROFILE_{profile_name}'] = profile_data
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                config.write(f)
                
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def load_config(self):
        """从文件加载配置"""
        try:
            if not os.path.exists(self.config_file):
                self.update_profile_combo()
                return
                
            config = configparser.ConfigParser()
            config.read(self.config_file, encoding='utf-8')
            
            # 加载设置
            if 'SETTINGS' in config:
                settings = config['SETTINGS']
                remember = settings.getboolean('remember_password', False)
                self.remember_password.set(remember)
                last_profile = settings.get('last_profile', '')
            else:
                last_profile = ''
            
            # 加载所有用户配置
            self.profiles = {}
            for section_name in config.sections():
                if section_name.startswith('PROFILE_'):
                    profile_name = section_name[8:]  # 移除 'PROFILE_' 前缀
                    self.profiles[profile_name] = dict(config[section_name])
            
            # 更新配置下拉框
            self.update_profile_combo()
            
            # 如果有最后选择的配置，则加载它
            if last_profile and last_profile in self.profiles:
                self.selected_profile.set(last_profile)
                self.load_profile(last_profile)
                        
        except Exception as e:
            print(f"加载配置失败: {e}")
    
    def on_remember_password_changed(self):
        """记住密码选项改变时的回调"""
        if not self.remember_password.get():
            # 如果取消记住密码，立即保存配置（清除密码）
            self.save_config()
        else:
            # 如果勾选记住密码，并且当前有密码，立即保存
            if self.password.get():
                self.save_config()
    
    def on_password_changed(self, *args):
        """密码字段变化时的回调"""
        # 如果已勾选记住密码，当密码变化时自动保存当前配置
        if self.remember_password.get() and self.selected_profile.get() and self.selected_profile.get() != "新建配置...":
            # 延迟保存，避免频繁保存
            if hasattr(self, 'password_save_timer'):
                self.root.after_cancel(self.password_save_timer)
            self.password_save_timer = self.root.after(2000, self.auto_save_current_profile)  # 2秒后保存
    
    def auto_save_current_profile(self):
        """自动保存当前配置"""
        current_profile = self.selected_profile.get()
        if current_profile and current_profile != "新建配置..." and current_profile in self.profiles:
            # 静默保存，不显示提示
            profile_data = {
                'nas_url': self.nas_url.get(),
                'username': self.username.get(),
                'password': ''
            }
            
            # 如果记住密码，则加密保存
            if self.remember_password.get():
                password_text = self.password.get()
                if password_text:
                    encrypted_password = self.encrypt_password(password_text)
                    if encrypted_password:
                        profile_data['password'] = encrypted_password
            
            # 更新配置
            self.profiles[current_profile] = profile_data
            
            # 保存到文件
            self.save_config()
    

    
    def update_profile_combo(self):
        """更新配置下拉框"""
        profile_names = list(self.profiles.keys())
        profile_names.append("新建配置...")
        self.profile_combo['values'] = profile_names
        
        if not profile_names or len(profile_names) == 1:  # 只有"新建配置..."
            self.selected_profile.set("")
    
    def on_profile_selected(self, event=None):
        """配置选择改变时的回调"""
        selected = self.selected_profile.get()
        if selected == "新建配置...":
            self.create_new_profile()
        elif selected in self.profiles:
            self.load_profile(selected)
    
    def load_profile(self, profile_name):
        """加载指定的配置"""
        if profile_name not in self.profiles:
            print(f"配置 '{profile_name}' 不存在于 profiles 中")
            return
            
        profile = self.profiles[profile_name]
        
        # 设置基本信息
        self.nas_url.set(profile.get('nas_url', ''))
        self.username.set(profile.get('username', ''))
        
        # 如果记住密码，则解密并设置密码
        if self.remember_password.get():
            encrypted_password = profile.get('password', '')
            if encrypted_password:
                decrypted_password = self.decrypt_password(encrypted_password)
                if decrypted_password:
                    self.password.set(decrypted_password)
                else:
                    self.password.set("")
            else:
                self.password.set("")
        else:
            self.password.set("")
    
    def create_new_profile(self):
        """创建新配置"""
        # 弹出对话框询问配置名称
        profile_name = tk.simpledialog.askstring(
            "新建配置", 
            "请输入配置名称:", 
            parent=self.root
        )
        
        if profile_name and profile_name.strip():
            profile_name = profile_name.strip()
            if profile_name in self.profiles:
                messagebox.showwarning("警告", f"配置 '{profile_name}' 已存在！")
                return
            
            # 清空当前输入
            self.nas_url.set("")
            self.username.set("")
            self.password.set("")
            self.selected_profile.set(profile_name)
            
            # 添加到配置列表
            self.profiles[profile_name] = {
                'nas_url': '',
                'username': '',
                'password': ''
            }
            
            # 更新下拉框
            self.update_profile_combo()
            self.selected_profile.set(profile_name)
    
    def save_current_profile(self):
        """保存当前配置"""
        current_profile = self.selected_profile.get()
        if not current_profile or current_profile == "新建配置...":
            # 如果没有选择配置，创建新的
            self.create_new_profile()
            return
        
        # 获取当前输入的信息
        nas_url = self.nas_url.get().strip()
        username = self.username.get().strip()
        password = self.password.get()
        

        
        # 检查必填信息
        if not nas_url or not username:
            messagebox.showwarning("警告", "请填写完整的NAS地址和用户名！")
            return
        
        # 保存当前输入的信息
        profile_data = {
            'nas_url': nas_url,
            'username': username,
            'password': ''
        }
        
        # 如果记住密码，则加密保存
        if self.remember_password.get() and password:
            encrypted_password = self.encrypt_password(password)
            if encrypted_password:
                profile_data['password'] = encrypted_password
        
        # 更新配置
        self.profiles[current_profile] = profile_data
        
        # 保存到文件
        self.save_config()
        
        messagebox.showinfo("成功", f"配置 '{current_profile}' 已保存！")
    
    def delete_current_profile(self):
        """删除当前配置"""
        current_profile = self.selected_profile.get()
        if not current_profile or current_profile == "新建配置...":
            messagebox.showwarning("提示", "请先选择要删除的配置！")
            return
        
        # 确认删除
        result = messagebox.askyesno(
            "确认删除", 
            f"确定要删除配置 '{current_profile}' 吗？",
            icon='question'
        )
        
        if result:
            # 删除配置
            if current_profile in self.profiles:
                del self.profiles[current_profile]
            
            # 清空当前输入
            self.nas_url.set("")
            self.username.set("")
            self.password.set("")
            self.selected_profile.set("")
            
            # 更新下拉框
            self.update_profile_combo()
            
            # 保存到文件
            self.save_config()
            
            messagebox.showinfo("完成", f"配置 '{current_profile}' 已删除！")
    
    def clear_all_profiles(self):
        """清除所有配置"""
        if not self.profiles:
            messagebox.showinfo("提示", "没有保存的配置！")
            return
        
        # 确认删除
        result = messagebox.askyesno(
            "确认删除", 
            "确定要删除所有保存的配置吗？",
            icon='question'
        )
        
        if result:
            # 删除配置文件
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
            
            # 清空配置
            self.profiles = {}
            
            # 清空当前输入
            self.nas_url.set("")
            self.username.set("")
            self.password.set("")
            self.selected_profile.set("")
            self.remember_password.set(False)
            
            # 更新下拉框
            self.update_profile_combo()
            
            messagebox.showinfo("完成", "所有配置已清除！")
    
    def logout(self):
        """登出"""
        if self.session_id:
            try:
                # 发送登出请求
                logout_url = f"{self.nas_url.get()}/webapi/auth.cgi"
                params = {
                    'api': 'SYNO.API.Auth',
                    'version': '1',
                    'method': 'logout',
                    'session': 'FileStation'
                    # 不传_sid，使用session的cookie
                }
                self.session.get(logout_url, params=params, timeout=5)
            except:
                pass  # 忽略登出错误
                
        # 重置状态
        self.session_id = None
        self.current_path = "/"
        self.last_login_info = None
        
        # 清空缩略图缓存
        if hasattr(self, 'thumbnail_cache'):
            self.thumbnail_cache.clear()
        
        # 更新UI
        self.connection_status.configure(text="未连接", style='Error.TLabel')
        self.login_btn.configure(state='normal')
        self.logout_btn.configure(state='disabled')
        self.upload_btn.configure(state='disabled')
        self.download_btn.configure(state='disabled')
        self.refresh_btn.configure(state='disabled')
        self.preview_btn.configure(state='disabled')
        self.view_combo.configure(state='disabled')
        
        # 清空列表
        self.dir_tree.delete(*self.dir_tree.get_children())
        self.file_list.delete(*self.file_list.get_children())
        self.path_label.configure(text="/")
        
        self.update_status("已断开连接")
        
        # 如果没有选择记住密码，清空密码字段
        if not self.remember_password.get():
            self.password.set("")
        
    def load_shared_folders(self):
        """加载共享文件夹"""
        threading.Thread(target=self._load_shared_folders_thread, daemon=True).start()
        
    def _load_shared_folders_thread(self):
        """加载共享文件夹线程"""
        try:
            self.update_status("正在加载文件夹...")
            
            # 获取共享文件夹列表
            # 获取列表API的路径
            list_api_path = self.api_info.get('SYNO.FileStation.List', {}).get('path', 'entry.cgi')
            url = f"{self.nas_url.get()}/webapi/{list_api_path}"
            params = {
                'api': 'SYNO.FileStation.List',
                'version': '2',
                'method': 'list_share'
                # 不传_sid，使用session的cookie
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if not result.get('success'):
                raise Exception(f"获取共享文件夹失败: {result.get('error', {})}")
                
            shares = result['data']['shares']
            
            # 更新UI
            self.root.after(0, lambda: self._update_directory_tree(shares))
            
        except Exception as e:
            self.root.after(0, lambda: self.update_status(f"加载文件夹失败: {str(e)}"))
            
    def _update_directory_tree(self, shares):
        """更新目录树"""
        # 清空现有项目
        self.dir_tree.delete(*self.dir_tree.get_children())
        
        # 添加根节点
        root_item = self.dir_tree.insert('', 'end', text='/', values=['/'], open=True)
        
        # 添加共享文件夹
        for share in shares:
            share_name = share['name']
            share_path = share['path']
            # 为每个共享文件夹添加一个占位符子节点，以便显示展开箭头
            folder_icon = self.folder_icons.get('folder_closed_tree', '')
            share_item = self.dir_tree.insert(root_item, 'end', text=share_name, values=[share_path], image=folder_icon)
            # 添加一个占位符，让文件夹显示展开箭头
            self.dir_tree.insert(share_item, 'end', text='<loading...>', values=[''])
            
        self.update_status("文件夹加载完成")
        
    def on_directory_select(self, event):
        """目录选择事件"""
        selection = self.dir_tree.selection()
        if not selection:
            return
            
        item = selection[0]
        values = self.dir_tree.item(item, 'values')
        if values and values[0]:  # 确保路径不为空
            self.current_path = values[0]
            self.path_label.configure(text=self.current_path)
            self.load_files(self.current_path)
    
    def on_directory_expand(self, event):
        """目录展开事件"""
        selection = self.dir_tree.selection()
        if not selection:
            return
            
        item = selection[0]
        values = self.dir_tree.item(item, 'values')
        if not values or not values[0]:
            return
            
        # 检查是否已经加载了子目录
        children = self.dir_tree.get_children(item)
        if children and len(children) == 1:
            # 检查是否是占位符
            child_text = self.dir_tree.item(children[0], 'text')
            if child_text == '<loading...>':
                # 删除占位符并加载真实的子目录
                self.dir_tree.delete(children[0])
                self.load_subdirectories(item, values[0])
    
    def load_subdirectories(self, parent_item, path):
        """加载子目录"""
        threading.Thread(target=self._load_subdirectories_thread, args=(parent_item, path), daemon=True).start()
    
    def _load_subdirectories_thread(self, parent_item, path):
        """加载子目录线程"""
        try:
            # 获取列表API的路径
            list_api_path = self.api_info.get('SYNO.FileStation.List', {}).get('path', 'entry.cgi')
            url = f"{self.nas_url.get()}/webapi/{list_api_path}"
            params = {
                'api': 'SYNO.FileStation.List',
                'version': '2',
                'method': 'list',
                'folder_path': path
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if not result.get('success'):
                return
                
            files = result['data']['files']
            
            # 只添加文件夹到目录树
            directories = [f for f in files if f['isdir']]
            
            # 更新UI
            self.root.after(0, lambda: self._add_directories_to_tree(parent_item, path, directories))
            
        except Exception as e:
            print(f"加载子目录失败: {e}")
    
    def _add_directories_to_tree(self, parent_item, parent_path, directories):
        """添加目录到树形结构"""
        for dir_info in directories:
            dir_name = dir_info['name']
            dir_path = f"{parent_path.rstrip('/')}/{dir_name}"
            
            # 添加目录项，使用文件夹图标
            folder_icon = self.folder_icons.get('folder_closed_tree', '')
            dir_item = self.dir_tree.insert(parent_item, 'end', text=dir_name, values=[dir_path], image=folder_icon)
            # 添加占位符，以便显示展开箭头
            self.dir_tree.insert(dir_item, 'end', text='<loading...>', values=[''])
    
    def update_tree_selection(self, path):
        """更新目录树的选择状态"""
        # 递归查找并选择对应路径的节点
        def find_and_select_item(item, target_path):
            item_values = self.dir_tree.item(item, 'values')
            if item_values and item_values[0] == target_path:
                self.dir_tree.selection_set(item)
                self.dir_tree.see(item)
                return True
            
            # 递归检查子节点
            for child in self.dir_tree.get_children(item):
                if find_and_select_item(child, target_path):
                    return True
            return False
        
        # 从根节点开始查找
        for root_item in self.dir_tree.get_children():
            if find_and_select_item(root_item, path):
                break
    
    def on_view_mode_changed(self, event=None):
        """视图模式改变事件"""
        mode = self.view_mode.get()
        print(f"切换到视图模式: {mode}")
        # 重新配置文件列表显示模式
        self.configure_file_list_view(mode)
        # 重新刷新文件列表以应用新的显示模式
        if hasattr(self, 'current_path') and self.current_path and self.current_path != "/":
            self.refresh_file_list()
    
    def configure_file_list_view(self, mode):
        """配置文件列表的显示模式"""
        if mode == "列表视图":
            # 标准列表视图 - 显示所有列
            self.file_list.configure(show='tree headings')
            self.file_list.column('#0', width=0, stretch=False)  # 隐藏树形列
            self.file_list.column('name', width=300)
            self.file_list.column('type', width=120)
            self.file_list.column('size', width=100)
            self.file_list.column('modified', width=150)
            
        elif mode == "平铺视图":
            # 平铺视图 - 显示树形列和部分信息列
            self.file_list.configure(show='tree headings')
            self.file_list.column('#0', width=250, stretch=True)  # 显示树形列，增加宽度
            self.file_list.column('name', width=0, stretch=False)  # 隐藏名称列
            self.file_list.column('type', width=120)
            self.file_list.column('size', width=100)
            self.file_list.column('modified', width=150)
            
        else:  # 图标视图（小图标、中图标、大图标）
            # 图标视图 - 主要显示树形列，根据图标大小调整列宽
            self.file_list.configure(show='tree')
            if mode == "小图标":
                self.file_list.column('#0', width=180, stretch=True)
            elif mode == "中图标":
                self.file_list.column('#0', width=280, stretch=True)  # 增大列宽以容纳64x64缩略图
            elif mode == "大图标":
                self.file_list.column('#0', width=400, stretch=True)  # 增大列宽以容纳96x96缩略图
            
            # 隐藏其他列，只显示树形列（图标+文件名）
            self.file_list.column('name', width=0, stretch=False)
            self.file_list.column('type', width=0, stretch=False)
            self.file_list.column('size', width=0, stretch=False)
            self.file_list.column('modified', width=0, stretch=False)
            
            # 设置树形列的标题为空，避免显示"文件名"标题
            self.file_list.heading('#0', text='')
            
    def load_files(self, path):
        """加载指定路径的文件"""
        threading.Thread(target=self._load_files_thread, args=(path,), daemon=True).start()
        
    def _load_files_thread(self, path):
        """加载文件线程"""
        try:
            self.update_status("正在加载文件...")
            
            # 获取列表API的路径
            list_api_path = self.api_info.get('SYNO.FileStation.List', {}).get('path', 'entry.cgi')
            url = f"{self.nas_url.get()}/webapi/{list_api_path}"
            # 获取文件列表和附加信息
            params = {
                'api': 'SYNO.FileStation.List',
                'version': '2',
                'method': 'list',
                'folder_path': path,
                'additional': '["size","time"]'  # 尝试JSON数组格式
                # 不传_sid，使用session的cookie
            }
            
                                    
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            if not result.get('success'):
                error_info = result.get('error', {})
                # 如果additional参数有问题，尝试不使用additional参数
                if error_info.get('code') == 400:  # 可能是参数错误
                    params_simple = {
                        'api': 'SYNO.FileStation.List',
                        'version': '2',
                        'method': 'list',
                        'folder_path': path
                    }
                    response = self.session.get(url, params=params_simple, timeout=10)
                    result = response.json()
                    
                if not result.get('success'):
                    raise Exception(f"获取文件列表失败: {result.get('error', {})}")
                    
            files = result['data']['files']
            
            # 更新UI
            self.root.after(0, lambda: self._update_file_list(files))
            
        except Exception as e:
            self.root.after(0, lambda: self.update_status(f"加载文件失败: {str(e)}"))
            
    def _update_file_list(self, files):
        """更新文件列表"""
        # 清空现有项目
        self.file_list.delete(*self.file_list.get_children())
        
        # 根据视图模式调整显示
        view_mode = self.view_mode.get()
        
        for i, file_info in enumerate(files):
            name = file_info['name']
            is_dir = file_info['isdir']
            file_type = self.get_file_type_display(name, is_dir)
            
            # 处理大小
            size = ""
            if not is_dir and 'additional' in file_info and 'size' in file_info['additional']:
                size_bytes = int(file_info['additional']['size'])
                size = self.format_file_size(size_bytes)
                
            # 处理修改时间
            modified = ""
            if 'additional' in file_info and 'time' in file_info['additional']:
                mtime = file_info['additional']['time']['mtime']
                modified = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            # 选择合适的图标
            icon = ""
            if is_dir and hasattr(self, 'folder_icons'):
                if view_mode == "列表视图":
                    icon = self.folder_icons.get('folder_closed_list', '')
                elif view_mode == "平铺视图":
                    icon = self.folder_icons.get('folder_closed_tile', '')
                elif view_mode == "小图标":
                    icon = self.folder_icons.get('folder_closed_small', '')
                elif view_mode == "中图标":
                    icon = self.folder_icons.get('folder_closed_medium', '')
                elif view_mode == "大图标":
                    icon = self.folder_icons.get('folder_closed_large', '')
                else:
                    icon = self.folder_icons.get('folder_closed_list', '')
            elif not is_dir and self.is_image_file(name) and view_mode in ["中图标", "大图标"]:
                # 为图片文件生成缩略图
                icon = self.get_image_thumbnail(name, view_mode)
                
            # 插入文件项目，根据视图模式决定是否显示图标
            if view_mode == "列表视图":
                # 标准列表视图
                item_id = self.file_list.insert('', 'end', values=(name, file_type, size, modified), image=icon)
            elif view_mode == "平铺视图":
                # 平铺视图 - 显示图标和名称，其他信息在列中显示
                item_id = self.file_list.insert('', 'end', text=name, values=(name, file_type, size, modified), image=icon)
            else:  # 图标视图
                # 图标视图 - 主要显示名称和图标，确保文件名正确显示
                item_id = self.file_list.insert('', 'end', text=name, values=(name, file_type, size, modified), image=icon)
                # 设置项目的标签，确保文件名显示在图标下方
                self.file_list.set(item_id, '#0', name)
            
        self.update_status(f"已加载 {len(files)} 个项目 - {view_mode}")
        
    def on_file_double_click(self, event):
        """文件双击事件"""
        selection = self.file_list.selection()
        if not selection:
            return
            
        item = selection[0]
        values = self.file_list.item(item, 'values')
        if not values:
            return
            
        filename = values[0]
        file_type = values[1]
        
        # 如果是文件夹，则进入该文件夹
        if file_type == "[文件夹]" or "文件夹" in file_type:
            new_path = f"{self.current_path.rstrip('/')}/{filename}"
            self.current_path = new_path
            self.path_label.configure(text=self.current_path)
            self.load_files(self.current_path)
            # 同时更新左侧目录树的选择
            self.update_tree_selection(self.current_path)
        # 如果是图片文件，则预览
        elif self.is_image_file(filename):
            self.preview_image(filename)
        # 如果是视频文件，则预览
        elif self.is_video_file(filename):
            self.preview_video(filename)
            
    def refresh_file_list(self):
        """刷新文件列表"""
        self.load_files(self.current_path)
        
    def on_file_right_click(self, event):
        """文件右键点击事件"""
        # 选择右键点击的项目
        item = self.file_list.identify('item', event.x, event.y)
        if item:
            self.file_list.selection_set(item)
            # 检查是否是文件（不是文件夹）
            values = self.file_list.item(item, 'values')
            if values and values[1] != "[文件夹]" and "文件夹" not in values[1]:  # 只有文件才能操作
                # 动态更新右键菜单
                self.update_context_menu(values[0])
                self.context_menu.post(event.x_root, event.y_root)
    
    def update_context_menu(self, filename):
        """更新右键菜单选项"""
        # 清空现有菜单项
        self.context_menu.delete(0, tk.END)
        
        # 根据文件类型添加菜单项
        if self.is_image_file(filename):
            self.context_menu.add_command(label="预览图片", command=self.preview_selected_file)
        elif self.is_video_file(filename):
            self.context_menu.add_command(label="预览视频", command=self.preview_selected_file)
        
        self.context_menu.add_command(label="下载", command=self.download_selected_file)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="刷新", command=self.refresh_file_list)
        self.context_menu.add_command(label="清理缩略图缓存", command=self.clear_thumbnail_cache)
                
    def preview_selected_file(self):
        """预览按钮点击事件"""
        selection = self.file_list.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要预览的文件")
            return
            
        item = selection[0]
        values = self.file_list.item(item, 'values')
        if not values:
            return
            
        filename = values[0]
        file_type = values[1]
        
        # 检查是否为文件夹
        if file_type == "[文件夹]" or "文件夹" in file_type:
            messagebox.showwarning("提示", "只能预览文件，不能预览文件夹")
            return
        
        # 检查文件类型并预览
        if self.is_image_file(filename):
            self.preview_image(filename)
        elif self.is_video_file(filename):
            self.preview_video(filename)
        else:
            messagebox.showwarning("提示", "只能预览图片和视频文件")
    
    def download_file(self):
        """下载按钮点击事件"""
        selection = self.file_list.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要下载的文件")
            return
            
        item = selection[0]
        values = self.file_list.item(item, 'values')
        if not values or values[1] == "[文件夹]" or "文件夹" in values[1]:
            messagebox.showwarning("提示", "只能下载文件，不能下载文件夹")
            return
            
        self.download_selected_file()
        
    def download_selected_file(self):
        """下载选中的文件"""
        if not self.session_id:
            messagebox.showerror("错误", "请先登录")
            return
            
        # 验证会话是否有效
        if not self.verify_session():
            messagebox.showerror("错误", "会话已过期，请重新登录")
            self.logout()
            return
            
        selection = self.file_list.selection()
        if not selection:
            return
            
        item = selection[0]
        values = self.file_list.item(item, 'values')
        if not values or values[1] == "[文件夹]" or "文件夹" in values[1]:
            messagebox.showwarning("提示", "只能下载文件")
            return
            
        filename = values[0]
        # 构建正确的文件路径
        if self.current_path == "/":
            file_path = f"/{filename}"
        else:
            file_path = f"{self.current_path.rstrip('/')}/{filename}"
        
        # 选择保存位置
        save_path = filedialog.asksaveasfilename(
            title="保存文件",
            initialfile=filename,
            filetypes=[("所有文件", "*.*")]
        )
        
        if not save_path:
            return
            
        # 在新线程中下载
        threading.Thread(target=self._download_file_thread, args=(file_path, save_path, filename), daemon=True).start()
        
    def upload_file(self):
        """上传文件"""
        if not self.session_id:
            messagebox.showerror("错误", "请先登录")
            return
            
        # 验证会话是否有效
        if not self.verify_session():
            messagebox.showerror("错误", "会话已过期，请重新登录")
            self.logout()
            return
            
        # 选择文件
        file_path = filedialog.askopenfilename(
            title="选择要上传的文件",
            filetypes=[("所有文件", "*.*")]
        )
        
        if not file_path:
            return
            
        # 在新线程中上传
        threading.Thread(target=self._upload_file_thread, args=(file_path,), daemon=True).start()
        
    def _upload_file_thread(self, file_path):
        """上传文件线程"""
        try:
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            self.root.after(0, lambda: self.show_progress(True))
            self.update_status(f"正在上传 {filename}...")
            
            # 确保路径正确，如果是根目录，显示错误
            if self.current_path == "/":
                raise Exception("请先选择一个共享文件夹，不能直接上传到根目录")
            
            # 上传前再次验证会话并刷新SID
            if not self.refresh_session_if_needed():
                raise Exception("会话验证失败，请重新登录")
            
            # 准备上传参数
            # 获取上传API的路径
            upload_api_path = self.api_info.get('SYNO.FileStation.Upload', {}).get('path', 'entry.cgi')
            url = f"{self.nas_url.get()}/webapi/{upload_api_path}"
                
            # 使用API信息中的最大版本号
            api_version = self.api_info.get('SYNO.FileStation.Upload', {}).get('maxVersion', 2)
            
            data = {
                'api': 'SYNO.FileStation.Upload',
                'version': str(api_version),
                'method': 'upload',
                'path': self.current_path,
                'create_parents': 'false',
                'overwrite': 'true'
                # 不传_sid，使用session的cookie
            }
            
            # 打开文件准备上传
            with open(file_path, 'rb') as f:
                files_data = {'file': (filename, f, 'application/octet-stream')}
                
                response = self.session.post(url, data=data, files=files_data, timeout=300)
                response.raise_for_status()
                
            result = response.json()
            if not result.get('success'):
                error_info = result.get('error', {})
                error_code = error_info.get('code', 'unknown')
                error_messages = {
                    119: "会话未找到，请重新登录",
                    407: "操作不被允许，请检查文件夹权限",
                    1800: "上传数据不完整",
                    1801: "上传超时",
                    1802: "文件名信息缺失",
                    1803: "上传被取消",
                    1804: "文件过大",
                    1805: "文件已存在且无法覆盖"
                }
                error_msg = error_messages.get(error_code, f"上传失败，错误代码: {error_code}")
                if error_code == 119:
                    # SID过期，尝试自动重新登录
                    self.session_id = None
                    if self.last_login_info:
                        self.root.after(0, self.try_auto_login)  # 立即尝试重新登录
                        error_msg = "会话已过期，正在尝试自动重新登录...\n请稍后再试上传操作"
                    else:
                        error_msg += "\n\n请点击'断开'按钮后重新登录"
                raise Exception(error_msg)
                
            # 上传成功
            self.root.after(0, lambda: self._on_upload_success(filename))
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self._on_upload_error(error_msg))
            
    def _on_upload_success(self, filename):
        """上传成功回调"""
        self.show_progress(False)
        self.update_status(f"文件 {filename} 上传成功")
        messagebox.showinfo("上传成功", f"文件 {filename} 已成功上传")
        
        # 刷新文件列表
        self.refresh_file_list()
        
    def _on_upload_error(self, error_msg):
        """上传失败回调"""
        self.show_progress(False)
        self.update_status("上传失败")
        messagebox.showerror("上传失败", error_msg)
        
    def _download_file_thread(self, file_path, save_path, filename):
        """下载文件线程"""
        try:
            self.root.after(0, lambda: self.show_progress(True))
            self.update_status(f"正在下载 {filename}...")
            
            # 下载前验证并刷新会话
            if not self.refresh_session_if_needed():
                raise Exception("会话验证失败，请重新登录")
            
            # 构建下载URL
            # 获取下载API的路径
            download_api_path = self.api_info.get('SYNO.FileStation.Download', {}).get('path', 'entry.cgi')
            url = f"{self.nas_url.get()}/webapi/{download_api_path}"
            params = {
                'api': 'SYNO.FileStation.Download',
                'version': '2',
                'method': 'download',
                'path': f'["{file_path}"]',
                'mode': 'download'
                # 不传_sid，使用session的cookie
            }
            
            # 发送下载请求
            response = self.session.get(url, params=params, timeout=300, stream=True)
            response.raise_for_status()
            
            # 检查响应类型
            content_type = response.headers.get('content-type', '')
            if 'application/json' in content_type:
                # 如果返回JSON，说明出错了
                result = response.json()
                if not result.get('success'):
                    error_code = result.get('error', {}).get('code', 'unknown')
                    raise Exception(f"下载失败，错误代码: {error_code}")
            
            # 获取文件大小
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            # 写入文件
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # 更新进度
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            self.root.after(0, lambda p=progress: self.progress_var.set(p))
                            # 更新状态栏显示百分比
                            self.root.after(0, lambda p=progress, ds=downloaded_size, ts=total_size: 
                                self.update_status(f"正在下载 {filename}... {p:.1f}% ({self.format_file_size(ds)}/{self.format_file_size(ts)})"))
                        else:
                            # 如果无法获取文件大小，显示已下载的数据量
                            self.root.after(0, lambda ds=downloaded_size: 
                                self.update_status(f"正在下载 {filename}... {self.format_file_size(ds)}"))
                            
            # 下载成功
            self.root.after(0, lambda: self._on_download_success(filename, save_path))
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self._on_download_error(error_msg))
            
    def _on_download_success(self, filename, save_path):
        """下载成功回调"""
        self.show_progress(False)
        self.progress_var.set(0)  # 重置进度条
        self.update_status(f"文件 {filename} 下载完成")
        messagebox.showinfo("下载成功", f"文件已保存到:\n{save_path}")
        
    def _on_download_error(self, error_msg):
        """下载失败回调"""
        self.show_progress(False)
        self.progress_var.set(0)  # 重置进度条
        self.update_status("下载失败")
        messagebox.showerror("下载失败", error_msg)
        
    def format_file_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def get_file_type_display(self, filename, is_dir=False):
        """根据文件名获取友好的文件类型显示"""
        if is_dir:
            return "[文件夹]"
        
        # 获取文件扩展名
        ext = os.path.splitext(filename)[1].lower()
        
        # 文件类型映射 - 使用简单的文本标识避免emoji兼容性问题
        file_types = {
            # 图片
            '.png': '[图片] PNG',
            '.jpg': '[图片] JPG', 
            '.jpeg': '[图片] JPEG',
            '.gif': '[图片] GIF',
            '.bmp': '[图片] BMP',
            '.svg': '[图片] SVG',
            '.webp': '[图片] WebP',
            '.ico': '[图片] ICO',
            
            # 文档
            '.txt': '[文本] TXT',
            '.doc': '[Word] DOC',
            '.docx': '[Word] DOCX',
            '.pdf': '[PDF] PDF',
            '.xls': '[Excel] XLS',
            '.xlsx': '[Excel] XLSX',
            '.ppt': '[PPT] PPT',
            '.pptx': '[PPT] PPTX',
            '.rtf': '[文本] RTF',
            '.odt': '[文档] ODT',
            '.ods': '[表格] ODS',
            '.odp': '[演示] ODP',
            
            # 代码和脚本
            '.py': '[代码] Python',
            '.js': '[代码] JavaScript',
            '.html': '[网页] HTML',
            '.htm': '[网页] HTM',
            '.css': '[样式] CSS',
            '.php': '[代码] PHP',
            '.java': '[代码] Java',
            '.cpp': '[代码] C++',
            '.c': '[代码] C',
            '.cs': '[代码] C#',
            '.xml': '[数据] XML',
            '.json': '[数据] JSON',
            '.sql': '[数据库] SQL',
            '.sh': '[脚本] Shell',
            '.bat': '[脚本] BAT',
            '.ps1': '[脚本] PowerShell',
            
            # 压缩包
            '.zip': '[压缩] ZIP',
            '.rar': '[压缩] RAR',
            '.7z': '[压缩] 7Z',
            '.tar': '[压缩] TAR',
            '.gz': '[压缩] GZ',
            '.bz2': '[压缩] BZ2',
            '.xz': '[压缩] XZ',
            
            # 音频
            '.mp3': '[音频] MP3',
            '.wav': '[音频] WAV',
            '.flac': '[音频] FLAC',
            '.aac': '[音频] AAC',
            '.ogg': '[音频] OGG',
            '.wma': '[音频] WMA',
            
            # 视频
            '.mp4': '[视频] MP4',
            '.avi': '[视频] AVI',
            '.mkv': '[视频] MKV',
            '.mov': '[视频] MOV',
            '.wmv': '[视频] WMV',
            '.flv': '[视频] FLV',
            '.webm': '[视频] WebM',
            '.m4v': '[视频] M4V',
            
            # 可执行文件
            '.exe': '[程序] EXE',
            '.msi': '[安装] MSI',
            '.deb': '[安装] DEB',
            '.rpm': '[安装] RPM',
            '.dmg': '[安装] DMG',
            '.app': '[应用] APP',
            
            # 数据库
            '.db': '[数据库] DB',
            '.sqlite': '[数据库] SQLite',
            '.mdb': '[数据库] MDB',
            
            # 配置文件
            '.ini': '[配置] INI',
            '.conf': '[配置] CONF',
            '.cfg': '[配置] CFG',
            '.yaml': '[配置] YAML',
            '.yml': '[配置] YML',
            '.toml': '[配置] TOML',
            
            # 字体
            '.ttf': '[字体] TTF',
            '.otf': '[字体] OTF',
            '.woff': '[字体] WOFF',
            '.woff2': '[字体] WOFF2',
            
            # 其他
            '.iso': '[镜像] ISO',
            '.log': '[日志] LOG',
            '.md': '[文档] Markdown',
            '.csv': '[数据] CSV',
        }
        
        return file_types.get(ext, f'[文件] {ext[1:].upper() if ext else "未知"}')
    
    def is_image_file(self, filename):
        """检查是否为图片文件"""
        if not filename:
            return False
        
        ext = os.path.splitext(filename)[1].lower()
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp', '.ico', '.tiff', '.tif'}
        return ext in image_extensions
    
    def is_video_file(self, filename):
        """检查是否为视频文件"""
        if not filename:
            return False
        
        ext = os.path.splitext(filename)[1].lower()
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.rmvb', '.mpg', '.mpeg'}
        return ext in video_extensions
    
    def get_image_thumbnail(self, filename, view_mode):
        """获取图片缩略图"""
        if not hasattr(self, 'thumbnail_cache'):
            self.thumbnail_cache = {}
        
        # 生成缓存键
        cache_key = f"{filename}_{view_mode}"
        
        # 检查缓存
        if cache_key in self.thumbnail_cache:
            return self.thumbnail_cache[cache_key]
        
        # 如果没有缓存，返回空字符串（异步加载缩略图）
        self.load_image_thumbnail_async(filename, view_mode, cache_key)
        return ""
    
    def load_image_thumbnail_async(self, filename, view_mode, cache_key):
        """异步加载图片缩略图"""
        # 在新线程中加载缩略图
        threading.Thread(target=self._load_thumbnail_thread, 
                        args=(filename, view_mode, cache_key), daemon=True).start()
    
    def _load_thumbnail_thread(self, filename, view_mode, cache_key):
        """缩略图加载线程"""
        try:
            # 构建文件路径
            file_path = f"{self.current_path.rstrip('/')}/{filename}"
            
            # 获取下载API的路径
            download_api_path = self.api_info.get('SYNO.FileStation.Download', {}).get('path', 'entry.cgi')
            url = f"{self.nas_url.get()}/webapi/{download_api_path}"
            
            # 下载参数
            params = {
                'api': 'SYNO.FileStation.Download',
                'version': '2',
                'method': 'download',
                'path': file_path
            }
            
            # 下载图片到临时文件
            response = self.session.get(url, params=params, stream=True, timeout=10)
            response.raise_for_status()
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
                temp_path = temp_file.name
                
                # 写入图片数据
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
            
            # 生成缩略图
            thumbnail = self.create_thumbnail(temp_path, view_mode)
            
            # 删除临时文件
            try:
                os.unlink(temp_path)
            except:
                pass
            
            # 在主线程中更新缓存和UI
            if thumbnail:
                self.root.after(0, lambda: self._update_thumbnail_cache(cache_key, thumbnail, filename))
            
        except Exception as e:
            print(f"⚠ 加载缩略图失败 {filename}: {str(e)}")
    
    def create_thumbnail(self, image_path, view_mode):
        """创建缩略图"""
        try:
            from PIL import Image, ImageTk
            
            # 打开图片
            image = Image.open(image_path)
            
            # 根据视图模式确定缩略图大小
            if view_mode == "中图标":
                thumbnail_size = (64, 64)  # 增大到64x64
            elif view_mode == "大图标":
                thumbnail_size = (96, 96)  # 增大到96x96
            else:
                thumbnail_size = (48, 48)
            
            # 计算缩放比例，保持宽高比
            img_width, img_height = image.size
            scale_x = (thumbnail_size[0] - 8) / img_width  # 留出更多边框空间
            scale_y = (thumbnail_size[1] - 8) / img_height
            scale = min(scale_x, scale_y)
            
            # 计算新的尺寸
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            # 缩放图片
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 创建背景（白色背景，更清晰）
            background = Image.new('RGBA', thumbnail_size, (255, 255, 255, 255))
            
            # 计算居中位置
            x = (thumbnail_size[0] - new_width) // 2
            y = (thumbnail_size[1] - new_height) // 2
            
            # 粘贴图片到背景上
            background.paste(image, (x, y))
            
            # 转换为PhotoImage
            thumbnail = ImageTk.PhotoImage(background)
            
            return thumbnail
            
        except Exception as e:
            print(f"⚠ 创建缩略图失败: {str(e)}")
            return None
    
    def _update_thumbnail_cache(self, cache_key, thumbnail, filename):
        """更新缩略图缓存并刷新UI"""
        # 更新缓存
        self.thumbnail_cache[cache_key] = thumbnail
        
        # 刷新文件列表以显示缩略图
        if hasattr(self, 'current_path') and self.current_path:
            self.refresh_file_list()
        
        print(f"✓ 缩略图加载完成: {filename}")
    
    def clear_thumbnail_cache(self):
        """清理缩略图缓存"""
        if hasattr(self, 'thumbnail_cache'):
            self.thumbnail_cache.clear()
            print("✓ 缩略图缓存已清理")
    
    def preview_image(self, filename):
        """预览图片文件"""
        if not self.session_id:
            messagebox.showerror("错误", "请先登录")
            return
        
        if not self.is_image_file(filename):
            messagebox.showwarning("提示", "只能预览图片文件")
            return
        
        # 构建文件路径
        file_path = f"{self.current_path.rstrip('/')}/{filename}"
        
        # 在新线程中下载并预览图片
        threading.Thread(target=self._preview_image_thread, args=(file_path, filename), daemon=True).start()
    
    def preview_video(self, filename):
        """预览视频文件"""
        if not self.session_id:
            messagebox.showerror("错误", "请先登录")
            return
        
        if not self.is_video_file(filename):
            messagebox.showwarning("提示", "只能预览视频文件")
            return
        
        # 构建文件路径
        file_path = f"{self.current_path.rstrip('/')}/{filename}"
        
        # 在新线程中下载并预览视频
        threading.Thread(target=self._preview_video_thread, args=(file_path, filename), daemon=True).start()
    
    def _preview_image_thread(self, file_path, filename):
        """图片预览线程"""
        try:
            self.update_status(f"正在加载图片预览: {filename}...")
            
            # 获取下载API的路径
            download_api_path = self.api_info.get('SYNO.FileStation.Download', {}).get('path', 'entry.cgi')
            url = f"{self.nas_url.get()}/webapi/{download_api_path}"
            
            # 下载参数
            params = {
                'api': 'SYNO.FileStation.Download',
                'version': '2',
                'method': 'download',
                'path': file_path
                # 不传_sid，使用session的cookie
            }
            
            # 下载图片到临时文件
            response = self.session.get(url, params=params, stream=True, timeout=30)
            response.raise_for_status()
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
                temp_path = temp_file.name
                
                # 写入图片数据
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
            
            # 在主线程中打开预览窗口
            self.root.after(0, lambda: self._open_preview_window(temp_path, filename))
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self._on_preview_error(error_msg))
    
    def _preview_video_thread(self, file_path, filename):
        """视频预览线程"""
        try:
            self.update_status(f"正在加载视频预览: {filename}...")
            
            # 获取下载API的路径
            download_api_path = self.api_info.get('SYNO.FileStation.Download', {}).get('path', 'entry.cgi')
            url = f"{self.nas_url.get()}/webapi/{download_api_path}"
            
            # 下载参数
            params = {
                'api': 'SYNO.FileStation.Download',
                'version': '2',
                'method': 'download',
                'path': file_path
                # 不传_sid，使用session的cookie
            }
            
            # 下载视频到临时文件
            response = self.session.get(url, params=params, stream=True, timeout=60)  # 增加超时时间
            response.raise_for_status()
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
                temp_path = temp_file.name
                
                # 写入视频数据
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
            
            # 在主线程中打开预览窗口
            self.root.after(0, lambda: self._open_video_preview_window(temp_path, filename))
            
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda: self._on_video_preview_error(error_msg))
    
    def _open_preview_window(self, temp_path, filename):
        """打开预览窗口"""
        try:
            # 创建预览窗口
            preview_window = ImagePreviewWindow(self.root, temp_path, filename)
            
            # 保存临时文件路径，以便窗口关闭时删除
            preview_window.original_image_path = temp_path
            
            # 绑定窗口关闭事件，删除临时文件
            def on_preview_close():
                try:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                except:
                    pass
                preview_window.window.destroy()
            
            preview_window.window.protocol("WM_DELETE_WINDOW", on_preview_close)
            
            self.update_status(f"图片预览已打开: {filename}")
            
        except Exception as e:
            self.update_status(f"打开预览窗口失败: {str(e)}")
            messagebox.showerror("预览失败", f"无法打开图片预览:\n{str(e)}")
    
    def _open_video_preview_window(self, temp_path, filename):
        """打开视频预览窗口"""
        try:
            # 创建视频预览窗口
            preview_window = VideoPreviewWindow(self.root, temp_path, filename)
            
            # 保存临时文件路径，以便窗口关闭时删除
            preview_window.original_video_path = temp_path
            
            # 绑定窗口关闭事件，删除临时文件
            def on_preview_close():
                try:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                except:
                    pass
                preview_window.window.destroy()
            
            preview_window.window.protocol("WM_DELETE_WINDOW", on_preview_close)
            
            self.update_status(f"视频预览已打开: {filename}")
            
        except Exception as e:
            self.update_status(f"打开视频预览窗口失败: {str(e)}")
            messagebox.showerror("预览失败", f"无法打开视频预览:\n{str(e)}")
    
    def _on_preview_error(self, error_msg):
        """预览错误处理"""
        self.update_status("图片预览失败")
        messagebox.showerror("预览失败", f"无法预览图片:\n{error_msg}")
    
    def _on_video_preview_error(self, error_msg):
        """视频预览错误处理"""
        self.update_status("视频预览失败")
        messagebox.showerror("预览失败", f"无法预览视频:\n{error_msg}")
        
    def update_status(self, message):
        """更新状态"""
        def _update():
            self.status_label.configure(text=message)
            
        if threading.current_thread() == threading.main_thread():
            _update()
        else:
            self.root.after(0, _update)
            
    def run(self):
        """运行应用程序"""
        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 启动主循环
        self.root.mainloop()
        
    def on_closing(self):
        """窗口关闭事件"""
        # 保存当前配置
        self.save_config()
        
        # 如果已登录，先登出
        if self.session_id:
            self.logout()
            
        self.root.destroy()


if __name__ == "__main__":
    app = SynologyNASManager()
    app.run() 
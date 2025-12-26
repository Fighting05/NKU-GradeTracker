# nku_grades_gui.py
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import json
import os
from datetime import datetime, timedelta
import webbrowser
import time
import sys

# 导入你的核心功能类
from nku_grades import WebVPNGradeChecker, GradeMonitor

# 设置主题
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class EnhancedGradeMonitor(threading.Thread):
    """增强的GUI成绩监控线程"""
    
    def __init__(self, username, password, token, semester_id, interval, log_callback, status_callback):
        super().__init__()
        self.username = username
        self.password = password
        self.token = token
        self.semester_id = semester_id
        self.interval = interval
        self.log_callback = log_callback
        self.status_callback = status_callback
        
        self.running = False
        self.daemon = True
        
        # 创建监控实例，传入日志回调
        from nku_grades import GradeMonitor
        self.monitor = GradeMonitor(username, password, token, log_callback=self.log)
    
    def log(self, message):
        """日志回调"""
        if self.log_callback:
            self.log_callback(message)
    
    def update_status(self, message, color="white"):
        """状态更新回调"""
        if self.status_callback:
            self.status_callback(message, color)
    
    def start_monitoring(self):
        """开始监控"""
        self.running = True
        self.start()
    
    def stop_monitoring(self):
        """停止监控"""
        self.running = False
    
    def run(self):
        """监控主循环"""
        self.log(f"🚀 开始监控学期 {self.semester_id}，每 {self.interval} 分钟检查一次")
        self.log(f"📱 推送Token: {'已配置' if self.token else '未配置'}")
        
        check_count = 0
        
        while self.running:
            try:
                check_count += 1
                self.log(f"\n{'='*60}")
                self.log(f"🔍 第 {check_count} 次检查 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                self.log(f"{'='*60}")
                
                self.update_status(f"🔄 正在进行第 {check_count} 次检查...", "yellow")
                
                # 登录检查
                if not self.monitor.login():
                    self.log("❌ 登录失败，等待下次检查")
                    self.update_status("❌ 登录失败", "red")
                elif not self.monitor.access_eamis():
                    self.log("❌ 访问教务系统失败，等待下次检查")
                    self.update_status("❌ 访问教务系统失败", "red")
                else:
                    # 检查成绩
                    has_changes = self.monitor.check_grades(self.semester_id)
                    
                    if has_changes:
                        self.log("🎊 本次检查发现成绩变化！")
                        self.update_status("🎉 发现成绩变化！", "green")
                    else:
                        self.log("😴 本次检查无变化")
                        self.update_status("✅ 监控正常，无变化", "green")
                
                if not self.running:
                    break
                
                # 计算下次检查时间
                next_check_time = datetime.now() + timedelta(minutes=self.interval)
                self.log(f"⏰ 下次检查时间: {next_check_time.strftime('%H:%M:%S')}")
                self.log(f"💤 等待 {self.interval} 分钟...")
                
                # 等待指定时间，期间可以被中断
                for i in range(self.interval):
                    if not self.running:
                        break
                    
                    remaining = self.interval - i
                    if remaining % 5 == 0 and remaining > 0:  # 每5分钟更新一次状态
                        self.update_status(f"⏳ {remaining} 分钟后检查", "blue")
                    
                    time.sleep(60)  # 等待1分钟
                
            except Exception as e:
                self.log(f"❌ 监控过程出错: {e}")
                self.update_status("❌ 监控出错", "red")
                if self.running:
                    self.log("⏱️ 等待1分钟后继续...")
                    time.sleep(60)
        
        self.log("🛑 监控已停止")
        self.update_status("⚪ 监控已停止", "white")

class ModernGradeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # 窗口设置
        self.title("NKU 成绩查询助手")
        self.geometry("1000x750")
        self.resizable(False, False)
        
        # 加载配置
        self.load_config()
        
        # 初始化变量
        self.current_semester_id = "4324"  # 当前选中的学期ID
        self.semester_options = []  # 动态获取的学期选项
        self.account_verified = False  # 账号验证状态
        
        # 创建界面
        self.create_widgets()
        
        # 监控线程
        self.monitor_thread = None
        self.monitoring = False
        
        # 如果配置中有学期数据，则加载
        self.load_semester_data()
        
    def get_browser_executable_path(self):
        """获取浏览器引擎路径"""
        if getattr(sys, 'frozen', False):
            # 运行在打包的exe中
            application_path = sys._MEIPASS
            browser_path = os.path.join(application_path, 'playwright_browsers', 'chromium')
            
            # 查找chromium可执行文件
            if os.path.exists(browser_path):
                for root, dirs, files in os.walk(browser_path):
                    for file in files:
                        if file.startswith('chrome') and (file.endswith('.exe') or 'chrome' in file):
                            return os.path.join(root, file)
        return None
        
    def _bind_mousewheel(self, widget):
        """绑定鼠标滚轮事件，优化滚动体验"""
        def _on_mousewheel(event):
            # 更精细的滚动步长控制
            if hasattr(event, 'delta'):
                # Windows 系统
                scroll_step = -int(event.delta / 40)  # 调整这个数值来改变滚动速度
            else:
                # Linux 系统
                scroll_step = -3 if event.num == 4 else 3
            
            # 使用更丝滑的滚动
            try:
                # 检查是否可以滚动
                current_view = widget._parent_canvas.canvasy(0)
                bbox = widget._parent_canvas.bbox("all")
                if bbox:
                    canvas_height = widget._parent_canvas.winfo_height()
                    content_height = bbox[3] - bbox[1]
                    
                    if content_height > canvas_height:
                        # 使用平滑滚动
                        widget._parent_canvas.yview_scroll(scroll_step, "units")
                        
                        # 可选：添加动画效果（但可能影响性能）
                        # self._smooth_scroll(widget, scroll_step)
            except:
                # 备用滚动方法
                widget._parent_canvas.yview_scroll(scroll_step, "units")
        
        # 绑定鼠标滚轮事件到整个左侧面板
        def bind_to_mousewheel(widget):
            widget.bind("<MouseWheel>", _on_mousewheel, add="+")  # Windows
            widget.bind("<Button-4>", lambda e: _on_mousewheel(type('Event', (), {'num': 4})()), add="+")  # Linux 向上
            widget.bind("<Button-5>", lambda e: _on_mousewheel(type('Event', (), {'num': 5})()), add="+")  # Linux 向下
            
            # 递归绑定所有子控件
            for child in widget.winfo_children():
                try:
                    bind_to_mousewheel(child)
                except:
                    pass  # 忽略无法绑定的控件
        
        # 延迟绑定，确保控件已完全初始化
        self.after(100, lambda: bind_to_mousewheel(widget))
        
        # 优化滚动条性能
        try:
            # 设置滚动增量
            widget._parent_canvas.configure(yscrollincrement=1)
        except:
            pass
        
    def create_widgets(self):
        # 创建主容器
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 创建左右两栏
        self.create_left_panel()
        self.create_right_panel()
        
    def create_left_panel(self):
        # 左侧面板 - 创建滚动框架，优化滚动性能
        self.left_panel = ctk.CTkScrollableFrame(
            self.main_container, 
            width=380, 
            height=650,
            scrollbar_button_color=("gray70", "gray30"),
            scrollbar_button_hover_color=("gray60", "gray40")
        )
        self.left_panel.pack(side="left", fill="y", padx=(0, 10))
        
        # 优化滚动性能 - 绑定更丝滑的滚动事件
        self._bind_mousewheel(self.left_panel)
        
        # Logo和标题
        logo_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        logo_frame.pack(pady=(5, 10))  # 减少顶部和底部间距
        
        ctk.CTkLabel(
            logo_frame, 
            text="🎓 NKU 成绩助手",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack()
        
        ctk.CTkLabel(
            logo_frame,
            text="南开大学成绩查询系统",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(pady=(3, 0))  # 减少间距
        
        # 账号信息卡片
        account_card = ctk.CTkFrame(self.left_panel)
        account_card.pack(fill="x", padx=15, pady=(0, 10))  # 减少底部间距
        
        ctk.CTkLabel(
            account_card,
            text="账号信息",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 6))  # 减少内部间距
        
        # 学号输入
        self.username_var = tk.StringVar(value=self.config.get('username', ''))
        self.create_input_field(account_card, "学号", self.username_var, "👤")
        
        # 密码输入
        self.password_var = tk.StringVar(value=self.config.get('password', ''))
        self.create_input_field(account_card, "WebVPN密码", self.password_var, "🔐", show="*")
        
        # Token输入
        self.token_var = tk.StringVar(value=self.config.get('token', ''))
        self.create_input_field(account_card, "PushPlus Token", self.token_var, "📱", show="*")
        
        # 验证状态显示
        self.verify_status = ctk.CTkLabel(
            account_card,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.verify_status.pack(fill="x", padx=15, pady=(0, 6))  # 减少间距
        
        # 验证和保存按钮框架
        button_frame = ctk.CTkFrame(account_card, fg_color="transparent")
        button_frame.pack(fill="x", padx=15, pady=(0, 8))  # 减少间距
        
        # 验证账号按钮
        self.verify_btn = ctk.CTkButton(
            button_frame,
            text="验证账号",
            height=32,
            font=ctk.CTkFont(size=13),
            fg_color="green",
            hover_color="dark green",
            command=self.verify_account
        )
        self.verify_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # 保存配置按钮
        save_btn = ctk.CTkButton(
            button_frame,
            text="保存配置",
            height=32,
            font=ctk.CTkFont(size=13),
            command=self.save_config_clicked
        )
        save_btn.pack(side="right", fill="x", expand=True, padx=(5, 0))
        
        # 帮助链接
        help_frame = ctk.CTkFrame(account_card, fg_color="transparent")
        help_frame.pack(fill="x", padx=15, pady=(0, 8))  # 减少间距
        
        help_btn2 = ctk.CTkButton(
            help_frame,
            text="如何获取Token？",
            font=ctk.CTkFont(size=11),
            fg_color="transparent", 
            text_color=("blue", "light blue"),
            hover=False,
            anchor="e",
            command=self.show_token_help
        )
        help_btn2.pack(fill="x")
        
        # 学期选择框架
        semester_frame = ctk.CTkFrame(self.left_panel)
        semester_frame.pack(fill="x", padx=15, pady=(0, 10))  # 减少间距
        
        ctk.CTkLabel(
            semester_frame,
            text="学期选择",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 6))  # 减少间距
        
        # 学期选择下拉框
        self.semester_var = tk.StringVar(value="请先验证账号获取学期列表")
        
        self.semester_menu = ctk.CTkOptionMenu(
            semester_frame,
            values=["请先验证账号获取学期列表"],
            variable=self.semester_var,
            height=32,
            font=ctk.CTkFont(size=13),
            dropdown_font=ctk.CTkFont(size=12),
            command=self.on_semester_change,
            state="disabled"
        )
        self.semester_menu.pack(fill="x", padx=15, pady=(0, 6))  # 减少间距
        
        # 刷新学期按钮
        self.refresh_btn = ctk.CTkButton(
            semester_frame,
            text="刷新学期列表",
            height=28,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            border_width=1,
            command=self.refresh_semesters,
            state="disabled"
        )
        self.refresh_btn.pack(fill="x", padx=15, pady=(0, 8))  # 减少间距
        
        # 功能按钮区域
        function_frame = ctk.CTkFrame(self.left_panel)
        function_frame.pack(fill="x", padx=15, pady=(0, 10))  # 减少间距
        
        ctk.CTkLabel(
            function_frame,
            text="功能选择",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 6))  # 减少间距
        
        # 查询按钮
        self.query_btn = ctk.CTkButton(
            function_frame,
            text="查询成绩",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.query_grades,
            state="disabled"
        )
        self.query_btn.pack(fill="x", padx=15, pady=(0, 6))  # 减少间距
        
        # 监控按钮
        self.monitor_btn = ctk.CTkButton(
            function_frame,
            text="开始监控",
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="green",
            hover_color="dark green",
            command=self.toggle_monitor,
            state="disabled"
        )
        self.monitor_btn.pack(fill="x", padx=15, pady=(0, 6))  # 减少间距
        
        # 监控设置
        monitor_settings = ctk.CTkFrame(function_frame, fg_color="transparent")
        monitor_settings.pack(fill="x", padx=15, pady=(0, 6))  # 减少间距
        
        ctk.CTkLabel(
            monitor_settings,
            text="监控间隔(分钟):",
            font=ctk.CTkFont(size=12)
        ).pack(side="left", padx=(0, 8))
        
        self.interval_var = tk.StringVar(value="30")
        interval_entry = ctk.CTkEntry(
            monitor_settings,
            textvariable=self.interval_var,
            width=50,
            height=28,
            font=ctk.CTkFont(size=12)
        )
        interval_entry.pack(side="left")
        
        # 监控状态显示
        self.monitor_status = ctk.CTkLabel(
            function_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.monitor_status.pack(fill="x", padx=15, pady=(0, 8))  # 减少间距
        
        # 状态指示器
        self.status_frame = ctk.CTkFrame(self.left_panel, height=50)
        self.status_frame.pack(fill="x", padx=15, pady=(5, 0))  # 减少顶部间距
        self.status_frame.pack_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="⚪ 就绪",
            font=ctk.CTkFont(size=13)
        )
        self.status_label.pack(expand=True)
        
    def create_right_panel(self):
        # 右侧面板
        self.right_panel = ctk.CTkFrame(self.main_container)
        self.right_panel.pack(side="right", fill="both", expand=True)
        
        # 标签页
        self.tabview = ctk.CTkTabview(self.right_panel)
        self.tabview.pack(fill="both", expand=True, padx=15, pady=15)
        
        # 成绩标签页
        self.grade_tab = self.tabview.add("成绩查询")
        self.create_grade_tab()
        
        # 日志标签页
        self.log_tab = self.tabview.add("运行日志")
        self.create_log_tab()
        
        # 统计标签页
        self.stats_tab = self.tabview.add("成绩统计")
        self.create_stats_tab()
        
    def create_grade_tab(self):
        # 成绩显示区域
        self.grade_frame = ctk.CTkScrollableFrame(self.grade_tab)
        self.grade_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 初始提示
        self.grade_hint = ctk.CTkLabel(
            self.grade_frame,
            text="请先验证账号，然后点击「查询成绩」获取最新成绩",
            font=ctk.CTkFont(size=16),
            text_color="gray"
        )
        self.grade_hint.pack(expand=True, pady=100)
        
    def create_log_tab(self):
        # 日志文本框
        self.log_text = ctk.CTkTextbox(
            self.log_tab, 
            font=ctk.CTkFont(size=11),
            wrap="word"
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 清空按钮
        clear_btn = ctk.CTkButton(
            self.log_tab,
            text="清空日志",
            height=30,
            font=ctk.CTkFont(size=12),
            command=lambda: self.log_text.delete("1.0", "end")
        )
        clear_btn.pack(side="left", padx=(10, 5), pady=(0, 10))
        
        # 查看配置按钮
        config_btn = ctk.CTkButton(
            self.log_tab,
            text="查看配置",
            height=30,
            font=ctk.CTkFont(size=12),
            command=self.show_config_info
        )
        config_btn.pack(side="left", padx=(5, 10), pady=(0, 10))
        
    def create_stats_tab(self):
        # 统计信息容器
        self.stats_frame = ctk.CTkFrame(self.stats_tab)
        self.stats_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # 初始提示
        self.stats_hint = ctk.CTkLabel(
            self.stats_frame,
            text="查询成绩后显示统计信息",
            font=ctk.CTkFont(size=16),
            text_color="gray"
        )
        self.stats_hint.pack(expand=True)
        
    def create_input_field(self, parent, label, variable, icon="", show=None):
        """创建输入框"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=15, pady=(0, 8))  # 减少间距
        
        # 标签
        ctk.CTkLabel(
            frame,
            text=f"{icon} {label}",
            font=ctk.CTkFont(size=12),
            anchor="w"
        ).pack(fill="x", pady=(0, 2))  # 减少间距
        
        # 输入框
        entry = ctk.CTkEntry(
            frame,
            textvariable=variable,
            height=30,
            font=ctk.CTkFont(size=12),
            show=show
        )
        entry.pack(fill="x")
        
    def verify_account(self):
        """验证账号并获取学期数据"""
        if not self.username_var.get().strip():
            messagebox.showerror("错误", "请输入学号")
            return
        if not self.password_var.get().strip():
            messagebox.showerror("错误", "请输入WebVPN密码")
            return
            
        self.verify_btn.configure(state="disabled", text="验证中...")
        self.verify_status.configure(text="正在验证账号...", text_color="yellow")
        self.set_status("🔄 验证账号中...", "yellow")
        self.log("开始验证账号...")
        
        # 在新线程中验证
        thread = threading.Thread(target=self._verify_account_thread)
        thread.daemon = True
        thread.start()
        
    def _verify_account_thread(self):
        """验证账号线程"""
        try:
            checker = WebVPNGradeChecker(
                self.username_var.get(),
                self.password_var.get()
            )
            
            # 步骤1：验证登录
            if checker.login():
                self.log("✅ WebVPN登录成功")
                
                # 步骤2：访问教务系统
                if checker.access_eamis():
                    self.log("✅ 教务系统访问成功")
                    
                    # 步骤3：获取学期数据
                    self.log("正在获取学期列表...")
                    semester_list = checker.get_dynamic_semesters()
                    
                    if semester_list:
                        self.log(f"✅ 成功获取 {len(semester_list)} 个学期")
                        
                        # 更新UI
                        self.after(0, self._update_semester_options, semester_list)
                        self.after(0, self._set_verification_success)
                        
                        # 保存学期数据到配置
                        self.config['semester_data'] = semester_list
                        self.log(f"学期数据已加入配置，共 {len(semester_list)} 个学期")
                        self.after(0, self.save_config_clicked)
                        
                    else:
                        self.log("❌ 获取学期列表失败")
                        self.after(0, self._set_verification_failed, "获取学期列表失败")
                else:
                    self.log("❌ 教务系统访问失败")
                    self.after(0, self._set_verification_failed, "教务系统访问失败")
            else:
                self.log("❌ WebVPN登录失败")
                self.after(0, self._set_verification_failed, "WebVPN登录失败")
                
        except Exception as e:
            self.log(f"❌ 验证过程出错: {e}")
            self.after(0, self._set_verification_failed, f"验证出错: {str(e)}")
        finally:
            self.after(0, self._restore_verify_button)
            
    def _update_semester_options(self, semester_list):
        """更新学期选项"""
        self.semester_options = [(sem['display_name'], sem['id']) for sem in semester_list]
        semester_names = [name for name, _ in self.semester_options]
        
        # 更新下拉框
        self.semester_menu.configure(values=semester_names, state="normal")
        
        # 设置默认选择（2024-2025第2学期，如果找不到就用第一个）
        default_selected = None
        for sem in semester_list:
            if sem['school_year'] == "2024-2025" and sem['term'] == "2":
                default_selected = sem['display_name']
                self.current_semester_id = sem['id']
                break
        
        if not default_selected and semester_list:
            default_selected = semester_list[0]['display_name']
            self.current_semester_id = semester_list[0]['id']
        
        if default_selected:
            self.semester_var.set(default_selected)
            self.log(f"默认选择学期: {default_selected} (ID: {self.current_semester_id})")
        
    def _set_verification_success(self):
        """设置验证成功状态"""
        self.account_verified = True
        self.verify_status.configure(text="✅ 账号验证成功", text_color="green")
        self.set_status("✅ 账号验证成功", "green")
        
        # 启用功能按钮
        self.semester_menu.configure(state="normal")
        self.refresh_btn.configure(state="normal")
        self.query_btn.configure(state="normal")
        self.monitor_btn.configure(state="normal")
        
        # 更新提示文本
        self.grade_hint.configure(text="点击「查询成绩」获取最新成绩")
        
    def _set_verification_failed(self, error_msg):
        """设置验证失败状态"""
        self.account_verified = False
        self.verify_status.configure(text=f"❌ {error_msg}", text_color="red")
        self.set_status(f"❌ {error_msg}", "red")
        
    def _restore_verify_button(self):
        """恢复验证按钮状态"""
        self.verify_btn.configure(state="normal", text="验证账号")
        
    def load_semester_data(self):
        """加载配置中的学期数据"""
        if 'semester_data' in self.config and self.config['semester_data']:
            semester_list = self.config['semester_data']
            self._update_semester_options(semester_list)
            self.log(f"从配置加载了 {len(semester_list)} 个学期")
            
            # 显示已保存的学期概要
            if len(semester_list) > 0:
                first_sem = semester_list[0]
                last_sem = semester_list[-1]
                self.log(f"学期范围: {last_sem['display_name']} ~ {first_sem['display_name']}")
        else:
            self.log("配置中暂无学期数据，请先验证账号获取")
        
    def on_semester_change(self, choice):
        """学期选择改变"""
        # 从选项中找到对应的ID
        for name, semester_id in self.semester_options:
            if name == choice:
                self.current_semester_id = semester_id
                self.log(f"已选择学期: {choice} (ID: {semester_id})")
                break
        else:
            # 如果没找到，尝试从semester_data中查找
            if 'semester_data' in self.config:
                for sem in self.config['semester_data']:
                    if sem['display_name'] == choice:
                        self.current_semester_id = sem['id']
                        self.log(f"已选择学期: {choice} (ID: {sem['id']})")
                        break
                else:
                    self.current_semester_id = "4324"  # 默认值
                    self.log(f"未找到学期ID，使用默认值: {self.current_semester_id}")
    
    def refresh_semesters(self):
        """刷新学期列表"""
        if not self.validate_input():
            return
            
        self.log("正在刷新学期列表...")
        self.set_status("🔄 刷新学期列表中...", "yellow")
        
        self.refresh_btn.configure(state="disabled", text="刷新中...")
        
        thread = threading.Thread(target=self._refresh_semesters_thread)
        thread.daemon = True
        thread.start()
        
    def _refresh_semesters_thread(self):
        """刷新学期列表线程"""
        try:
            checker = WebVPNGradeChecker(
                self.username_var.get(),
                self.password_var.get()
            )
            
            if checker.login():
                self.log("✅ 登录成功")
                if checker.access_eamis():
                    self.log("✅ 进入教务系统")
                    
                    # 使用动态获取方法
                    semester_list = checker.get_dynamic_semesters()
                    
                    if semester_list:
                        self.log(f"✅ 刷新成功，获取到 {len(semester_list)} 个学期")
                        
                        # 更新UI
                        self.after(0, self._update_semester_options, semester_list)
                        self.after(0, lambda: self.set_status("✅ 学期列表已刷新", "green"))
                        
                        # 保存到配置
                        self.config['semester_data'] = semester_list
                        self.log(f"学期数据已更新到配置，共 {len(semester_list)} 个学期")
                        self.after(0, self.save_config_clicked)
                        
                    else:
                        self.log("❌ 获取学期列表失败")
                        self.after(0, lambda: self.set_status("❌ 获取学期列表失败", "red"))
                else:
                    self.log("❌ 访问教务系统失败")
                    self.after(0, lambda: self.set_status("❌ 访问教务系统失败", "red"))
            else:
                self.log("❌ 登录失败")
                self.after(0, lambda: self.set_status("❌ 登录失败", "red"))
        except Exception as e:
            self.log(f"❌ 刷新学期失败: {e}")
            self.after(0, lambda: self.set_status("❌ 刷新学期失败", "red"))
        finally:
            self.after(0, lambda: self.refresh_btn.configure(state="normal", text="刷新学期列表"))
        
    def log(self, message):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        self.log_text.insert("end", log_message)
        self.log_text.see("end")
        
    def set_status(self, text, color="white"):
        """设置状态"""
        self.status_label.configure(text=text, text_color=color)
        
    def query_grades(self):
        """查询成绩"""
        if not self.validate_input():
            return
        
        if not self.account_verified:
            messagebox.showwarning("提示", "请先验证账号")
            return
        
        # 直接使用存储的学期ID
        semester_id = self.current_semester_id
        selected_name = self.semester_var.get()
        
        self.query_btn.configure(state="disabled", text="查询中...")
        self.set_status(f"🔄 正在查询学期 {semester_id}...", "yellow")
        self.log(f"开始查询 {selected_name} (ID: {semester_id}) 的成绩...")
        
        # 在新线程中运行
        thread = threading.Thread(target=self._query_grades_thread, args=(semester_id,))
        thread.daemon = True
        thread.start()
        
    def _query_grades_thread(self, semester_id):
        """查询成绩线程 - 增强日志版"""
        try:
            # 创建查询实例，传入日志回调
            from nku_grades import WebVPNGradeChecker
            checker = WebVPNGradeChecker(
                self.username_var.get(),
                self.password_var.get(),
                log_callback=self.log  # 传入日志回调
            )
            
            # 后续代码保持不变，因为现在 checker 会自动将日志输出到GUI
            if checker.login():
                if checker.access_eamis():
                    grades = checker.get_grades(semester_id)
                    
                    if grades:
                        self.log(f"✅ 获取到 {len(grades)} 门成绩")
                        self.after(0, self.display_grades, grades)
                        self.after(0, self.update_stats, grades)
                        self.after(0, lambda: self.set_status("✅ 查询成功", "green"))
                        
                        # 询问是否推送
                        if self.token_var.get():
                            self.after(0, self.ask_push, grades, checker, semester_id)
                    else:
                        self.log("❌ 未获取到成绩（该学期可能没有成绩）")
                        self.after(0, lambda: self.set_status("❌ 未获取到成绩", "red"))
                else:
                    self.log("❌ 访问教务系统失败")
                    self.after(0, lambda: self.set_status("❌ 访问失败", "red"))
            else:
                self.log("❌ 登录失败")
                self.after(0, lambda: self.set_status("❌ 登录失败", "red"))
                
        except Exception as e:
            self.log(f"❌ 出错: {str(e)}")
            self.after(0, lambda: self.set_status("❌ 查询出错", "red"))
        finally:
            self.after(0, lambda: self.query_btn.configure(state="normal", text="查询成绩"))
            
    def display_grades(self, grades):
        """显示成绩"""
        # 清空原有内容
        for widget in self.grade_frame.winfo_children():
            widget.destroy()
            
        # 显示每门课程
        for i, grade in enumerate(grades):
            self.create_grade_card(self.grade_frame, grade, i)
            
    def create_grade_card(self, parent, grade, index):
        """创建成绩卡片"""
        # 根据等级设置颜色
        grade_colors = {
            'A': '#4CAF50', 'A-': '#66BB6A',
            'B+': '#42A5F5', 'B': '#2196F3', 'B-': '#1E88E5',
            'C+': '#FFA726', 'C': '#FF9800', 'C-': '#FB8C00',
            'D': '#EF5350', 'F': '#F44336',
            '通过': '#9E9E9E', '不通过': '#F44336'
        }
        
        color = grade_colors.get(grade['等级'], '#757575')
        
        # 卡片容器
        card = ctk.CTkFrame(parent, height=75)
        card.pack(fill="x", pady=(0, 8))
        card.pack_propagate(False)
        
        # 左侧信息
        left_frame = ctk.CTkFrame(card, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True, padx=12, pady=12)
        
        ctk.CTkLabel(
            left_frame,
            text=grade['课程名称'],
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w"
        ).pack(fill="x")
        
        ctk.CTkLabel(
            left_frame,
            text=f"{grade['课程代码']} · {grade['课程类别']} · {grade['学分']}学分",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w"
        ).pack(fill="x", pady=(3, 0))
        
        # 右侧成绩
        right_frame = ctk.CTkFrame(card, fg_color="transparent")
        right_frame.pack(side="right", padx=12, pady=12)
        
        # 等级标签
        grade_label = ctk.CTkLabel(
            right_frame,
            text=grade['等级'],
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=color
        )
        grade_label.pack()
        
        # 绩点标签
        if grade['绩点'] is not None:
            ctk.CTkLabel(
                right_frame,
                text=f"绩点 {grade['绩点']}",
                font=ctk.CTkFont(size=10),
                text_color="gray"
            ).pack(pady=(2, 0))
        else:
            ctk.CTkLabel(
                right_frame,
                text=grade['绩点文本'],
                font=ctk.CTkFont(size=10),
                text_color="gray"
            ).pack(pady=(2, 0))
            
    def update_stats(self, grades):
        """更新统计信息"""
        # 清空原有内容
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
            
        # 计算统计数据
        total_credits = sum(g['学分'] for g in grades)
        graded_courses = [g for g in grades if g['绩点'] is not None]
        
        if graded_courses:
            gpa_credits = sum(g['学分'] for g in graded_courses)
            weighted_gpa = sum(g['学分'] * g['绩点'] for g in graded_courses)
            avg_gpa = weighted_gpa / gpa_credits
        else:
            avg_gpa = 0
            gpa_credits = 0
            
        # 等级统计
        grade_stats = {}
        for grade in grades:
            level = grade['等级']
            if level not in grade_stats:
                grade_stats[level] = 0
            grade_stats[level] += 1
            
        # 显示统计卡片
        stats_data = [
            ("📚 总课程数", f"{len(grades)} 门"),
            ("💯 总学分", f"{total_credits} 分"),
            ("⭐ 平均绩点", f"{avg_gpa:.3f}"),
            ("📊 等级制课程", f"{len(graded_courses)} 门")
        ]
        
        # 创建2x2网格
        for i, (label, value) in enumerate(stats_data):
            row = i // 2
            col = i % 2
            
            stat_card = ctk.CTkFrame(self.stats_frame, height=80)
            stat_card.grid(row=row, column=col, padx=8, pady=8, sticky="ew")
            stat_card.pack_propagate(False)
            
            ctk.CTkLabel(
                stat_card,
                text=label,
                font=ctk.CTkFont(size=12),
                text_color="gray"
            ).pack(pady=(12, 3))
            
            ctk.CTkLabel(
                stat_card,
                text=value,
                font=ctk.CTkFont(size=20, weight="bold")
            ).pack(pady=(0, 12))
            
        # 配置网格权重
        self.stats_frame.grid_columnconfigure(0, weight=1)
        self.stats_frame.grid_columnconfigure(1, weight=1)
        
        # 等级分布
        if grade_stats:
            grade_dist_frame = ctk.CTkFrame(self.stats_frame)
            grade_dist_frame.grid(row=2, column=0, columnspan=2, padx=8, pady=8, sticky="ew")
            
            ctk.CTkLabel(
                grade_dist_frame,
                text="📈 等级分布",
                font=ctk.CTkFont(size=13, weight="bold")
            ).pack(pady=(10, 5))
            
            # 按等级顺序排列
            grade_order = ['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F', '通过', '不通过']
            for grade_level in grade_order:
                if grade_level in grade_stats:
                    grade_info = ctk.CTkLabel(
                        grade_dist_frame,
                        text=f"{grade_level}: {grade_stats[grade_level]} 门",
                        font=ctk.CTkFont(size=11)
                    )
                    grade_info.pack(pady=1)
            
            # 其他等级
            other_grades = [g for g in grade_stats if g not in grade_order]
            for grade_level in other_grades:
                grade_info = ctk.CTkLabel(
                    grade_dist_frame,
                    text=f"{grade_level}: {grade_stats[grade_level]} 门",
                    font=ctk.CTkFont(size=11)
                )
                grade_info.pack(pady=1)
                
            # 底部留白
            ctk.CTkLabel(grade_dist_frame, text="").pack(pady=5)
        
    def ask_push(self, grades, checker, semester_id):
        """询问是否推送"""
        result = messagebox.askyesno("推送确认", "是否将成绩推送到微信？")
        if result:
            try:
                html = checker.build_grade_html(grades, semester_id)
                if checker.send_pushplus(self.token_var.get(), f"成绩查询结果 - 学期{semester_id}", html):
                    self.log("✅ 推送成功")
                    self.set_status("✅ 已推送到微信", "green")
                else:
                    self.log("❌ 推送失败")
                    self.set_status("❌ 推送失败", "red")
            except Exception as e:
                self.log(f"❌ 推送出错: {e}")
                self.set_status("❌ 推送出错", "red")
                
    def toggle_monitor(self):
        """切换监控状态 - 增强版"""
        if not self.monitoring:
            if not self.validate_input(need_token=True):
                return
            
            if not self.account_verified:
                messagebox.showwarning("提示", "请先验证账号")
                return
            
            # 获取并验证监控间隔
            try:
                interval = int(self.interval_var.get())
                if interval < 5:
                    messagebox.showwarning("警告", "监控间隔不能小于5分钟")
                    return
            except:
                messagebox.showerror("错误", "请输入有效的监控间隔")
                return
            
            self.monitoring = True
            self.monitor_btn.configure(
                text="停止监控",
                fg_color="red",
                hover_color="dark red"
            )
            self.set_status("📡 启动监控中...", "yellow")
            
            # 使用当前选中的学期
            semester_id = self.current_semester_id
            selected_name = self.semester_var.get()
            
            self.log(f"开始监控成绩变化 (学期: {selected_name}, ID: {semester_id}, 间隔: {interval}分钟)")
            self.log("🔧 增强功能:")
            self.log("   ✅ 自动检测新增课程")
            self.log("   ✅ 自动检测成绩更新") 
            self.log("   ✅ 详细的HTML微信推送")
            self.log("   ✅ 完善的监控日志")
            self.log("   ✅ 兼容22级百分制和23级等级制")
            
            # 创建并启动增强监控线程
            self.monitor_thread = self._create_enhanced_monitor(semester_id, interval)
            self.monitor_thread.start_monitoring()
            
        else:
            self.monitoring = False
            self.monitor_btn.configure(
                text="开始监控",
                fg_color="green",
                hover_color="dark green"
            )
            self.set_status("⚪ 就绪")
            self.monitor_status.configure(text="", text_color="gray")
            self.log("停止监控")
            
            # 停止监控线程
            if self.monitor_thread:
                self.monitor_thread.stop_monitoring()
            
    def _create_enhanced_monitor(self, semester_id, interval):
        """创建增强的监控线程"""
        class EnhancedGUIMonitor(threading.Thread):
            def __init__(self, username, password, token, semester_id, interval, gui_app):
                super().__init__()
                self.username = username
                self.password = password
                self.token = token
                self.semester_id = semester_id
                self.interval = interval
                self.gui_app = gui_app
                self.running = False
                self.daemon = True
                
                # 创建监控实例，传入日志回调
                from nku_grades import GradeMonitor
                self.monitor = GradeMonitor(username, password, token, log_callback=self.log)
            
            def log(self, message):
                """日志回调到GUI"""
                self.gui_app.after(0, lambda: self.gui_app.log(message))
            
            def update_status(self, message, color="white"):
                """状态更新回调到GUI"""
                self.gui_app.after(0, lambda: self.gui_app.set_status(message, color))
            
            def start_monitoring(self):
                """开始监控"""
                self.running = True
                self.start()
            
            def stop_monitoring(self):
                """停止监控"""
                self.running = False
            
            def run(self):
                """监控主循环"""
                self.log(f"🚀 开始监控学期 {self.semester_id}，每 {self.interval} 分钟检查一次")
                self.log(f"📱 推送Token: {'已配置' if self.token else '未配置'}")
                
                check_count = 0
                
                while self.running:
                    try:
                        check_count += 1
                        self.log(f"\n{'='*60}")
                        self.log(f"🔍 第 {check_count} 次检查 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        self.log(f"{'='*60}")
                        
                        self.update_status(f"🔄 正在进行第 {check_count} 次检查...", "yellow")
                        
                        # 登录检查
                        if not self.monitor.login():
                            self.log("❌ 登录失败，等待下次检查")
                            self.update_status("❌ 登录失败", "red")
                        elif not self.monitor.access_eamis():
                            self.log("❌ 访问教务系统失败，等待下次检查")
                            self.update_status("❌ 访问教务系统失败", "red")
                        else:
                            # 检查成绩
                            has_changes = self.monitor.check_grades(self.semester_id)
                            
                            if has_changes:
                                self.log("🎊 本次检查发现成绩变化！")
                                self.update_status("🎉 发现成绩变化！", "green")
                            else:
                                self.log("😴 本次检查无变化")
                                self.update_status("✅ 监控正常，无变化", "green")
                        
                        if not self.running:
                            break
                        
                        # 计算下次检查时间并更新GUI状态
                        next_check_time = datetime.now() + timedelta(minutes=self.interval)
                        self.log(f"⏰ 下次检查时间: {next_check_time.strftime('%H:%M:%S')}")
                        self.log(f"💤 等待 {self.interval} 分钟...")
                        
                        # 等待指定时间，期间定期更新状态
                        for i in range(self.interval):
                            if not self.running:
                                break
                            
                            remaining = self.interval - i
                            
                            # 更新监控状态显示
                            if remaining > 1:
                                self.gui_app.after(0, lambda r=remaining: self.gui_app.monitor_status.configure(
                                    text=f"下次检查: {r-1} 分钟后",
                                    text_color="green"
                                ))
                            
                            time.sleep(60)  # 等待1分钟
                        
                    except Exception as e:
                        self.log(f"❌ 监控过程出错: {e}")
                        self.update_status("❌ 监控出错", "red")
                        if self.running:
                            self.log("⏱️ 等待1分钟后继续...")
                            time.sleep(60)
                
                self.log("🛑 监控已停止")
                self.update_status("⚪ 就绪", "white")
                
                # 清空监控状态
                self.gui_app.after(0, lambda: self.gui_app.monitor_status.configure(text="", text_color="gray"))
        
        return EnhancedGUIMonitor(
            self.username_var.get(),
            self.password_var.get(), 
            self.token_var.get(),
            semester_id,
            interval,
            self
        )

    def show_config_info(self):
        """显示配置文件信息"""
        config_file = 'gui_config.json'
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                
                self.log("=" * 50)
                self.log("📄 当前配置文件信息:")
                self.log(f"文件路径: {os.path.abspath(config_file)}")
                self.log(f"文件大小: {os.path.getsize(config_file)} bytes")
                
                # 显示配置内容概要
                self.log("\n配置内容:")
                if 'username' in file_config:
                    self.log(f"  学号: {file_config['username']}")
                if 'password' in file_config:
                    self.log(f"  密码: {'*' * len(file_config['password'])}")
                if 'token' in file_config:
                    self.log(f"  Token: {'*' * min(8, len(file_config['token']))}...")
                
                if 'semester_data' in file_config and file_config['semester_data']:
                    semester_data = file_config['semester_data']
                    self.log(f"  学期数据: {len(semester_data)} 个学期")
                    
                    # 显示前几个学期
                    self.log("  学期列表:")
                    for i, sem in enumerate(semester_data[:5]):
                        self.log(f"    {i+1}. {sem['display_name']} (ID: {sem['id']})")
                    
                    if len(semester_data) > 5:
                        self.log(f"    ... 还有 {len(semester_data) - 5} 个学期")
                else:
                    self.log("  学期数据: 未保存")
                
                self.log("=" * 50)
                
            except Exception as e:
                self.log(f"❌ 读取配置文件失败: {e}")
        else:
            self.log(f"❌ 配置文件 {config_file} 不存在")
            
    def validate_input(self, need_token=False):
        """验证输入"""
        if not self.username_var.get().strip():
            messagebox.showerror("错误", "请输入学号")
            return False
        if not self.password_var.get().strip():
            messagebox.showerror("错误", "请输入WebVPN密码")
            return False
        if need_token and not self.token_var.get().strip():
            messagebox.showerror("错误", "监控功能需要PushPlus Token")
            return False
        return True
        
    def show_token_help(self):
        """显示Token获取帮助"""
        help_window = ctk.CTkToplevel(self)
        help_window.title("如何获取PushPlus Token")
        help_window.geometry("600x500")
        help_window.grab_set()  # 模态窗口
        
        # 帮助内容
        help_text = """获取PushPlus Token步骤：

1. 访问PushPlus官网
   网址：http://www.pushplus.plus/

2. 注册账号
   - 点击右上角"登录/注册"
   - 使用微信扫码注册登录
   - 不过注意的是需要实名认证，需要花费一块钱（当然不是支付给我的）

3. 获取Token的
   - 在网站上选择"发送消息"
   - 选择"一对一消息",此处就可以看到你的Token
   - Token是一串32位的字符串，类似：abcd1234efgh5678...

5. 复制Token
   - 将Token复制
   - 粘贴到本程序的"PushPlus Token"输入框中

注意事项：
- Token是免费的，每天可以发送200条消息
- 请妥善保管你的Token，不要泄露给他人
- 如果Token失效，可以重新登录网站获取新的

Token的作用：
- 用于成绩查询后推送结果到微信
- 用于成绩监控功能的变化通知
- 无需填写也可以使用查询功能，只是无法推送"""
        
        # 创建滚动文本框
        text_widget = ctk.CTkTextbox(
            help_window, 
            font=ctk.CTkFont(size=12),
            wrap="word"
        )
        text_widget.pack(fill="both", expand=True, padx=15, pady=15)
        text_widget.insert("1.0", help_text)
        text_widget.configure(state="disabled")
        
        # 按钮框架
        button_frame = ctk.CTkFrame(help_window, fg_color="transparent")
        button_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # 访问网站按钮
        visit_btn = ctk.CTkButton(
            button_frame,
            text="访问官网",
            font=ctk.CTkFont(size=12),
            command=lambda: webbrowser.open("http://www.pushplus.plus/")
        )
        visit_btn.pack(side="left", padx=(0, 10))
        
        # 关闭按钮
        close_btn = ctk.CTkButton(
            button_frame,
            text="我知道了",
            font=ctk.CTkFont(size=12),
            command=help_window.destroy
        )
        close_btn.pack(side="right")
        
    def save_config_clicked(self):
        """保存配置"""
        # 更新基本配置，但保留已有的其他数据（如学期数据）
        self.config.update({
            'username': self.username_var.get(),
            'password': self.password_var.get(),
            'token': self.token_var.get()
        })
        
        try:
            with open('gui_config.json', 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            # 显示保存的内容概要
            config_summary = f"配置已保存 (包含: 账号信息"
            if 'semester_data' in self.config:
                config_summary += f", {len(self.config['semester_data'])}个学期"
            config_summary += ")"
            
            self.log(f"✅ {config_summary}")
            self.set_status("✅ 配置已保存", "green")
        except Exception as e:
            self.log(f"❌ 保存配置失败: {e}")
            self.set_status("❌ 保存配置失败", "red")
        
    def load_config(self):
        """加载配置"""
        self.config = {}
        if os.path.exists('gui_config.json'):
            try:
                with open('gui_config.json', 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except Exception as e:
                print(f"加载配置失败: {e}")
                self.config = {}

    def on_closing(self):
        """关闭窗口时的处理"""
        if self.monitoring:
            self.monitoring = False
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=1)
        self.destroy()

if __name__ == "__main__":
    app = ModernGradeApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
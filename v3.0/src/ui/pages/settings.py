"""
NKU成绩查询 v3.0 - 设置页
配置管理和账号登录
"""

import flet as ft
from ...data.database import get_db


class SettingsPage(ft.Container):
    """设置页类"""

    def __init__(self, app_state):
        super().__init__()
        self.app_state = app_state
        self.db = get_db()

        # 输入框
        self.username_field = ft.TextField(
            label="学号",
            width=300,
            text_size=14,
        )

        self.password_field = ft.TextField(
            label="密码",
            password=True,
            can_reveal_password=True,
            width=300,
            text_size=14,
        )

        # 状态文本
        self.status_text = ft.Text("", size=12, color=ft.colors.GREY_600)

        # 登录按钮
        self.login_btn = ft.ElevatedButton(
            "验证登录",
            on_click=self.on_login_click,
            width=300,
        )

        # PushPlus 推送配置
        self.pushplus_token_field = ft.TextField(
            label="PushPlus Token",
            width=300,
            text_size=14,
            password=True,
            can_reveal_password=True,
            hint_text="从 pushplus.plus 获取",
        )

        self.save_pushplus_btn = ft.ElevatedButton(
            "保存推送配置",
            on_click=self.on_save_pushplus_click,
            width=300,
        )

        # 如何获取Token按钮
        self.token_help_btn = ft.TextButton(
            "如何获取Token？",
            on_click=self.show_token_help,
            style=ft.ButtonStyle(
                color=ft.colors.BLUE,
            ),
        )

        # 清理按钮
        self.clear_cache_btn = ft.OutlinedButton(
            "清理成绩缓存",
            on_click=self.on_clear_cache_click,
            width=145,
            icon=ft.icons.CLEANING_SERVICES_OUTLINED,
        )

        self.clear_all_btn = ft.OutlinedButton(
            "清理所有数据",
            on_click=self.on_clear_all_click,
            width=145,
            icon=ft.icons.DELETE_SWEEP_OUTLINED,
        )

        # 加载保存的配置
        self._load_config()

        # 构建UI
        self.content = ft.Column(
            [
                ft.Container(height=20),
                ft.Text("账号设置", size=24, weight=ft.FontWeight.W_600),
                ft.Container(height=20),
                self.username_field,
                ft.Container(height=10),
                self.password_field,
                ft.Container(height=20),
                self.login_btn,
                ft.Container(height=10),
                self.status_text,
                ft.Container(height=30),
                ft.Divider(),
                ft.Container(height=10),
                ft.Text("推送配置", size=20, weight=ft.FontWeight.W_500),
                ft.Container(height=15),
                ft.Text("PushPlus 微信推送", size=14, weight=ft.FontWeight.W_500),
                ft.Container(height=5),
                self.pushplus_token_field,
                ft.Container(height=10),
                self.save_pushplus_btn,
                ft.Container(height=5),
                self.token_help_btn,
                ft.Container(height=5),
                ft.Text(
                    "成绩变化时推送到微信（免费，每天200条）",
                    size=11,
                    color=ft.colors.GREY_600,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=30),
                ft.Divider(),
                ft.Container(height=10),
                ft.Text("数据管理", size=20, weight=ft.FontWeight.W_500),
                ft.Container(height=15),
                ft.Row(
                    [self.clear_cache_btn, self.clear_all_btn],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10,
                ),
                ft.Container(height=10),
                ft.Text(
                    "清理成绩缓存：删除历史成绩和日志，保留账号配置",
                    size=11,
                    color=ft.colors.GREY_600,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "清理所有数据：删除所有数据，包括账号密码",
                    size=11,
                    color=ft.colors.GREY_600,
                    text_align=ft.TextAlign.CENTER,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
        )
        self.alignment = ft.alignment.top_center
        self.expand = True
        self.padding = 20

    def _load_config(self):
        """加载保存的配置"""
        username = self.db.get_config("username")
        password = self.db.get_config("password")
        pushplus_token = self.db.get_config("pushplus_token")

        if username:
            self.username_field.value = username
        if password:
            self.password_field.value = password
        if pushplus_token:
            self.pushplus_token_field.value = pushplus_token

    def on_login_click(self, e):
        """登录按钮点击事件"""
        username = self.username_field.value
        password = self.password_field.value

        if not username or not password:
            self.status_text.value = "请输入学号和密码"
            self.status_text.color = ft.colors.RED
            self.update()
            return

        # 保存配置
        self.db.save_config("username", username)
        self.db.save_config("password", password)

        # 更新状态
        self.status_text.value = "正在登录..."
        self.status_text.color = ft.colors.BLUE
        self.login_btn.disabled = True
        self.update()

        # 执行登录（在后台线程）
        import threading
        threading.Thread(target=self._do_login, args=(username, password), daemon=True).start()

    def _do_login(self, username: str, password: str):
        """执行登录（后台线程）"""
        from ...core.auth import WebVPNAuthenticator
        from ...core.semester import SemesterManager

        try:
            # 创建认证器
            auth = WebVPNAuthenticator(username, password, log_callback=self._log)

            # 登录
            if not auth.login():
                self._update_status("登录失败，请检查学号和密码", ft.colors.RED)
                return

            # 访问教务系统
            if not auth.access_eamis():
                self._update_status("访问教务系统失败", ft.colors.RED)
                return

            # 获取学期列表
            semester_mgr = SemesterManager(auth.session, auth.base_url, log_callback=self._log)
            semesters = semester_mgr.get_semesters()

            # 保存到应用状态
            self.app_state["auth"] = auth
            self.app_state["semesters"] = semesters
            self.app_state["logged_in"] = True

            self._update_status(f"登录成功！找到 {len(semesters)} 个学期", ft.colors.GREEN)

        except Exception as e:
            self._update_status(f"登录出错: {str(e)}", ft.colors.RED)

    def _log(self, message: str):
        """日志回调"""
        print(f"[Settings] {message}")

    def on_save_pushplus_click(self, e):
        """保存PushPlus配置"""
        token = self.pushplus_token_field.value

        if not token:
            self.status_text.value = "请输入 PushPlus Token"
            self.status_text.color = ft.colors.RED
            self.update()
            return

        self.db.save_config("pushplus_token", token)

        self.status_text.value = "推送配置已保存"
        self.status_text.color = ft.colors.GREEN
        self.update()

    def show_token_help(self, e):
        """显示Token获取帮助"""
        if not hasattr(self, 'page') or not self.page:
            return

        help_text = """获取PushPlus Token步骤：

1. 访问PushPlus官网
   网址：http://www.pushplus.plus/

2. 注册账号
   - 点击右上角"登录/注册"
   - 使用微信扫码登录

3. 关注公众号
   - 扫描页面上的二维码
   - 关注"PushPlus推送加"公众号

4. 复制Token
   - 登录后在首页可以看到你的Token
   - 将Token复制粘贴到上方输入框

注意事项：
- Token是免费的，每天可以发送200条消息
- 不要泄露你的Token给他人
- 推送消息会实时发送到微信公众号"""

        dialog = ft.AlertDialog(
            title=ft.Text("如何获取PushPlus Token"),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(help_text, size=13, selectable=True),
                        ft.Container(height=10),
                        ft.ElevatedButton(
                            "访问官网",
                            icon=ft.icons.OPEN_IN_BROWSER,
                            on_click=lambda _: self._open_url("http://www.pushplus.plus/"),
                        ),
                    ],
                    tight=True,
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=450,
                height=400,
            ),
            actions=[
                ft.TextButton("关闭", on_click=lambda _: self.page.close(dialog)),
            ],
        )
        self.page.open(dialog)

    def _open_url(self, url: str):
        """打开网址"""
        import webbrowser
        webbrowser.open(url)

    def on_clear_cache_click(self, e):
        """清理成绩缓存按钮点击"""
        def confirm_action(confirmed):
            if confirmed:
                self.db.clear_grades_only()
                self.status_text.value = "成绩缓存已清理"
                self.status_text.color = ft.colors.GREEN
                self.update()

        # 显示确认对话框
        if hasattr(self, 'page') and self.page:
            dialog = ft.AlertDialog(
                title=ft.Text("确认清理"),
                content=ft.Text("确定要清理成绩缓存吗？这将删除所有历史成绩和监控日志，但保留账号配置。"),
                actions=[
                    ft.TextButton("取消", on_click=lambda _: self.page.close(dialog)),
                    ft.TextButton("确定", on_click=lambda _: (confirm_action(True), self.page.close(dialog))),
                ],
            )
            self.page.open(dialog)

    def on_clear_all_click(self, e):
        """清理所有数据按钮点击"""
        def confirm_action(confirmed):
            if confirmed:
                self.db.clear_all_data()
                # 清空输入框
                self.username_field.value = ""
                self.password_field.value = ""
                self.pushplus_token_field.value = ""
                # 清空应用状态
                self.app_state["logged_in"] = False
                self.app_state["auth"] = None
                self.app_state["semesters"] = []
                self.status_text.value = "所有数据已清理"
                self.status_text.color = ft.colors.GREEN
                self.update()

        # 显示确认对话框
        if hasattr(self, 'page') and self.page:
            dialog = ft.AlertDialog(
                title=ft.Text("确认清理"),
                content=ft.Text("确定要清理所有数据吗？这将删除账号密码、历史成绩和所有配置，操作不可恢复！"),
                actions=[
                    ft.TextButton("取消", on_click=lambda _: self.page.close(dialog)),
                    ft.TextButton("确定", on_click=lambda _: (confirm_action(True), self.page.close(dialog))),
                ],
            )
            self.page.open(dialog)

    def _update_status(self, message: str, color):
        """更新状态文本（从后台线程调用）"""
        async def update_ui():
            self.status_text.value = message
            self.status_text.color = color
            self.login_btn.disabled = False
            self.update()

        # 使用 page.run_task() 从主线程更新UI
        if hasattr(self, 'page') and self.page:
            self.page.run_task(update_ui)

"""
NKU成绩查询 v3.0 - 主应用
底部导航栏 + 页面路由
"""

import flet as ft
from .theme import get_app_theme
from .pages.home import HomePage
from .pages.query import QueryPage
from .pages.monitor import MonitorPage
from .pages.settings import SettingsPage


class NKUGradesApp:
    """NKU成绩查询主应用类"""

    def __init__(self, page: ft.Page):
        self.page = page
        self.current_page_index = 0

        # 应用状态（在页面间共享）
        self.app_state = {
            "logged_in": False,
            "auth": None,
            "semesters": [],
        }

        # 配置页面
        self.page.title = "NKU成绩查询"
        self.page.theme = get_app_theme()

        # 设置中文字体（微软雅黑，Windows系统自带）
        self.page.theme.font_family = "Microsoft YaHei"
        self.page.padding = 0
        self.page.window.width = 400
        self.page.window.height = 700
        self.page.window.resizable = True

        # 创建页面实例
        self.home_page = HomePage(self.app_state)
        self.query_page = QueryPage(self.app_state)
        self.monitor_page = MonitorPage(self.app_state)
        self.settings_page = SettingsPage(self.app_state)

        # 检查是否已保存账号密码，决定启动页面
        from ..data.database import get_db
        db = get_db()
        username = db.get_config("username")
        password = db.get_config("password")

        # 如果未登录，默认打开设置页；否则打开首页
        if not username or not password:
            initial_index = 3  # 设置页
            initial_content = self.settings_page
        else:
            initial_index = 0  # 首页
            initial_content = self.home_page
            # 自动登录（后台线程）
            import threading
            threading.Thread(target=self._auto_login, args=(username, password), daemon=True).start()

        # 创建页面容器
        self.page_container = ft.Container(
            content=initial_content,
            expand=True,
        )

        # 创建底部导航栏
        self.navigation_bar = ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.icons.HOME_OUTLINED,
                    selected_icon=ft.icons.HOME,
                    label="首页",
                ),
                ft.NavigationBarDestination(
                    icon=ft.icons.SEARCH_OUTLINED,
                    selected_icon=ft.icons.SEARCH,
                    label="查询",
                ),
                ft.NavigationBarDestination(
                    icon=ft.icons.MONITOR_HEART_OUTLINED,
                    selected_icon=ft.icons.MONITOR_HEART,
                    label="监控",
                ),
                ft.NavigationBarDestination(
                    icon=ft.icons.SETTINGS_OUTLINED,
                    selected_icon=ft.icons.SETTINGS,
                    label="设置",
                ),
            ],
            selected_index=initial_index,
            on_change=self.on_navigation_change,
        )

        # 构建页面布局
        self.page.add(
            ft.Column(
                [
                    # 主内容区域
                    self.page_container,
                    # 底部导航栏
                    self.navigation_bar,
                ],
                spacing=0,
                expand=True,
            )
        )

    def _auto_login(self, username: str, password: str):
        """自动登录（后台线程）"""
        from ..core.auth import WebVPNAuthenticator
        from ..core.semester import SemesterManager

        try:
            print("[自动登录] 开始...")
            auth = WebVPNAuthenticator(username, password, log_callback=lambda msg: print(f"[自动登录] {msg}"))

            if not auth.login():
                print("[自动登录] 登录失败")
                return

            if not auth.access_eamis():
                print("[自动登录] 访问教务系统失败")
                return

            semester_mgr = SemesterManager(auth.session, auth.base_url, log_callback=lambda msg: print(f"[自动登录] {msg}"))
            semesters = semester_mgr.get_semesters()

            # 保存到应用状态
            self.app_state["auth"] = auth
            self.app_state["semesters"] = semesters
            self.app_state["logged_in"] = True

            print(f"[自动登录] 成功！找到 {len(semesters)} 个学期")

        except Exception as e:
            print(f"[自动登录] 出错: {e}")

    def on_navigation_change(self, e: ft.ControlEvent):
        """底部导航栏切换事件"""
        selected_index = e.control.selected_index
        self.current_page_index = selected_index

        # 根据选中的索引切换页面
        if selected_index == 0:
            self.page_container.content = self.home_page
            # 进入首页时刷新
            if hasattr(self.home_page, 'on_page_show'):
                self.home_page.on_page_show()
        elif selected_index == 1:
            self.page_container.content = self.query_page
            # 进入查询页时更新学期列表
            if hasattr(self.query_page, 'on_page_show'):
                self.query_page.on_page_show()
        elif selected_index == 2:
            self.page_container.content = self.monitor_page
            # 进入监控页时刷新
            if hasattr(self.monitor_page, 'on_page_show'):
                self.monitor_page.on_page_show()
        elif selected_index == 3:
            self.page_container.content = self.settings_page

        self.page.update()


def main(page: ft.Page):
    """应用入口函数"""
    NKUGradesApp(page)

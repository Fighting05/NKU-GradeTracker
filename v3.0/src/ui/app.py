"""
NKU成绩查询 v3.0 - 主应用
底部导航栏 + 页面路由
"""

import sys
import traceback

print("[DEBUG] app.py - 开始导入模块...")

try:
    import flet as ft
    print("[DEBUG] app.py - flet 导入成功")

    from .theme import get_app_theme
    print("[DEBUG] app.py - theme 导入成功")

    from .pages.home import HomePage
    print("[DEBUG] app.py - HomePage 导入成功")

    from .pages.query import QueryPage
    print("[DEBUG] app.py - QueryPage 导入成功")

    from .pages.monitor import MonitorPage
    print("[DEBUG] app.py - MonitorPage 导入成功")

    from .pages.settings import SettingsPage
    print("[DEBUG] app.py - SettingsPage 导入成功")

except Exception as e:
    print(f"[ERROR] app.py - 导入失败: {e}")
    print(f"[ERROR] app.py - 详细错误:\n{traceback.format_exc()}")
    raise


class NKUGradesApp:
    """NKU成绩查询主应用类"""

    def __init__(self, page: ft.Page):
        print("[DEBUG] NKUGradesApp.__init__ - 开始初始化")

        try:
            self.page = page
            self.current_page_index = 0
            print("[DEBUG] NKUGradesApp - 基本属性设置完成")

            # 应用状态（在页面间共享）
            self.app_state = {
                "logged_in": False,
                "auth": None,
                "semesters": [],
            }
            print("[DEBUG] NKUGradesApp - 应用状态初始化完成")

            # 配置页面
            self.page.title = "NKU成绩查询"
            print("[DEBUG] NKUGradesApp - 页面标题设置完成")

            self.page.theme = get_app_theme()
            print("[DEBUG] NKUGradesApp - 主题设置完成")

            # 设置中文字体（Windows 用微软雅黑，其他平台用系统默认）
            import platform
            print(f"[DEBUG] NKUGradesApp - 平台: {platform.system()}")
            if platform.system() == "Windows":
                self.page.theme.font_family = "Microsoft YaHei"
                print("[DEBUG] NKUGradesApp - 字体设置为微软雅黑")

            self.page.padding = 0
            print("[DEBUG] NKUGradesApp - padding 设置完成")

            # 仅在桌面平台设置窗口大小（Android 上不支持 window 属性）
            if hasattr(self.page, "window") and self.page.window is not None:
                try:
                    self.page.window.width = 400
                    self.page.window.height = 700
                    self.page.window.resizable = True
                    print("[DEBUG] NKUGradesApp - 窗口大小设置完成")
                except Exception as e:
                    print(f"[DEBUG] NKUGradesApp - 窗口设置失败（正常，Android平台）: {e}")
            else:
                print("[DEBUG] NKUGradesApp - 无窗口属性（移动平台）")

        except Exception as e:
            print(f"[ERROR] NKUGradesApp.__init__ - 初始化失败: {e}")
            print(f"[ERROR] 详细错误:\n{traceback.format_exc()}")
            raise

        # 创建页面实例
        try:
            print("[DEBUG] NKUGradesApp - 正在创建 HomePage...")
            self.home_page = HomePage(self.app_state)
            print("[DEBUG] NKUGradesApp - HomePage 创建成功")

            print("[DEBUG] NKUGradesApp - 正在创建 QueryPage...")
            self.query_page = QueryPage(self.app_state)
            print("[DEBUG] NKUGradesApp - QueryPage 创建成功")

            print("[DEBUG] NKUGradesApp - 正在创建 MonitorPage...")
            self.monitor_page = MonitorPage(self.app_state)
            print("[DEBUG] NKUGradesApp - MonitorPage 创建成功")

            print("[DEBUG] NKUGradesApp - 正在创建 SettingsPage...")
            self.settings_page = SettingsPage(self.app_state)
            print("[DEBUG] NKUGradesApp - SettingsPage 创建成功")

        except Exception as e:
            print(f"[ERROR] NKUGradesApp - 页面创建失败: {e}")
            print(f"[ERROR] 详细错误:\n{traceback.format_exc()}")
            raise

        # 检查是否已保存账号密码，决定启动页面
        try:
            print("[DEBUG] NKUGradesApp - 正在加载数据库...")
            from ..data.database import get_db
            db = get_db()
            print("[DEBUG] NKUGradesApp - 数据库加载成功")

            print("[DEBUG] NKUGradesApp - 正在读取配置...")
            username = db.get_config("username")
            password = db.get_config("password")
            print(f"[DEBUG] NKUGradesApp - 配置读取完成，username存在: {bool(username)}")

        except Exception as e:
            print(f"[ERROR] NKUGradesApp - 数据库/配置读取失败: {e}")
            print(f"[ERROR] 详细错误:\n{traceback.format_exc()}")
            # 如果数据库失败，使用默认值
            username = None
            password = None

        # 如果未登录，默认打开设置页；否则打开首页
        try:
            if not username or not password:
                initial_index = 3  # 设置页
                initial_content = self.settings_page
                print("[DEBUG] NKUGradesApp - 未登录，显示设置页")
            else:
                initial_index = 0  # 首页
                initial_content = self.home_page
                print("[DEBUG] NKUGradesApp - 已登录，显示首页")
                # 自动登录（后台线程）
                import threading
                threading.Thread(target=self._auto_login, args=(username, password), daemon=True).start()
                print("[DEBUG] NKUGradesApp - 自动登录线程已启动")

            # 创建页面容器
            print("[DEBUG] NKUGradesApp - 正在创建页面容器...")
            self.page_container = ft.Container(
                content=initial_content,
                expand=True,
            )
            print("[DEBUG] NKUGradesApp - 页面容器创建成功")

            # 创建底部导航栏
            print("[DEBUG] NKUGradesApp - 正在创建底部导航栏...")
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
            print("[DEBUG] NKUGradesApp - 底部导航栏创建成功")

            # 构建页面布局
            print("[DEBUG] NKUGradesApp - 正在构建页面布局...")
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
            print("[DEBUG] NKUGradesApp - 页面布局添加成功")
            print("[DEBUG] NKUGradesApp - 初始化完成！")

        except Exception as e:
            print(f"[ERROR] NKUGradesApp - UI构建失败: {e}")
            print(f"[ERROR] 详细错误:\n{traceback.format_exc()}")
            raise

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
    print("[DEBUG] main() - 开始创建 NKUGradesApp")
    try:
        NKUGradesApp(page)
        print("[DEBUG] main() - NKUGradesApp 创建成功")
    except Exception as e:
        print(f"[ERROR] main() - 创建失败: {e}")
        import traceback
        print(f"[ERROR] 详细错误:\n{traceback.format_exc()}")
        # 显示错误信息给用户
        page.add(ft.Text(f"启动失败: {str(e)}", color=ft.colors.RED))
        raise

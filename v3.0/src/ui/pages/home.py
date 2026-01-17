"""
NKU成绩查询 v3.0 - 首页
概览仪表盘
"""

import flet as ft
from ...data.database import get_db


class HomePage(ft.Container):
    """首页类"""

    def __init__(self, app_state):
        super().__init__()
        self.app_state = app_state
        self.db = get_db()

        # 登录状态卡片
        self.login_status_card = self._create_login_status_card()

        # 统计卡片
        self.stats_card = self._create_stats_card()

        # 快捷操作
        self.quick_actions = self._create_quick_actions()

        # 最近成绩
        self.recent_grades_section = ft.Column([], spacing=10)

        # 构建UI
        self.content = ft.Column(
            [
                ft.Container(height=10),
                ft.Text("NKU 成绩查询", size=24, weight=ft.FontWeight.W_600),
                ft.Container(height=15),
                self.login_status_card,
                ft.Container(height=15),
                self.stats_card,
                ft.Container(height=15),
                self.quick_actions,
                ft.Container(height=15),
                ft.Text("最近查询", size=18, weight=ft.FontWeight.W_500),
                ft.Container(height=10),
                self.recent_grades_section,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
        )
        self.alignment = ft.alignment.top_center
        self.expand = True
        self.padding = 20

    def _create_login_status_card(self):
        """创建登录状态卡片"""
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.icons.ACCOUNT_CIRCLE, size=40, color=ft.colors.BLUE),
                    ft.Column(
                        [
                            ft.Text("账号状态", size=12, color=ft.colors.GREY_600),
                            ft.Text("未登录", size=16, weight=ft.FontWeight.W_500, color=ft.colors.GREY_700),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                ],
                spacing=15,
            ),
            bgcolor=ft.colors.SURFACE_VARIANT,
            border_radius=12,
            padding=15,
            width=350,
        )

    def _create_stats_card(self):
        """创建统计卡片"""
        return ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text("0", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.PRIMARY),
                            ft.Text("总课程", size=12, color=ft.colors.GREY_600),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=True,
                    ),
                    ft.VerticalDivider(width=1),
                    ft.Column(
                        [
                            ft.Text("0.0", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.PRIMARY),
                            ft.Text("总学分", size=12, color=ft.colors.GREY_600),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=True,
                    ),
                    ft.VerticalDivider(width=1),
                    ft.Column(
                        [
                            ft.Text("0.00", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.PRIMARY),
                            ft.Text("平均绩点", size=12, color=ft.colors.GREY_600),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=True,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_AROUND,
            ),
            bgcolor=ft.colors.SURFACE_VARIANT,
            border_radius=12,
            padding=20,
            width=350,
        )

    def _create_quick_actions(self):
        """创建快捷操作按钮"""
        return ft.Column(
            [
                ft.ElevatedButton(
                    "刷新统计数据",
                    icon=ft.icons.REFRESH,
                    on_click=self.on_refresh_click,
                    width=300,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def on_page_show(self):
        """页面显示时调用"""
        self._update_ui()

    def on_refresh_click(self, e):
        """刷新统计数据"""
        self._update_ui()

    def _update_ui(self):
        """更新UI"""
        # 更新登录状态
        logged_in = self.app_state.get("logged_in", False)
        username = self.db.get_config("username")

        login_status_content = self.login_status_card.content
        if logged_in and username:
            login_status_content.controls[0].color = ft.colors.GREEN
            login_status_content.controls[1].controls[1].value = f"{username} (已登录)"
            login_status_content.controls[1].controls[1].color = ft.colors.GREEN
        else:
            login_status_content.controls[0].color = ft.colors.GREY
            login_status_content.controls[1].controls[1].value = "未登录"
            login_status_content.controls[1].controls[1].color = ft.colors.GREY_700

        # 更新统计信息
        all_grades = self.db.get_grades()
        total_courses = len(all_grades)
        total_credits = sum(g.credits for g in all_grades)
        gpas = [g.gpa for g in all_grades if g.gpa is not None]
        avg_gpa = sum(gpas) / len(gpas) if gpas else 0.0

        stats_content = self.stats_card.content
        stats_content.controls[0].controls[0].value = str(total_courses)
        stats_content.controls[2].controls[0].value = f"{total_credits:.1f}"
        stats_content.controls[4].controls[0].value = f"{avg_gpa:.2f}"

        # 更新最近成绩（显示最近5门）
        self.recent_grades_section.controls.clear()
        if all_grades:
            # 按查询时间降序排列
            sorted_grades = sorted(all_grades, key=lambda g: g.query_time or "", reverse=True)[:5]

            for grade in sorted_grades:
                from ..theme import get_grade_color
                grade_color = get_grade_color(grade.grade, grade.grade_type)

                card = ft.Container(
                    content=ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(grade.course_name, size=14, weight=ft.FontWeight.W_500),
                                    ft.Text(f"{grade.semester_name} | {grade.credits}学分", size=11, color=ft.colors.GREY_600),
                                ],
                                spacing=3,
                                expand=True,
                            ),
                            ft.Text(grade.grade, size=16, weight=ft.FontWeight.BOLD, color=grade_color),
                        ],
                    ),
                    bgcolor=ft.colors.SURFACE_VARIANT,
                    border_radius=10,
                    padding=12,
                    width=350,
                )
                self.recent_grades_section.controls.append(card)
        else:
            self.recent_grades_section.controls.append(
                ft.Text("暂无成绩数据", size=14, color=ft.colors.GREY_600)
            )

        # 只有在page存在时才update
        if hasattr(self, 'page') and self.page:
            self.update()


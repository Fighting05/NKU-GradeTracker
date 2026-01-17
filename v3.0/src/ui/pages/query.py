"""
NKU成绩查询 v3.0 - 查询页
成绩查询和展示
"""

import flet as ft
from ...data.database import get_db
from ...ui.theme import get_grade_color


class QueryPage(ft.Container):
    """查询页类"""

    def __init__(self, app_state):
        super().__init__()
        self.app_state = app_state
        self.db = get_db()

        # 学期选择下拉框
        self.semester_dropdown = ft.Dropdown(
            label="选择学期",
            width=190,
            text_size=14,
            on_change=self.on_semester_change,
        )

        # 查询按钮
        self.query_btn = ft.ElevatedButton(
            "查询成绩",
            on_click=self.on_query_click,
            width=145,
        )

        # 查看所有历史成绩按钮
        self.view_all_btn = ft.OutlinedButton(
            "查看历史",
            on_click=self.on_view_all_click,
            width=145,
            icon=ft.icons.HISTORY,
        )

        # 状态文本
        self.status_text = ft.Text("", size=12, color=ft.colors.GREY_600)

        # 成绩列表容器
        self.grades_list = ft.Column([], scroll=ft.ScrollMode.AUTO, spacing=10)

        # 统计信息
        self.stats_text = ft.Text("", size=14, color=ft.colors.GREY_700)

        # 构建UI
        self.content = ft.Column(
            [
                ft.Container(height=10),
                ft.Text("成绩查询", size=24, weight=ft.FontWeight.W_600),
                ft.Container(height=15),
                ft.Row(
                    [self.semester_dropdown, self.view_all_btn],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10,
                ),
                ft.Container(height=10),
                self.query_btn,
                ft.Container(height=10),
                self.status_text,
                ft.Container(height=10),
                self.stats_text,
                ft.Container(height=10),
                self.grades_list,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
        )
        self.alignment = ft.alignment.top_center
        self.expand = True
        self.padding = 20

    def on_page_show(self):
        """页面显示时调用"""
        self._update_semester_list()

    def _update_semester_list(self):
        """更新学期列表"""
        if not self.app_state.get("logged_in"):
            self.semester_dropdown.options = []
            self.semester_dropdown.hint_text = "请先在设置页登录"
            self.semester_dropdown.disabled = True
            self.query_btn.disabled = True
        else:
            semesters = self.app_state.get("semesters", [])
            self.semester_dropdown.options = [
                ft.dropdown.Option(key=sem.id, text=sem.display_name)
                for sem in semesters
            ]
            self.semester_dropdown.disabled = False
            self.query_btn.disabled = False

            if semesters:
                self.semester_dropdown.value = semesters[0].id

        # 只有在page存在时才update
        if hasattr(self, 'page') and self.page:
            self.update()

    def on_semester_change(self, e):
        """学期选择变化"""
        pass

    def on_view_all_click(self, e):
        """查看所有历史成绩"""
        all_grades = self.db.get_grades()

        if not all_grades:
            self.status_text.value = "暂无历史成绩"
            self.status_text.color = ft.colors.ORANGE
            self.update()
            return

        # 显示所有历史成绩
        self.semester_dropdown.value = None
        self._display_grades(all_grades)
        self.status_text.value = f"显示所有历史成绩（共 {len(all_grades)} 门课程）"
        self.status_text.color = ft.colors.BLUE
        self.update()

    def on_query_click(self, e):
        """查询按钮点击"""
        if not self.app_state.get("logged_in"):
            self.status_text.value = "请先登录"
            self.status_text.color = ft.colors.RED
            self.update()
            return

        semester_id = self.semester_dropdown.value
        if not semester_id:
            self.status_text.value = "请选择学期"
            self.status_text.color = ft.colors.RED
            self.update()
            return

        # 找到学期名称
        semesters = self.app_state.get("semesters", [])
        semester_name = next(
            (s.display_name for s in semesters if s.id == semester_id),
            semester_id
        )

        # 更新状态
        self.status_text.value = f"正在查询 {semester_name}..."
        self.status_text.color = ft.colors.BLUE
        self.query_btn.disabled = True
        self.update()

        # 后台查询
        import threading
        threading.Thread(
            target=self._do_query,
            args=(semester_id, semester_name),
            daemon=True
        ).start()

    def _do_query(self, semester_id: str, semester_name: str):
        """执行查询（后台线程）"""
        from ...core.grades import GradeQueryer

        try:
            auth = self.app_state.get("auth")
            if not auth:
                self._update_status("认证信息丢失，请重新登录", ft.colors.RED)
                return

            # 查询成绩
            queryer = GradeQueryer(auth.session, auth.base_url, log_callback=self._log)
            grades = queryer.query_grades(semester_id, semester_name)

            if not grades:
                self._update_status("未找到成绩数据", ft.colors.ORANGE)
                return

            # 保存到数据库
            self.db.save_grades(grades)

            # 更新UI
            self._display_grades(grades)
            self._update_status(f"查询成功！共 {len(grades)} 门课程", ft.colors.GREEN)

            # 询问是否推送
            self._ask_push_notification(grades, semester_name)

        except Exception as e:
            self._update_status(f"查询出错: {str(e)}", ft.colors.RED)

    def _display_grades(self, grades):
        """显示成绩列表"""
        async def update_ui():
            self.grades_list.controls.clear()

            # 计算统计信息
            total_courses = len(grades)
            total_credits = sum(g.credits for g in grades)
            gpas = [g.gpa for g in grades if g.gpa is not None]
            avg_gpa = sum(gpas) / len(gpas) if gpas else 0

            self.stats_text.value = f"课程数: {total_courses} | 总学分: {total_credits:.1f} | 平均绩点: {avg_gpa:.2f}"

            # 显示成绩卡片
            for grade in grades:
                card = self._create_grade_card(grade)
                self.grades_list.controls.append(card)

            self.query_btn.disabled = False
            self.update()

        if hasattr(self, 'page') and self.page:
            self.page.run_task(update_ui)

    def _create_grade_card(self, grade):
        """创建成绩卡片"""
        grade_color = get_grade_color(grade.grade, grade.grade_type)

        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                grade.course_name,
                                size=16,
                                weight=ft.FontWeight.W_600,
                                expand=True,
                            ),
                            ft.Text(
                                grade.grade,
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color=grade_color,
                            ),
                        ],
                    ),
                    ft.Text(
                        f"{grade.course_code} | {grade.course_type} | {grade.credits}学分",
                        size=12,
                        color=ft.colors.GREY_600,
                    ),
                    ft.Text(
                        f"绩点: {grade.gpa if grade.gpa else 'N/A'} | {grade.grade_type}",
                        size=11,
                        color=ft.colors.GREY_500,
                    ) if grade.gpa else ft.Container(),
                ],
                spacing=5,
            ),
            bgcolor=ft.colors.SURFACE_VARIANT,
            border_radius=12,
            padding=15,
            width=350,
        )

    def _log(self, message: str):
        """日志回调"""
        print(f"[Query] {message}")

    def _ask_push_notification(self, grades, semester_name):
        """询问是否推送查询结果"""
        async def show_dialog():
            dialog = ft.AlertDialog(
                title=ft.Text("推送查询结果"),
                content=ft.Text(f"是否将 {semester_name} 的 {len(grades)} 门成绩推送到通知？"),
                actions=[
                    ft.TextButton("取消", on_click=lambda _: self.page.close(dialog)),
                    ft.TextButton("推送", on_click=lambda _: (self._send_push_notification(grades, semester_name), self.page.close(dialog))),
                ],
            )
            self.page.open(dialog)

        if hasattr(self, 'page') and self.page:
            self.page.run_task(show_dialog)

    def _send_push_notification(self, grades, semester_name):
        """发送查询结果推送"""
        from ...services.pushplus import PushPlusService
        from ...services.email import build_grade_change_html

        try:
            pushplus_token = self.db.get_config("pushplus_token")

            if pushplus_token:
                title = f"NKU 成绩查询 - {semester_name}"
                html_content = build_grade_change_html(grades, [])

                service = PushPlusService(pushplus_token)
                success = service.send_notification(title, html_content)

                if success:
                    print(f"[Query] PushPlus 推送成功")
                else:
                    print(f"[Query] PushPlus 推送失败")
            else:
                print("[Query] 未配置PushPlus Token")

        except Exception as e:
            print(f"[Query] 推送出错: {e}")

    def _update_status(self, message: str, color):
        """更新状态"""
        async def update_ui():
            self.status_text.value = message
            self.status_text.color = color
            self.query_btn.disabled = False
            self.update()

        if hasattr(self, 'page') and self.page:
            self.page.run_task(update_ui)

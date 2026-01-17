"""
NKU成绩查询 v3.0 - 监控页
成绩监控和日志
"""

import flet as ft
import threading
import time
from ...data.database import get_db
from ...core.monitor import GradeMonitor


class MonitorPage(ft.Container):
    """监控页类"""

    def __init__(self, app_state):
        super().__init__()
        self.app_state = app_state
        self.db = get_db()
        self.monitor = None
        self.countdown_timer = None

        # 学期选择（单选下拉框）
        self.semester_dropdown = ft.Dropdown(
            label="选择监控学期",
            width=300,
            text_size=14,
        )

        # 监控间隔输入
        self.interval_field = ft.TextField(
            label="检查间隔（分钟）",
            value="30",
            width=300,
            text_size=14,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        # 监控状态文本
        self.status_text = ft.Text("监控未启动", size=14, color=ft.colors.GREY_600)

        # 倒计时文本
        self.countdown_text = ft.Text("", size=12, color=ft.colors.GREY_600)

        # 实时日志输出框
        self.realtime_log = ft.TextField(
            multiline=True,
            read_only=True,
            min_lines=10,
            max_lines=10,
            width=350,
            text_size=11,
            border_color=ft.colors.GREY_400,
        )

        # 开始/停止按钮
        self.toggle_btn = ft.ElevatedButton(
            "开始监控",
            on_click=self.on_toggle_click,
            width=300,
            icon=ft.icons.PLAY_ARROW,
        )

        # 日志列表
        self.logs_list = ft.Column([], scroll=ft.ScrollMode.AUTO, spacing=8)

        # 构建UI
        self.content = ft.Column(
            [
                ft.Container(height=10),
                ft.Text("成绩监控", size=24, weight=ft.FontWeight.W_600),
                ft.Container(height=15),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("监控设置", size=16, weight=ft.FontWeight.W_500),
                            ft.Container(height=10),
                            self.semester_dropdown,
                            ft.Container(height=10),
                            self.interval_field,
                            ft.Container(height=10),
                            self.toggle_btn,
                            ft.Container(height=10),
                            self.status_text,
                            self.countdown_text,
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    bgcolor=ft.colors.SURFACE_VARIANT,
                    border_radius=12,
                    padding=15,
                    width=350,
                ),
                ft.Container(height=15),
                ft.Text("实时日志", size=18, weight=ft.FontWeight.W_500),
                ft.Container(height=10),
                self.realtime_log,
                ft.Container(height=15),
                ft.Text("历史日志", size=18, weight=ft.FontWeight.W_500),
                ft.Container(height=10),
                self.logs_list,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
        )
        self.alignment = ft.alignment.top_center
        self.expand = True
        self.padding = 20

    def on_page_show(self):
        """页面显示时调用"""
        self._load_semesters()
        self._load_logs()

    def _load_semesters(self):
        """加载学期列表"""
        semesters = self.app_state.get("semesters", [])

        if not semesters:
            self.semester_dropdown.options = []
            self.semester_dropdown.hint_text = "请先在设置页登录"
            self.semester_dropdown.disabled = True
        else:
            self.semester_dropdown.options = [
                ft.dropdown.Option(key=sem.id, text=sem.display_name)
                for sem in semesters
            ]
            self.semester_dropdown.disabled = False

            # 默认选择第一个学期
            if semesters:
                self.semester_dropdown.value = semesters[0].id

        if hasattr(self, 'page') and self.page:
            self.update()

    def on_toggle_click(self, e):
        """开始/停止监控"""
        if not self.app_state.get("logged_in"):
            self.status_text.value = "请先登录"
            self.status_text.color = ft.colors.RED
            self.update()
            return

        if self.monitor and self.monitor.is_running():
            # 停止监控
            self.monitor.stop()
            self.toggle_btn.text = "开始监控"
            self.toggle_btn.icon = ft.icons.PLAY_ARROW
            self.status_text.value = "监控已停止"
            self.status_text.color = ft.colors.GREY_600
            self.countdown_text.value = ""
            self.interval_field.disabled = False
            self.update()
        else:
            # 开始监控
            try:
                interval = int(self.interval_field.value)
                if interval < 5:
                    self.status_text.value = "间隔不能小于5分钟"
                    self.status_text.color = ft.colors.RED
                    self.update()
                    return
            except:
                self.status_text.value = "请输入有效的数字"
                self.status_text.color = ft.colors.RED
                self.update()
                return

            auth = self.app_state.get("auth")
            all_semesters = self.app_state.get("semesters", [])

            if not auth or not all_semesters:
                self.status_text.value = "请先在设置页登录"
                self.status_text.color = ft.colors.RED
                self.update()
                return

            # 获取选中的学期
            semester_id = self.semester_dropdown.value
            if not semester_id:
                self.status_text.value = "请选择监控学期"
                self.status_text.color = ft.colors.RED
                self.update()
                return

            # 找到对应的学期对象
            selected_semester = None
            for sem in all_semesters:
                if sem.id == semester_id:
                    selected_semester = sem
                    break

            if not selected_semester:
                self.status_text.value = "学期信息错误"
                self.status_text.color = ft.colors.RED
                self.update()
                return

            # 创建监控器（只监控一个学期）
            self.monitor = GradeMonitor(
                auth=auth,
                semesters=[selected_semester],
                interval_minutes=interval,
                log_callback=self._log,
                change_callback=self._on_grade_change
            )

            self.monitor.start()
            self.toggle_btn.text = "停止监控"
            self.toggle_btn.icon = ft.icons.STOP
            self.status_text.value = f"监控运行中（每 {interval} 分钟检查一次）"
            self.status_text.color = ft.colors.GREEN
            self.interval_field.disabled = True
            self.update()

            # 启动倒计时更新线程
            if self.countdown_timer:
                self.countdown_timer = None
            self.countdown_timer = threading.Thread(target=self._update_countdown, daemon=True)
            self.countdown_timer.start()

    def _update_countdown(self):
        """更新倒计时显示"""
        while self.monitor and self.monitor.is_running():
            countdown = self.monitor.get_countdown()
            minutes = countdown // 60
            seconds = countdown % 60

            async def update_ui():
                self.countdown_text.value = f"下次检查: {minutes} 分 {seconds} 秒后"
                self.update()

            if hasattr(self, 'page') and self.page:
                self.page.run_task(update_ui)

            time.sleep(1)

    def _log(self, message: str):
        """日志回调"""
        print(f"[Monitor] {message}")

        # 添加到实时日志框
        async def update_log():
            import datetime
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            log_line = f"[{timestamp}] {message}\n"

            # 追加到实时日志
            current_log = self.realtime_log.value or ""
            # 保留最近50行
            lines = (current_log + log_line).split('\n')
            if len(lines) > 50:
                lines = lines[-50:]
            self.realtime_log.value = '\n'.join(lines)

            self.update()

        if hasattr(self, 'page') and self.page:
            self.page.run_task(update_log)

    def _on_grade_change(self, new_courses, updated_courses):
        """成绩变化回调"""
        # 构建通知内容
        message_parts = []

        if new_courses:
            message_parts.append(f"新增 {len(new_courses)} 门课程:")
            for grade in new_courses[:5]:  # 最多显示5门
                message_parts.append(f"  - {grade.course_name}: {grade.grade}")

        if updated_courses:
            message_parts.append(f"更新 {len(updated_courses)} 门课程:")
            for item in updated_courses[:5]:
                old_g = item['old']
                new_g = item['new']
                message_parts.append(f"  - {new_g.course_name}: {old_g.grade} → {new_g.grade}")

        message = "\n".join(message_parts)
        print(f"[成绩变化]\n{message}")

        # 发送邮件通知
        self._send_email_notification(new_courses, updated_courses)

    def _send_email_notification(self, new_courses, updated_courses):
        """发送推送通知"""
        try:
            pushplus_token = self.db.get_config("pushplus_token")

            if pushplus_token:
                self._send_pushplus(new_courses, updated_courses, pushplus_token)
            else:
                print("[Monitor] 未配置PushPlus Token，跳过推送")

        except Exception as e:
            print(f"[Monitor] 推送出错: {e}")

    def _send_pushplus(self, new_courses, updated_courses, token):
        """发送 PushPlus 推送"""
        try:
            from ...services.pushplus import PushPlusService
            from ...services.email import build_grade_change_html

            title = f"NKU 成绩变化 - 新增{len(new_courses)}门，更新{len(updated_courses)}门"
            html_content = build_grade_change_html(new_courses, updated_courses)

            service = PushPlusService(token)
            success = service.send_notification(title, html_content)

            if success:
                print(f"[Monitor] PushPlus 推送成功")
            else:
                print(f"[Monitor] PushPlus 推送失败")

        except Exception as e:
            print(f"[Monitor] PushPlus 推送出错: {e}")

    def _load_logs(self):
        """加载监控日志"""
        self.logs_list.controls.clear()

        logs = self.db.get_monitor_logs(limit=20)

        if logs:
            for log in logs:
                status_color = ft.colors.GREEN if log['status'] == 'success' else ft.colors.RED
                status_icon = ft.icons.CHECK_CIRCLE if log['status'] == 'success' else ft.icons.ERROR

                # 格式化时间显示（只显示时分秒）
                try:
                    import datetime
                    dt = datetime.datetime.fromisoformat(log['check_time'])
                    time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    time_str = log['check_time'][:19] if len(log['check_time']) >= 19 else log['check_time']

                card = ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(status_icon, size=20, color=status_color),
                            ft.Column(
                                [
                                    ft.Text(time_str, size=11, color=ft.colors.GREY_600),
                                    ft.Text(log['message'], size=12, weight=ft.FontWeight.W_400),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                        ],
                        spacing=10,
                    ),
                    bgcolor=ft.colors.SURFACE_VARIANT,
                    border_radius=8,
                    padding=10,
                    width=350,
                )
                self.logs_list.controls.append(card)
        else:
            self.logs_list.controls.append(
                ft.Text("暂无监控记录", size=14, color=ft.colors.GREY_600)
            )

        if hasattr(self, 'page') and self.page:
            self.update()

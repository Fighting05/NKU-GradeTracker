"""
NKU成绩查询 v3.0 - 监控功能
后台定时检查成绩变化
"""

import time
import threading
from typing import List, Optional, Callable, Dict
from ..data.models import Grade
from ..data.database import get_db
from .grades import GradeQueryer
from .semester import SemesterManager


class GradeMonitor:
    """成绩监控器"""

    def __init__(self, auth, semesters: List, interval_minutes: int = 30,
                 log_callback: Optional[Callable] = None,
                 change_callback: Optional[Callable] = None):
        """
        初始化监控器

        Args:
            auth: 认证对象
            semesters: 学期列表
            interval_minutes: 检查间隔（分钟），最小5分钟
            log_callback: 日志回调
            change_callback: 成绩变化回调，参数为(新增列表, 更新列表)
        """
        self.auth = auth
        self.semesters = semesters
        self.interval_minutes = max(5, interval_minutes)  # 最小5分钟
        self.log_callback = log_callback
        self.change_callback = change_callback

        self.db = get_db()
        self.running = False
        self.thread = None
        self.countdown_seconds = 0

    def log(self, message: str):
        """日志输出"""
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def start(self):
        """启动监控"""
        if self.running:
            self.log("监控已在运行中")
            return

        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        self.log(f"监控已启动，检查间隔: {self.interval_minutes} 分钟")

    def stop(self):
        """停止监控"""
        if not self.running:
            self.log("监控未运行")
            return

        self.running = False
        self.log("监控已停止")

    def is_running(self) -> bool:
        """是否正在运行"""
        return self.running

    def get_countdown(self) -> int:
        """获取倒计时秒数"""
        return self.countdown_seconds

    def _monitor_loop(self):
        """监控主循环"""
        while self.running:
            try:
                # 执行一次检查
                self._check_grades()

                # 倒计时等待
                self.countdown_seconds = self.interval_minutes * 60
                while self.running and self.countdown_seconds > 0:
                    time.sleep(1)
                    self.countdown_seconds -= 1

            except Exception as e:
                self.log(f"监控出错: {e}")
                # 出错后等待1分钟再重试
                time.sleep(60)

    def _check_grades(self):
        """检查成绩变化"""
        self.log("开始检查成绩...")

        try:
            # 重新创建Session防止过期
            from .auth import WebVPNAuthenticator
            username = self.db.get_config("username")
            password = self.db.get_config("password")

            if not username or not password:
                self.log("未找到账号配置，停止监控")
                self.stop()
                return

            # 重新登录
            auth = WebVPNAuthenticator(username, password, log_callback=lambda msg: print(f"[Monitor-Auth] {msg}"))
            if not auth.login() or not auth.access_eamis():
                self.log("登录失败，跳过本次检查")
                return

            # 查询所有学期成绩
            queryer = GradeQueryer(auth.session, auth.base_url, log_callback=lambda msg: print(f"[Monitor-Query] {msg}"))

            all_new_grades = []
            for semester in self.semesters:
                grades = queryer.query_grades(semester.id, semester.display_name)
                all_new_grades.extend(grades)

            # 对比数据库中的成绩
            old_grades = self.db.get_grades()
            new_courses, updated_courses = self._compare_grades(old_grades, all_new_grades)

            # 保存新成绩
            if all_new_grades:
                self.db.save_grades(all_new_grades)

            # 触发变化回调
            if new_courses or updated_courses:
                self.log(f"发现变化: 新增 {len(new_courses)} 门，更新 {len(updated_courses)} 门")
                if self.change_callback:
                    self.change_callback(new_courses, updated_courses)
            else:
                self.log("未发现成绩变化")

            # 记录监控日志
            self.db.save_monitor_log(
                status="success",
                new_count=len(new_courses),
                update_count=len(updated_courses),
                message=f"检查完成，新增{len(new_courses)}门，更新{len(updated_courses)}门"
            )

        except Exception as e:
            self.log(f"检查出错: {e}")
            self.db.save_monitor_log(
                status="failed",
                new_count=0,
                update_count=0,
                message=str(e)
            )

    def _compare_grades(self, old_grades: List[Grade], new_grades: List[Grade]):
        """
        对比成绩，找出新增和更新的课程

        Returns:
            (新增列表, 更新列表)
        """
        # 构建旧成绩字典 {(semester_id, course_code): grade}
        old_dict = {(g.semester_id, g.course_code): g for g in old_grades}

        new_courses = []
        updated_courses = []

        for new_grade in new_grades:
            key = (new_grade.semester_id, new_grade.course_code)
            old_grade = old_dict.get(key)

            if not old_grade:
                # 新增课程
                new_courses.append(new_grade)
            else:
                # 检查是否更新（成绩或绩点变化）
                if (old_grade.grade != new_grade.grade or
                    old_grade.gpa != new_grade.gpa):
                    updated_courses.append({
                        'old': old_grade,
                        'new': new_grade
                    })

        return new_courses, updated_courses

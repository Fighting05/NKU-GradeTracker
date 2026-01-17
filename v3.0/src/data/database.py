"""
NKU成绩查询 v3.0 - SQLite 数据库操作
"""

import sqlite3
from typing import List, Optional
from pathlib import Path
from .storage import get_database_path
from .models import Grade, Config


class Database:
    """数据库管理类"""

    def __init__(self, db_path: Optional[Path] = None):
        """
        初始化数据库连接

        Args:
            db_path: 数据库文件路径，不指定则使用默认路径
        """
        self.db_path = db_path or get_database_path()
        self._init_database()

    def _init_database(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 配置表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        # 成绩历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                semester_id TEXT NOT NULL,
                semester_name TEXT NOT NULL,
                course_code TEXT NOT NULL,
                course_name TEXT NOT NULL,
                course_type TEXT,
                credits REAL,
                grade_type TEXT,
                grade TEXT,
                gpa REAL,
                score REAL,
                query_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(semester_id, course_code)
            )
        """)

        # 监控日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monitor_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT,
                new_count INTEGER DEFAULT 0,
                update_count INTEGER DEFAULT 0,
                message TEXT
            )
        """)

        conn.commit()
        conn.close()

    def save_config(self, key: str, value: str):
        """保存配置"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
            (key, value)
        )
        conn.commit()
        conn.close()

    def get_config(self, key: str) -> Optional[str]:
        """获取配置"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def save_grades(self, grades: List[Grade]):
        """
        保存成绩列表

        Args:
            grades: 成绩列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for grade in grades:
            cursor.execute("""
                INSERT OR REPLACE INTO grades
                (semester_id, semester_name, course_code, course_name,
                 course_type, credits, grade_type, grade, gpa, score, query_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                grade.semester_id,
                grade.semester_name,
                grade.course_code,
                grade.course_name,
                grade.course_type,
                grade.credits,
                grade.grade_type,
                grade.grade,
                grade.gpa,
                grade.score,
                grade.query_time
            ))

        conn.commit()
        conn.close()

    def get_grades(self, semester_id: Optional[str] = None) -> List[Grade]:
        """
        获取成绩列表

        Args:
            semester_id: 学期ID，不指定则返回所有成绩

        Returns:
            成绩列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if semester_id:
            cursor.execute("""
                SELECT semester_id, semester_name, course_code, course_name,
                       course_type, credits, grade_type, grade, gpa, score, query_time
                FROM grades
                WHERE semester_id = ?
                ORDER BY query_time DESC
            """, (semester_id,))
        else:
            cursor.execute("""
                SELECT semester_id, semester_name, course_code, course_name,
                       course_type, credits, grade_type, grade, gpa, score, query_time
                FROM grades
                ORDER BY query_time DESC
            """)

        rows = cursor.fetchall()
        conn.close()

        grades = []
        for row in rows:
            grades.append(Grade(
                semester_id=row[0],
                semester_name=row[1],
                course_code=row[2],
                course_name=row[3],
                course_type=row[4],
                credits=row[5],
                grade_type=row[6],
                grade=row[7],
                gpa=row[8],
                score=row[9],
                query_time=row[10]
            ))

        return grades

    def clear_all_data(self):
        """清理所有数据（配置、成绩、日志）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 清空所有表
        cursor.execute("DELETE FROM config")
        cursor.execute("DELETE FROM grades")
        cursor.execute("DELETE FROM monitor_logs")

        conn.commit()
        conn.close()

    def clear_grades_only(self):
        """只清理成绩数据，保留配置"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM grades")
        cursor.execute("DELETE FROM monitor_logs")

        conn.commit()
        conn.close()

    def save_monitor_log(self, status: str, new_count: int, update_count: int, message: str):
        """保存监控日志"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO monitor_logs (status, new_count, update_count, message)
            VALUES (?, ?, ?, ?)
        """, (status, new_count, update_count, message))

        conn.commit()
        conn.close()

    def get_monitor_logs(self, limit: int = 50) -> List:
        """获取监控日志"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT check_time, status, new_count, update_count, message
            FROM monitor_logs
            ORDER BY check_time DESC
            LIMIT ?
        """, (limit,))

        logs = []
        for row in cursor.fetchall():
            logs.append({
                'check_time': row[0],
                'status': row[1],
                'new_count': row[2],
                'update_count': row[3],
                'message': row[4]
            })

        conn.close()
        return logs


# 全局数据库实例
_db_instance = None


def get_db() -> Database:
    """获取全局数据库实例（单例模式）"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance

"""
NKU成绩查询 v3.0 - 学期管理
从 nku_grades.py 移植（简化版）
"""

import re
from typing import List, Optional, Callable
from ..data.models import Semester


class SemesterManager:
    """学期管理器"""

    def __init__(self, session, base_url: str, log_callback: Optional[Callable] = None):
        """
        初始化学期管理器

        Args:
            session: requests.Session 对象
            base_url: WebVPN 基础URL
            log_callback: 日志回调函数
        """
        self.session = session
        self.base_url = base_url
        self.log_callback = log_callback

    def log(self, message: str):
        """日志输出"""
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def get_semesters(self) -> List[Semester]:
        """
        获取学期列表

        Returns:
            学期列表
        """
        self.log("正在获取学期列表...")

        try:
            # 访问成绩页面获取 tagId
            person_url = f"{self.base_url}/https/77726476706e69737468656265737421f5f64c95347e6651700388a5d6502720dc08a5/eams/teach/grade/course/person.action"

            headers = {
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': f'{self.base_url}/https/77726476706e69737468656265737421f5f64c95347e6651700388a5d6502720dc08a5/eams/home.action'
            }

            self.session.headers.update(headers)
            response = self.session.get(person_url, params={'vpn-12-o2-eamis.nankai.edu.cn': ''})

            # 提取 tagId
            tag_id_match = re.search(r'semesterBar(\d+)Semester', response.text)
            if tag_id_match:
                tag_id = f"semesterBar{tag_id_match.group(1)}Semester"
                self.log(f"获取到 tagId")
            else:
                self.log("未能获取到 tagId，使用默认值")
                tag_id = "semesterBar4452416521Semester"

            # 调用 dataQuery.action 获取学期数据
            data_query_url = f"{self.base_url}/https/77726476706e69737468656265737421f5f64c95347e6651700388a5d6502720dc08a5/eams/dataQuery.action"

            data = {
                'tagId': tag_id,
                'dataType': 'semesterCalendar',
                'value': '4324',
                'empty': 'false'
            }

            headers = {
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': f'{self.base_url}/https/77726476706e69737468656265737421f5f64c95347e6651700388a5d6502720dc08a5/eams/home.action'
            }

            self.session.headers.update(headers)
            response = self.session.post(data_query_url, data=data, params={'vpn-12-o2-eamis.nankai.edu.cn': ''})

            if response.status_code == 200:
                self.log("成功获取学期数据")
                semesters = self._parse_semesters(response.text)
                if semesters:
                    self.log(f"找到 {len(semesters)} 个可用学期")
                    return semesters
                else:
                    self.log("解析学期数据失败，使用默认数据")
                    return self._get_default_semesters()
            else:
                self.log(f"获取学期数据失败，使用默认数据")
                return self._get_default_semesters()

        except Exception as e:
            self.log(f"获取学期数据时出错: {e}")
            return self._get_default_semesters()

    def _parse_semesters(self, response_text: str) -> Optional[List[Semester]]:
        """解析学期数据"""
        try:
            semesters_match = re.search(r'semesters:\s*({.*?})\s*,\s*yearIndex', response_text, re.DOTALL)
            if not semesters_match:
                return None

            semesters_text = semesters_match.group(1)
            semester_data = {}

            # 解析年度分组
            year_pattern = r'(y\d+):\s*\[(.*?)\]'
            year_matches = re.finditer(year_pattern, semesters_text, re.DOTALL)

            for year_match in year_matches:
                year_key = year_match.group(1)
                year_data_text = year_match.group(2)
                semester_list = []

                # 解析学期
                semester_pattern = r'\{id:(\d+),schoolYear:"([^"]+)",name:"([^"]+)"\}'
                semester_matches = re.finditer(semester_pattern, year_data_text)

                for sem_match in semester_matches:
                    semester_info = {
                        'id': int(sem_match.group(1)),
                        'schoolYear': sem_match.group(2),
                        'name': sem_match.group(3)
                    }
                    semester_list.append(semester_info)

                if semester_list:
                    semester_data[year_key] = semester_list

            # 格式化学期数据并统一排序
            formatted_semesters = []

            for year_key, semesters in semester_data.items():
                for semester in semesters:
                    semester_id = str(semester['id'])
                    # 只保留 4 位数 ID 的学期
                    if len(semester_id) == 4:
                        formatted_semesters.append(
                            Semester(
                                id=semester_id,
                                display_name=f"{semester['schoolYear']} 第{semester['name']}学期",
                                school_year=semester['schoolYear'],
                                term=semester['name']
                            )
                        )

            # 全局排序：按学年结束年份降序，再按学期降序
            def semester_sort_key(sem: Semester):
                # 提取学年结束年份，如 "2024-2025" -> 2025
                year_end = int(sem.school_year.split('-')[1])
                # 学期数
                term_num = int(sem.term)
                # 返回排序键：年份降序（负数），学期降序（负数）
                return (-year_end, -term_num)

            formatted_semesters.sort(key=semester_sort_key)
            return formatted_semesters

        except Exception as e:
            self.log(f"解析学期数据时出错: {e}")
            return None

    def _get_default_semesters(self) -> List[Semester]:
        """返回默认的学期数据"""
        return [
            Semester('4364', '2025-2026 第1学期', '2025-2026', '1'),
            Semester('4344', '2024-2025 第3学期', '2024-2025', '3'),
            Semester('4324', '2024-2025 第2学期', '2024-2025', '2'),
            Semester('4262', '2024-2025 第1学期', '2024-2025', '1'),
            Semester('4304', '2023-2024 第3学期', '2023-2024', '3'),
            Semester('4284', '2023-2024 第2学期', '2023-2024', '2'),
            Semester('4263', '2023-2024 第1学期', '2023-2024', '1'),
        ]

"""
NKU成绩查询 v3.0 - 成绩查询
从 nku_grades.py 移植（简化MVP版本）
"""

import re
import time
from typing import List, Optional, Callable
from bs4 import BeautifulSoup
from ..data.models import Grade


class GradeQueryer:
    """成绩查询器"""

    def __init__(self, session, base_url: str, log_callback: Optional[Callable] = None):
        """
        初始化成绩查询器

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

    def query_grades(self, semester_id: str, semester_name: str) -> List[Grade]:
        """
        查询指定学期的成绩

        Args:
            semester_id: 学期ID
            semester_name: 学期名称

        Returns:
            成绩列表
        """
        self.log(f"正在查询学期 {semester_name} 的成绩...")

        try:
            person_url = f"{self.base_url}/https/77726476706e69737468656265737421f5f64c95347e6651700388a5d6502720dc08a5/eams/teach/grade/course/person.action"

            headers = {
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': f'{self.base_url}/https/77726476706e69737468656265737421f5f64c95347e6651700388a5d6502720dc08a5/eams/home.action'
            }

            self.session.headers.update(headers)

            # 第1步：访问成绩页面
            data = {'project.id': '1', 'semester.id': semester_id}
            response = self.session.post(person_url, data=data, params={'vpn-12-o2-eamis.nankai.edu.cn': ''})

            # 提取 tagId
            tag_id_match = re.search(r'semesterBar(\d+)Semester', response.text)
            if not tag_id_match:
                self.log("未能获取到 tagId")
                return []

            tag_id = f"semesterBar{tag_id_match.group(1)}Semester"

            # 第2步：查询学期日历
            data_query_url = f"{self.base_url}/https/77726476706e69737468656265737421f5f64c95347e6651700388a5d6502720dc08a5/eams/dataQuery.action"
            data = {
                'tagId': tag_id,
                'dataType': 'semesterCalendar',
                'value': semester_id,
                'empty': 'false'
            }
            self.session.post(data_query_url, data=data, params={'vpn-12-o2-eamis.nankai.edu.cn': ''})

            # 第3步：查询实体ID
            data = {'entityId': '1'}
            self.session.post(data_query_url, data=data, params={'vpn-12-o2-eamis.nankai.edu.cn': ''})

            # 第4步：获取成绩
            search_url = f"{self.base_url}/https/77726476706e69737468656265737421f5f64c95347e6651700388a5d6502720dc08a5/eams/teach/grade/course/person!search.action"
            timestamp = int(time.time() * 1000)
            params = {
                'semesterId': semester_id,
                'projectType': '',
                '_': timestamp,
                'vpn-12-o2-eamis.nankai.edu.cn': ''
            }

            response = self.session.get(search_url, params=params)

            if response.status_code == 200:
                self.log("成功获取成绩数据")
                grades = self._parse_grades(response.text, semester_id, semester_name)
                self.log(f"找到 {len(grades)} 门课程")
                return grades
            else:
                self.log(f"获取成绩失败，状态码: {response.status_code}")
                return []

        except Exception as e:
            self.log(f"查询成绩时出错: {e}")
            return []

    def _parse_grades(self, html: str, semester_id: str, semester_name: str) -> List[Grade]:
        """解析成绩HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # 先尝试找grid表格
            table = soup.find('tbody', id=lambda x: x and 'grid' in x and '_data' in x)

            # 如果没找到，使用兜底逻辑：选择行数最多的tbody
            if not table:
                self.log("未找到grid表格，尝试其他方式...")
                all_tbodies = soup.find_all('tbody')
                self.log(f"找到 {len(all_tbodies)} 个tbody")

                if all_tbodies:
                    table = max(all_tbodies, key=lambda x: len(x.find_all('tr')))
                    self.log(f"选择包含 {len(table.find_all('tr'))} 行的tbody")
                else:
                    self.log("未找到任何表格")
                    return []

            grades = []
            rows = table.find_all('tr')

            self.log(f"找到 {len(rows)} 行成绩数据")

            for i, row in enumerate(rows):
                cells = row.find_all('td')

                if len(cells) < 8:
                    self.log(f"第{i+1}行列数不足({len(cells)}列)，跳过")
                    continue

                try:
                    # 正确的列索引（与原版一致）
                    course_code = cells[1].text.strip()
                    course_name = cells[3].text.strip()
                    course_type = cells[4].text.strip()
                    credits = float(cells[5].text.strip() or 0)
                    grade_text = cells[6].text.strip()
                    gpa_text = cells[7].text.strip()

                    # 判断成绩类型
                    grade_type, grade, gpa, score = self._parse_grade_info(grade_text, gpa_text)

                    grades.append(Grade(
                        semester_id=semester_id,
                        semester_name=semester_name,
                        course_code=course_code,
                        course_name=course_name,
                        course_type=course_type,
                        credits=credits,
                        grade_type=grade_type,
                        grade=grade,
                        gpa=gpa,
                        score=score
                    ))

                    self.log(f"解析: {course_name} - {grade}")

                except Exception as e:
                    self.log(f"解析第{i+1}行出错: {e}")
                    continue

            return grades

        except Exception as e:
            self.log(f"解析成绩数据时出错: {e}")
            return []

    def _parse_grade_info(self, grade_text: str, gpa_text: str):
        """解析成绩信息，判断成绩类型"""
        # 通过制：通过/不通过/合格/不合格
        if grade_text in ['通过', '不通过', '合格', '不合格']:
            return '通过制', grade_text, None, None

        # 等级制：A/A-/B+/B/B-/C+/C/C-/D/F
        if grade_text in ['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F']:
            try:
                gpa = float(gpa_text) if gpa_text and gpa_text not in ['', '--'] else None
            except:
                gpa = None
            return '等级制', grade_text, gpa, None

        # 百分制：数字成绩
        try:
            score = float(grade_text)
            gpa = self._score_to_gpa(score)
            return '百分制', f"{int(score)}分", gpa, score
        except:
            # 未知格式
            return '其他', grade_text, None, None

    def _score_to_gpa(self, score: float) -> float:
        """百分制成绩转换为绩点"""
        if score >= 90:
            return 4.0
        elif score >= 85:
            return 3.7
        elif score >= 82:
            return 3.3
        elif score >= 78:
            return 3.0
        elif score >= 75:
            return 2.7
        elif score >= 72:
            return 2.3
        elif score >= 68:
            return 2.0
        elif score >= 64:
            return 1.5
        elif score >= 60:
            return 1.0
        else:
            return 0.0

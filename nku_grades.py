"""
南开大学 WebVPN 成绩查询工具 - 增强版

主要改进：
1. 完善日志系统，GUI可以获取详细日志
2. 增强监控推送，使用HTML格式显示新成绩详情
3. 统一日志接口，支持GUI和命令行双重输出
"""
import requests
import time
import json
import re
import os
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

def encrypt_password(password):
    """AES CBC加密南开大学WebVPN密码"""
    key = "8bfa9ad090fbbf87e518f1ce24a93eee".encode('utf-8')
    iv = "fbfae671950f423b58d49b91ff6a22b9".encode('utf-8')
    cipher = AES.new(key, AES.MODE_CBC, iv[:16])
    encrypted_hex = cipher.encrypt(pad(password.encode('utf-8'), AES.block_size)).hex()
    return encrypted_hex

class WebVPNGradeChecker:
    def __init__(self, username, password, log_callback=None):
        self.session = requests.Session()
        self.base_url = "https://webvpn.nankai.edu.cn"
        self.username = username
        self.password = password
        self.encrypted_password = encrypt_password(password)
        self.semester_data = None
        self.log_callback = log_callback  # GUI日志回调函数
        
        # 设置请求头
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Origin': 'https://webvpn.nankai.edu.cn',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        })
    
    def log(self, message, level="INFO"):
        """统一日志输出"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        # 控制台输出
        print(formatted_message)
        
        # GUI回调输出
        if self.log_callback:
            self.log_callback(formatted_message)
    
    def get_dynamic_semesters(self):
        """动态获取当前用户的所有学期数据"""
        self.log("正在获取学期列表...")
        
        try:
            # 1. 访问成绩页面获取tagId
            person_url = f"{self.base_url}/https/77726476706e69737468656265737421f5f64c95347e6651700388a5d6502720dc08a5/eams/teach/grade/course/person.action"
            
            headers = {
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': f'{self.base_url}/https/77726476706e69737468656265737421f5f64c95347e6651700388a5d6502720dc08a5/eams/home.action'
            }
            
            self.session.headers.update(headers)
            response = self.session.get(person_url, params={'vpn-12-o2-eamis.nankai.edu.cn': ''})
            
            # 提取tagId
            tag_id_match = re.search(r'semesterBar(\d+)Semester', response.text)
            if tag_id_match:
                tag_id = f"semesterBar{tag_id_match.group(1)}Semester"
                self.log(f"✅ 获取到tagId: {tag_id}")
            else:
                self.log("⚠️ 未能获取到tagId，使用默认值")
                tag_id = "semesterBar4452416521Semester"
            
            # 2. 调用dataQuery.action获取学期数据
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
                self.log("✅ 成功获取学期数据")
                semester_info = self._parse_semester_response(response.text)
                if semester_info:
                    formatted_semesters = self._format_semesters(semester_info)
                    self.log(f"✅ 找到 {len(formatted_semesters)} 个可用学期")
                    return formatted_semesters
                else:
                    self.log("⚠️ 解析学期数据失败，使用默认数据")
                    return self._get_default_semesters()
            else:
                self.log(f"❌ 获取学期数据失败，状态码: {response.status_code}")
                return self._get_default_semesters()
                
        except Exception as e:
            self.log(f"❌ 获取学期数据时出错: {e}")
            return self._get_default_semesters()
    
    def _parse_semester_response(self, response_text):
        """解析学期数据响应"""
        try:
            response_text = response_text.strip()
            semesters_match = re.search(r'semesters:\s*({.*?})\s*,\s*yearIndex', response_text, re.DOTALL)
            if semesters_match:
                semesters_text = semesters_match.group(1)
                return self._parse_semesters_object(semesters_text)
            else:
                self.log("❌ 未找到semesters数据")
                return None
        except Exception as e:
            self.log(f"❌ 解析学期数据时出错: {e}")
            return None
    
    def _parse_semesters_object(self, semesters_text):
        """解析semesters对象"""
        semester_data = {}
        year_pattern = r'(y\d+):\s*\[(.*?)\]'
        year_matches = re.finditer(year_pattern, semesters_text, re.DOTALL)
        
        for year_match in year_matches:
            year_key = year_match.group(1)
            year_data_text = year_match.group(2)
            semester_list = []
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
        
        return semester_data
    
    def _format_semesters(self, semester_data):
        """格式化学期数据，只保留4位数ID的学期"""
        formatted_semesters = []
        sorted_years = sorted(semester_data.keys(), reverse=True)
        
        for year_key in sorted_years:
            semesters = semester_data[year_key]
            sorted_semesters = sorted(semesters, key=lambda x: int(x['name']), reverse=True)
            
            for semester in sorted_semesters:
                semester_id = str(semester['id'])
                if len(semester_id) == 4:
                    semester_info = {
                        'id': semester_id,
                        'display_name': f"{semester['schoolYear']} 第{semester['name']}学期",
                        'school_year': semester['schoolYear'],
                        'term': semester['name']
                    }
                    formatted_semesters.append(semester_info)
        
        return formatted_semesters
    
    def _get_default_semesters(self):
        """返回默认的学期数据"""
        return [
            {'id': '4364', 'display_name': '2025-2026 第1学期', 'school_year': '2025-2026', 'term': '1'},
            {'id': '4344', 'display_name': '2024-2025 第3学期', 'school_year': '2024-2025', 'term': '3'},
            {'id': '4324', 'display_name': '2024-2025 第2学期', 'school_year': '2024-2025', 'term': '2'},
            {'id': '4262', 'display_name': '2024-2025 第1学期', 'school_year': '2024-2025', 'term': '1'},
            {'id': '4304', 'display_name': '2023-2024 第3学期', 'school_year': '2023-2024', 'term': '3'},
            {'id': '4284', 'display_name': '2023-2024 第2学期', 'school_year': '2023-2024', 'term': '2'},
            {'id': '4263', 'display_name': '2023-2024 第1学期', 'school_year': '2023-2024', 'term': '1'},
        ]
    
    def login(self):
        """完整的登录流程"""
        self.log("正在登录WebVPN...")

        try:
            # 重新创建session（防止长时间监控导致session过期）
            self.log("初始化会话...")
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Origin': 'https://webvpn.nankai.edu.cn',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
            })
            self.session.get(f"{self.base_url}/")
            self.session.get(f"{self.base_url}/https/77726476706e69737468656265737421f9f64cd22931665b7f01c7a99c406d36af/login")
            
            # 获取CSRF Token
            self.log("获取CSRF Token...")
            timestamp = int(time.time() * 1000)
            token_url = f"{self.base_url}/wengine-vpn/cookie"
            params = {
                'method': 'get',
                'host': 'iam.nankai.edu.cn', 
                'scheme': 'https',
                'path': '/login',
                'vpn_timestamp': timestamp
            }
            
            response = self.session.get(token_url, params=params)
            csrf_match = re.search(r'csrf-token=([^;]+)', response.text)
            
            if not csrf_match:
                self.log("❌ 获取CSRF Token失败")
                return False
            
            csrf_token = csrf_match.group(1)
            self.log(f"✅ 获取到CSRF Token: {csrf_token[:10]}...")
            
            # 输入用户名和密码
            self.log("输入登录信息...")
            input_url = f"{self.base_url}/wengine-vpn/input"
            self.session.headers['Content-Type'] = 'text/plain;charset=UTF-8'
            
            self.session.post(input_url, json={"name": "", "type": "text", "value": self.username})
            self.session.post(input_url, json={"name": "", "type": "password", "value": self.encrypted_password})
        
            # 提交登录
            self.log("提交登录请求...")
            login_url = f"{self.base_url}/https/77726476706e69737468656265737421f9f64cd22931665b7f01c7a99c406d36af/api/v1/login"
            login_data = {
                "login_scene": "feilian",
                "account_type": "userid",
                "account": self.username,
                "password": self.encrypted_password
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Csrf-Token': csrf_token,
                'X-Version-Check': '0',
                'X-Fe-Version': '3.0.9.8465',
                'Accept-Language': 'zh-CN',
            }
            
            self.session.headers.update(headers)
            response = self.session.post(login_url, json=login_data, params={'vpn-12-o2-iam.nankai.edu.cn': '', 'os': 'web'})
            
            if response.status_code == 200 and 'success' in response.text.lower():
                self.log("✅ WebVPN登录成功")
                return True
            else:
                self.log("❌ WebVPN登录失败")
                return False
                
        except Exception as e:
            self.log(f"❌ 登录过程出错: {e}")
            return False
    
    def access_eamis(self):
        """访问教务系统"""
        self.log("正在访问教务系统...")
        
        try:
            timestamp = int(time.time() * 1000)
            
            # 访问教务系统
            self.session.get(f"{self.base_url}/https/77726476706e69737468656265737421f5f64c95347e6651700388a5d6502720dc08a5/eams?wrdrecordvisit={timestamp}")
            
            # 访问主页
            home_url = f"{self.base_url}/https/77726476706e69737468656265737421f5f64c95347e6651700388a5d6502720dc08a5/eams/home.action"
            home_response = self.session.get(home_url)
            
            if home_response.status_code == 200 or "教务系统" in home_response.text:
                self.log("✅ 成功进入教务系统")
                return True
            else:
                self.log("❌ 访问教务系统失败")
                return False
                
        except Exception as e:
            self.log(f"❌ 访问教务系统出错: {e}")
            return False
    
    def get_grades(self, semester_id="4324"):
        """获取指定学期的成绩"""
        self.log(f"正在获取学期 {semester_id} 的成绩...")
        
        person_url = f"{self.base_url}/https/77726476706e69737468656265737421f5f64c95347e6651700388a5d6502720dc08a5/eams/teach/grade/course/person.action"
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': f'{self.base_url}/https/77726476706e69737468656265737421f5f64c95347e6651700388a5d6502720dc08a5/eams/home.action'
        }
        
        original_headers = self.session.headers.copy()
        self.session.headers.update(headers)
        
        try:
            # POST请求
            response = self.session.post(person_url, 
                                    data={'project.id': '1', 'semester.id': semester_id}, 
                                    params={'vpn-12-o2-eamis.nankai.edu.cn': ''})
            
            # 提取tagId
            tag_id_match = re.search(r'semesterBar(\d+)Semester', response.text)
            tag_id = f"semesterBar{tag_id_match.group(1)}Semester" if tag_id_match else "semesterBar13572391471Semester"
            
            # 步骤2：查询学期日历数据
            data_query_url = f"{self.base_url}/https/77726476706e69737468656265737421f5f64c95347e6651700388a5d6502720dc08a5/eams/dataQuery.action"
            
            self.session.post(data_query_url, 
                            data={'tagId': tag_id, 'dataType': 'semesterCalendar', 'value': semester_id, 'empty': 'false'},
                            params={'vpn-12-o2-eamis.nankai.edu.cn': ''})
            
            # 步骤3：查询实体ID
            self.session.post(data_query_url, 
                            data={'entityId': '1'},
                            params={'vpn-12-o2-eamis.nankai.edu.cn': ''})
            
            # 步骤4：最终GET请求获取成绩数据
            timestamp = int(time.time() * 1000)
            final_url = f"{self.base_url}/https/77726476706e69737468656265737421f5f64c95347e6651700388a5d6502720dc08a5/eams/teach/grade/course/person!search.action"
            
            ajax_headers = {
                'Accept': 'text/html, */*; q=0.01',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': f'{self.base_url}/https/77726476706e69737468656265737421f5f64c95347e6651700388a5d6502720dc08a5/eams/teach/grade/course/person!search.action?semesterId={semester_id}&projectType='
            }
            
            self.session.headers.update(ajax_headers)
            
            final_response = self.session.get(final_url, 
                                            params={'vpn-12-o2-eamis.nankai.edu.cn': '', 'semesterId': semester_id, 
                                                'projectType': '', '_': timestamp})
            
            # 兼容不同成绩制度的检查条件
            response_text = final_response.text
            has_grade_table = False
            
            # 检查是否包含成绩表格
            if 'tbody' in response_text and ('grid' in response_text and '_data' in response_text):
                has_grade_table = True
                self.log("✅ 检测到成绩表格结构")
            elif '等级' in response_text and '绩点' in response_text:
                has_grade_table = True
                self.log("✅ 检测到等级制成绩表格")
            elif ('总评成绩' in response_text or '最终' in response_text or 
                '课程名称' in response_text and '学分' in response_text):
                has_grade_table = True
                self.log("✅ 检测到百分制成绩表格")
            elif re.search(r'\b\d{1,3}\b', response_text) and '课程' in response_text:
                has_grade_table = True
                self.log("✅ 检测到数字成绩表格")
            
            if has_grade_table:
                self.log("🔍 开始解析成绩数据...")
                return self.parse_grades(response_text)
            else:
                self.log("❌ 未能获取到完整的成绩数据（可能该学期没有成绩）")
                return None
                
        except Exception as e:
            self.log(f"❌ 获取成绩时出错: {e}")
            return None
        finally:
            self.session.headers = original_headers

    def parse_grades(self, html_content):
        """解析成绩HTML - 自动识别不同成绩制度"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            grade_tbody = soup.find('tbody', id=lambda x: x and 'grid' in x and '_data' in x)
            if not grade_tbody:
                self.log("❌ 未找到成绩表格tbody，尝试其他方式...")
                all_tbodies = soup.find_all('tbody')
                self.log(f"📊 找到 {len(all_tbodies)} 个tbody")
                
                if all_tbodies:
                    grade_tbody = max(all_tbodies, key=lambda x: len(x.find_all('tr')))
                    self.log(f"✅ 选择包含 {len(grade_tbody.find_all('tr'))} 行的tbody")
                else:
                    return None
            
            grades = []
            rows = grade_tbody.find_all('tr')
            
            self.log(f"📊 找到 {len(rows)} 行成绩数据")
            
            for i, row in enumerate(rows):
                cells = row.find_all('td')
                
                if len(cells) >= 8:
                    try:
                        # 基础信息（前6列固定）
                        grade_info = {
                            '学年学期': cells[0].get_text(strip=True),
                            '课程代码': cells[1].get_text(strip=True),
                            '课程序号': cells[2].get_text(strip=True),
                            '课程名称': cells[3].get_text(strip=True),
                            '课程类别': cells[4].get_text(strip=True),
                            '学分': float(cells[5].get_text(strip=True))
                        }
                        
                        # 解析第7列和第8列
                        col7_text = cells[6].get_text(strip=True)
                        col8_text = cells[7].get_text(strip=True)
                        
                        # 判断成绩制度
                        if self._is_letter_grade(col7_text):
                            # 等级制
                            grade_info['成绩类型'] = '等级制'
                            grade_info['等级'] = col7_text
                            try:
                                gpa = float(col8_text) if col8_text != '--' else None
                            except ValueError:
                                gpa = None
                            grade_info['绩点'] = gpa
                            grade_info['绩点文本'] = col8_text
                            self.log(f"✅ {grade_info['课程名称']}: {col7_text} (绩点: {col8_text}) - 等级制")
                            
                        elif col7_text in ['通过', '不通过', '合格', '不合格']:
                            # 通过制
                            grade_info['成绩类型'] = '通过制'
                            grade_info['等级'] = col7_text
                            grade_info['绩点'] = None
                            grade_info['绩点文本'] = '--'
                            self.log(f"✅ {grade_info['课程名称']}: {col7_text} - 通过制")
                            
                        else:
                            # 百分制
                            try:
                                score = float(col7_text)
                                grade_info['成绩类型'] = '百分制'
                                grade_info['分数'] = score
                                grade_info['等级'] = f"{score}分"
                                grade_info['绩点'] = self._score_to_gpa(score)
                                grade_info['绩点文本'] = str(grade_info['绩点']) if grade_info['绩点'] else "--"
                                self.log(f"✅ {grade_info['课程名称']}: {score}分 (绩点: {grade_info['绩点']}) - 百分制")
                            except ValueError:
                                # 未知格式
                                grade_info['成绩类型'] = '其他'
                                grade_info['等级'] = col7_text
                                grade_info['绩点'] = None
                                grade_info['绩点文本'] = col8_text
                                self.log(f"⚠️ {grade_info['课程名称']}: {col7_text} - 未知格式")
                        
                        grades.append(grade_info)
                        
                    except Exception as e:
                        self.log(f"❌ 解析第{i+1}行出错: {e}")
                        continue
                else:
                    self.log(f"⚠️ 第{i+1}行列数不足({len(cells)}列)，跳过")
            
            self.log(f"📊 成功解析 {len(grades)} 门课程")
            return grades if grades else None
            
        except Exception as e:
            self.log(f"❌ 解析成绩时出错: {e}")
            return None

    def _is_letter_grade(self, grade_text):
        """判断是否为字母等级制成绩"""
        letter_grades = ['A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F']
        return grade_text in letter_grades

    def _score_to_gpa(self, score):
        """将百分制分数转换为绩点"""
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

    def display_grades(self, grades):
        """显示成绩信息"""
        if not grades:
            self.log("没有成绩数据可显示")
            return
        
        self.log(f"\n{'='*80}")
        self.log(f"{'学期成绩单':^80}")
        self.log(f"{'='*80}")
        
        # 统计
        total_credits = 0
        gpa_credits = 0
        weighted_gpa = 0
        score_courses = []
        grade_courses = []
        pass_courses = []
        other_courses = []
        
        for i, grade in enumerate(grades, 1):
            credits = grade['学分']
            total_credits += credits
            
            self.log(f"\n{i}. {grade['课程名称']}")
            self.log(f"   课程代码: {grade['课程代码']} | 学分: {credits}")
            self.log(f"   成绩类型: {grade.get('成绩类型', '未知')}")
            
            grade_type = grade.get('成绩类型', '未知')
            
            if grade_type == '百分制':
                self.log(f"   成绩分数: {grade.get('分数', '未知')}分 | 对应绩点: {grade.get('绩点', 0)}")
                score_courses.append(grade)
                if grade.get('绩点') is not None:
                    gpa_credits += credits
                    weighted_gpa += credits * grade['绩点']
                    
            elif grade_type == '等级制':
                self.log(f"   成绩等级: {grade['等级']} | 绩点: {grade.get('绩点', '无')}")
                grade_courses.append(grade)
                if grade.get('绩点') is not None:
                    gpa_credits += credits
                    weighted_gpa += credits * grade['绩点']
                    
            elif grade_type == '通过制':
                self.log(f"   成绩: {grade['等级']}")
                pass_courses.append(grade)
                
            else:
                self.log(f"   成绩: {grade['等级']}")
                other_courses.append(grade)
        
        # 统计信息
        avg_gpa = weighted_gpa / gpa_credits if gpa_credits > 0 else 0
        
        self.log(f"\n{'='*80}")
        self.log(f"📊 学期统计:")
        self.log(f"   总课程数: {len(grades)} 门")
        self.log(f"   总学分: {total_credits}")
        
        if score_courses:
            total_score = sum(g.get('分数', 0) for g in score_courses)
            score_credits = sum(g['学分'] for g in score_courses)
            avg_score = total_score / len(score_courses) if score_courses else 0
            weighted_avg_score = sum(g.get('分数', 0) * g['学分'] for g in score_courses) / score_credits if score_credits > 0 else 0
            self.log(f"\n   📊 百分制课程: {len(score_courses)} 门")
            self.log(f"   平均分数: {avg_score:.1f}分")
            self.log(f"   加权平均分数: {weighted_avg_score:.1f}分")
        
        if grade_courses:
            self.log(f"\n   🎯 等级制课程: {len(grade_courses)} 门")
        
        if gpa_credits > 0:
            self.log(f"\n   ⭐ 计入绩点学分: {gpa_credits}")
            self.log(f"   加权平均绩点: {avg_gpa:.3f}")
        
        if pass_courses:
            self.log(f"\n   ✅ 通过制课程: {len(pass_courses)} 门")
            for course in pass_courses:
                self.log(f"   - {course['课程名称']} ({course['学分']} 学分): {course['等级']}")
        
        if other_courses:
            self.log(f"\n   ❓ 其他课程: {len(other_courses)} 门")
            for course in other_courses:
                self.log(f"   - {course['课程名称']} ({course['学分']} 学分): {course['等级']}")
        
        self.log(f"{'='*80}\n")

    def send_pushplus(self, token, title, content):
        """发送PushPlus通知"""
        if not token:
            self.log("❌ 未配置PushPlus Token")
            return False
        
        url = "http://www.pushplus.plus/send"
        data = {
            "token": token,
            "title": title,
            "content": content,
            "template": "html"
        }
        
        try:
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            if result.get('code') == 200:
                self.log("✅ 推送成功")
                return True
            else:
                self.log(f"❌ 推送失败: {result.get('msg')}")
                return False
        except Exception as e:
            self.log(f"❌ 推送异常: {e}")
            return False
    
    def build_grade_html(self, grades, semester_id, title_prefix="学期成绩单"):
        """构建成绩HTML格式 - 兼容多种成绩制度"""
        if not grades:
            return "<p>没有成绩数据</p>"
        
        # 分类统计
        total_credits = 0
        gpa_credits = 0
        weighted_gpa = 0
        grade_courses = []
        score_courses = []
        pass_courses = []
        
        for grade in grades:
            credits = grade['学分']
            total_credits += credits
            
            grade_type = grade.get('成绩类型', '未知')
            
            if grade_type == '等级制':
                grade_courses.append(grade)
                if grade.get('绩点') is not None:
                    gpa_credits += credits
                    weighted_gpa += credits * grade['绩点']
            elif grade_type == '百分制':
                score_courses.append(grade)
                if grade.get('绩点') is not None:
                    gpa_credits += credits
                    weighted_gpa += credits * grade['绩点']
            elif grade_type == '通过制':
                pass_courses.append(grade)
        
        avg_gpa = weighted_gpa / gpa_credits if gpa_credits > 0 else 0
        gpa_color = "#4CAF50" if avg_gpa >= 3.5 else "#2196F3" if avg_gpa >= 3.0 else "#FF9800"
        
        # 计算平均分数
        avg_score = 0
        if score_courses:
            total_score = sum(g.get('分数', 0) for g in score_courses)
            avg_score = total_score / len(score_courses)
        
        # 构建HTML
        html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <!-- 标题卡片 -->
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; border-radius: 15px 15px 0 0; text-align: center;">
                <h2 style="margin: 0; font-size: 28px;">🎓 {title_prefix}</h2>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">学期 {semester_id}</p>
            </div>
            
            <!-- 统计卡片 -->
            <div style="background: white; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px;">
        """
        
        # 如果有绩点课程，显示GPA
        if gpa_credits > 0:
            html += f"""
                <div style="text-align: center;">
                    <h1 style="margin: 0; color: {gpa_color}; font-size: 48px; font-weight: bold;">{avg_gpa:.3f}</h1>
                    <p style="margin: 5px 0 15px 0; color: #666; font-size: 18px;">加权平均绩点</p>
                </div>
            """
        
        html += f"""
                <div style="display: flex; justify-content: space-around; text-align: center; border-top: 1px solid #eee; padding-top: 15px;">
                    <div>
                        <p style="margin: 0; color: #999; font-size: 14px;">课程数</p>
                        <p style="margin: 5px 0 0 0; color: #333; font-size: 24px; font-weight: bold;">{len(grades)}</p>
                    </div>
                    <div>
                        <p style="margin: 0; color: #999; font-size: 14px;">总学分</p>
                        <p style="margin: 5px 0 0 0; color: #333; font-size: 24px; font-weight: bold;">{total_credits}</p>
                    </div>
        """
        
        # 动态显示第三个统计项
        if score_courses:
            html += f"""
                    <div>
                        <p style="margin: 0; color: #999; font-size: 14px;">平均分</p>
                        <p style="margin: 5px 0 0 0; color: #333; font-size: 24px; font-weight: bold;">{avg_score:.1f}分</p>
                    </div>
            """
        elif grade_courses:
            html += f"""
                    <div>
                        <p style="margin: 0; color: #999; font-size: 14px;">等级制</p>
                        <p style="margin: 5px 0 0 0; color: #333; font-size: 24px; font-weight: bold;">{len(grade_courses)}门</p>
                    </div>
            """
        
        html += """
                </div>
            </div>
            
            <!-- 成绩详情 -->
            <div style="background: white; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); border-radius: 10px;">
                <h3 style="margin: 0 0 20px 0; color: #333; font-size: 20px;">📚 课程成绩明细</h3>
        """
        
        # 添加每门课程
        for i, grade in enumerate(grades):
            grade_type = grade.get('成绩类型', '未知')
            
            # 根据成绩类型设置颜色
            if grade_type == '等级制':
                grade_colors = {
                    'A': '#4CAF50', 'A-': '#66BB6A',
                    'B+': '#42A5F5', 'B': '#2196F3', 'B-': '#1E88E5',
                    'C+': '#FFA726', 'C': '#FF9800', 'C-': '#FB8C00',
                    'D': '#EF5350', 'F': '#F44336'
                }
                grade_color = grade_colors.get(grade['等级'], '#757575')
            elif grade_type == '百分制':
                score = grade.get('分数', 0)
                if score >= 90:
                    grade_color = '#4CAF50'
                elif score >= 80:
                    grade_color = '#2196F3'
                elif score >= 70:
                    grade_color = '#FF9800'
                elif score >= 60:
                    grade_color = '#FFC107'
                else:
                    grade_color = '#F44336'
            elif grade_type == '通过制':
                if grade['等级'] in ['通过', '合格']:
                    grade_color = '#4CAF50'
                else:
                    grade_color = '#F44336'
            else:
                grade_color = '#757575'
            
            bg_color = "#f8f9fa" if i % 2 == 0 else "#ffffff"
            
            # 显示的成绩文本
            if grade_type == '百分制':
                display_grade = f"{grade.get('分数', 0):.0f}分"
            else:
                display_grade = grade['等级']
            
            # 绩点信息
            if grade.get('绩点') is not None:
                gpa_display = f"绩点 {grade['绩点']:.1f}"
            else:
                gpa_display = grade.get('绩点文本', '--')
            
            html += f"""
            <div style="display: flex; align-items: center; padding: 15px; background: {bg_color}; border-radius: 8px; margin-bottom: 10px;">
                <div style="flex: 1;">
                    <h4 style="margin: 0; color: #333; font-size: 16px;">{grade['课程名称']}</h4>
                    <p style="margin: 5px 0 0 0; color: #666; font-size: 14px;">
                        {grade['课程代码']} · {grade['课程类别']} · {grade['学分']}学分
                    </p>
                </div>
                <div style="text-align: right;">
                    <span style="display: inline-block; padding: 6px 12px; background: {grade_color}; color: white; border-radius: 20px; font-weight: bold; font-size: 16px;">
                        {display_grade}
                    </span>
                    <p style="margin: 5px 0 0 0; color: #666; font-size: 14px;">
                        {gpa_display}
                    </p>
                </div>
            </div>
            """
        
        html += f"""
            </div>
            
            <!-- 底部信息 -->
            <div style="text-align: center; color: #999; font-size: 12px; margin-top: 20px; padding: 20px;">
                <p>查询时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p style="margin-top: 10px;">🎉 继续加油！</p>
            </div>
        </div>
        """
        
        return html

    def select_semester(self):
        """让用户选择学期"""
        available_semesters = self.get_dynamic_semesters()
        
        if not available_semesters:
            self.log("❌ 无法获取学期数据")
            return "4324"
        
        self.log("\n📅 可用学期列表:")
        self.log("="*60)
        
        current_year = None
        display_index = 1
        semester_map = {}
        
        for semester in available_semesters:
            if semester['school_year'] != current_year:
                if current_year is not None:
                    self.log("")
                current_year = semester['school_year']
                self.log(f"📚 {current_year} 学年:")
            
            self.log(f"  {display_index:2d}. {semester['display_name']} (ID: {semester['id']})")
            semester_map[str(display_index)] = semester
            display_index += 1
        
        self.log("="*60)
        self.log(f"共找到 {len(available_semesters)} 个学期")
        
        choice = input("\n请选择学期 (输入数字或直接输入学期ID): ").strip()
        
        if not choice:
            # 默认选择
            for sem in available_semesters:
                if sem['school_year'] == "2024-2025" and sem['term'] == "2":
                    self.log(f"\n✅ 使用默认学期: {sem['display_name']}")
                    return sem['id']
            selected = available_semesters[0]
            self.log(f"\n✅ 使用默认学期: {selected['display_name']}")
            return selected['id']
        elif choice in semester_map:
            selected = semester_map[choice]
            self.log(f"\n✅ 已选择: {selected['display_name']}")
            return selected['id']
        elif choice.isdigit() and len(choice) == 4:
            self.log(f"\n✅ 使用学期ID: {choice}")
            return choice
        else:
            self.log("❌ 无效输入，使用默认学期")
            return available_semesters[0]['id']
    
    def run(self, semester_id=None, pushplus_token=None):
        """运行完整流程"""
        if not self.login():
            return
        
        if not self.access_eamis():
            return
        
        if not semester_id:
            semester_id = self.select_semester()
        
        grades = self.get_grades(semester_id)
        
        if grades:
            self.log(f"\n✅ 成功获取到 {len(grades)} 条成绩记录")
            self.display_grades(grades)
            
            if pushplus_token:
                push = input("\n是否将成绩推送到微信? (y/n): ").strip().lower()
                if push == 'y':
                    html = self.build_grade_html(grades, semester_id)
                    self.send_pushplus(pushplus_token, f"成绩查询结果 - 学期{semester_id}", html)
        else:
            self.log("\n❌ 未能获取到成绩数据")
        
        # 询问是否查询其他学期
        while True:
            another = input("\n是否查询其他学期? (y/n): ").strip().lower()
            if another == 'y':
                semester_id = self.select_semester()
                grades = self.get_grades(semester_id)
                if grades:
                    self.display_grades(grades)
                    if pushplus_token:
                        push = input("\n是否将成绩推送到微信? (y/n): ").strip().lower()
                        if push == 'y':
                            html = self.build_grade_html(grades, semester_id)
                            self.send_pushplus(pushplus_token, f"成绩查询结果 - 学期{semester_id}", html)
            else:
                break


# 🔧 重点改进：成绩监控类
class GradeMonitor(WebVPNGradeChecker):
    def __init__(self, username, encrypted_password, pushplus_token, log_callback=None):
        super().__init__(username, encrypted_password, log_callback)
        self.pushplus_token = pushplus_token
        self.last_grades_file = "last_grades.json"
        
    def load_last_grades(self):
        """加载上次的成绩"""
        try:
            if os.path.exists(self.last_grades_file):
                with open(self.last_grades_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.log(f"加载历史成绩失败: {e}")
        return []
    
    def save_last_grades(self, grades):
        """保存成绩"""
        try:
            grades_data = [{
                '课程代码': g['课程代码'],
                '课程名称': g['课程名称'],
                '等级': g['等级'],
                '学分': g['学分'],
                '绩点': g['绩点'],
                '成绩类型': g.get('成绩类型', '未知'),
                '分数': g.get('分数', None)
            } for g in grades]
            
            with open(self.last_grades_file, 'w', encoding='utf-8') as f:
                json.dump(grades_data, f, ensure_ascii=False, indent=2)
                
            self.log(f"已保存 {len(grades_data)} 门课程记录")
        except Exception as e:
            self.log(f"保存成绩失败: {e}")
    
    def check_grades(self, semester_id="4324"):
        """检查成绩变化 - 增强版"""
        self.log(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始检查学期 {semester_id} 的成绩...")
        
        # 获取当前成绩
        current_grades = self.get_grades(semester_id)
        if not current_grades:
            self.log("❌ 未获取到成绩数据，跳过本次检查")
            return False
        
        self.log(f"✅ 当前获取到 {len(current_grades)} 门课程")
        
        # 加载上次成绩
        last_grades = self.load_last_grades()
        self.log(f"📚 历史记录中有 {len(last_grades)} 门课程")
        
        # 比较变化
        last_dict = {g['课程代码']: g for g in last_grades}
        new_courses = []
        updated_courses = []
        
        for grade in current_grades:
            course_code = grade['课程代码']
            if course_code not in last_dict:
                # 完全新增的课程
                new_courses.append(grade)
                self.log(f"🆕 新增课程: {grade['课程名称']} - {grade['等级']}")
            else:
                # 检查成绩是否有变化
                last_grade = last_dict[course_code]
                if (grade['等级'] != last_grade['等级'] or 
                    grade.get('绩点') != last_grade.get('绩点')):
                    updated_courses.append({
                        'current': grade,
                        'previous': last_grade
                    })
                    self.log(f"📝 更新课程: {grade['课程名称']} - {last_grade['等级']} → {grade['等级']}")
        
        # 统计变化
        total_changes = len(new_courses) + len(updated_courses)
        
        if total_changes > 0:
            self.log(f"🎉 发现成绩变化！")
            self.log(f"   新增课程: {len(new_courses)} 门")
            self.log(f"   更新课程: {len(updated_courses)} 门")
            
            # 🔧 重点改进：发送详细的HTML推送
            if self.pushplus_token:
                self._send_grade_change_notification(new_courses, updated_courses, semester_id)
            else:
                self.log("⚠️ 未配置推送Token，跳过通知")
                
        else:
            self.log(f"✅ 暂无新变化 (当前共 {len(current_grades)} 门课程)")
        
        # 保存当前成绩
        self.save_last_grades(current_grades)
        
        return total_changes > 0
    
    def _send_grade_change_notification(self, new_courses, updated_courses, semester_id):
        """发送成绩变化通知 - 增强的HTML推送"""
        try:
            total_changes = len(new_courses) + len(updated_courses)
            
            # 构建推送标题
            if new_courses and updated_courses:
                title = f"🎓 成绩更新通知 - 新增{len(new_courses)}门，更新{len(updated_courses)}门"
            elif new_courses:
                title = f"🎓 新增成绩通知 - {len(new_courses)}门课程"
            else:
                title = f"🎓 成绩更新通知 - {len(updated_courses)}门课程"
            
            # 构建HTML内容
            html_content = self._build_change_notification_html(new_courses, updated_courses, semester_id)
            
            # 发送推送
            if self.send_pushplus(self.pushplus_token, title, html_content):
                self.log(f"✅ 成绩变化通知已推送到微信 ({total_changes}门课程)")
            else:
                self.log("❌ 推送失败")
                
        except Exception as e:
            self.log(f"❌ 发送通知时出错: {e}")
    
    def _build_change_notification_html(self, new_courses, updated_courses, semester_id):
        """构建成绩变化通知的HTML"""
        total_changes = len(new_courses) + len(updated_courses)
        
        html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <!-- 标题卡片 -->
            <div style="background: linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 100%); color: white; padding: 25px; border-radius: 15px 15px 0 0; text-align: center;">
                <h2 style="margin: 0; font-size: 28px;">🎉 成绩更新通知</h2>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">学期 {semester_id} · 共 {total_changes} 门课程有变化</p>
            </div>
            
            <!-- 统计卡片 -->
            <div style="background: white; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-around; text-align: center;">
                    <div>
                        <h3 style="margin: 0; color: #4CAF50; font-size: 36px; font-weight: bold;">{len(new_courses)}</h3>
                        <p style="margin: 5px 0 0 0; color: #666; font-size: 16px;">新增课程</p>
                    </div>
                    <div>
                        <h3 style="margin: 0; color: #2196F3; font-size: 36px; font-weight: bold;">{len(updated_courses)}</h3>
                        <p style="margin: 5px 0 0 0; color: #666; font-size: 16px;">更新课程</p>
                    </div>
                </div>
            </div>
        """
        
        # 新增课程部分
        if new_courses:
            html += """
            <div style="background: white; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); border-radius: 10px; margin-bottom: 20px;">
                <h3 style="margin: 0 0 20px 0; color: #4CAF50; font-size: 20px;">🆕 新增课程</h3>
            """
            
            for i, grade in enumerate(new_courses):
                grade_type = grade.get('成绩类型', '未知')
                
                # 设置颜色
                if grade_type == '等级制':
                    grade_colors = {
                        'A': '#4CAF50', 'A-': '#66BB6A',
                        'B+': '#42A5F5', 'B': '#2196F3', 'B-': '#1E88E5',
                        'C+': '#FFA726', 'C': '#FF9800', 'C-': '#FB8C00',
                        'D': '#EF5350', 'F': '#F44336'
                    }
                    grade_color = grade_colors.get(grade['等级'], '#757575')
                elif grade_type == '百分制':
                    score = grade.get('分数', 0)
                    if score >= 90:
                        grade_color = '#4CAF50'
                    elif score >= 80:
                        grade_color = '#2196F3'
                    elif score >= 70:
                        grade_color = '#FF9800'
                    elif score >= 60:
                        grade_color = '#FFC107'
                    else:
                        grade_color = '#F44336'
                elif grade_type == '通过制':
                    grade_color = '#4CAF50' if grade['等级'] in ['通过', '合格'] else '#F44336'
                else:
                    grade_color = '#757575'
                
                # 显示文本
                if grade_type == '百分制':
                    display_grade = f"{grade.get('分数', 0):.0f}分"
                else:
                    display_grade = grade['等级']
                
                # 绩点信息
                if grade.get('绩点') is not None:
                    gpa_display = f"绩点 {grade['绩点']:.1f}"
                else:
                    gpa_display = grade.get('绩点文本', '--')
                
                bg_color = "#e8f5e8" if i % 2 == 0 else "#f0f8f0"
                
                html += f"""
                <div style="display: flex; align-items: center; padding: 15px; background: {bg_color}; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #4CAF50;">
                    <div style="flex: 1;">
                        <h4 style="margin: 0; color: #333; font-size: 16px;">{grade['课程名称']}</h4>
                        <p style="margin: 5px 0 0 0; color: #666; font-size: 14px;">
                            {grade['课程代码']} · {grade['课程类别']} · {grade['学分']}学分
                        </p>
                    </div>
                    <div style="text-align: right;">
                        <span style="display: inline-block; padding: 6px 12px; background: {grade_color}; color: white; border-radius: 20px; font-weight: bold; font-size: 16px;">
                            {display_grade}
                        </span>
                        <p style="margin: 5px 0 0 0; color: #666; font-size: 14px;">
                            {gpa_display}
                        </p>
                    </div>
                </div>
                """
            
            html += "</div>"
        
        # 更新课程部分
        if updated_courses:
            html += """
            <div style="background: white; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); border-radius: 10px; margin-bottom: 20px;">
                <h3 style="margin: 0 0 20px 0; color: #2196F3; font-size: 20px;">📝 更新课程</h3>
            """
            
            for i, change in enumerate(updated_courses):
                current = change['current']
                previous = change['previous']
                
                bg_color = "#e3f2fd" if i % 2 == 0 else "#f0f8ff"
                
                html += f"""
                <div style="padding: 15px; background: {bg_color}; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #2196F3;">
                    <h4 style="margin: 0 0 10px 0; color: #333; font-size: 16px;">{current['课程名称']}</h4>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="color: #666; font-size: 14px;">
                            {current['课程代码']} · {current['课程类别']} · {current['学分']}学分
                        </div>
                        <div style="text-align: right;">
                            <div style="margin-bottom: 5px;">
                                <span style="color: #999; font-size: 12px;">原成绩: </span>
                                <span style="text-decoration: line-through; color: #999;">{previous['等级']}</span>
                            </div>
                            <div>
                                <span style="color: #999; font-size: 12px;">新成绩: </span>
                                <span style="color: #2196F3; font-weight: bold; font-size: 16px;">{current['等级']}</span>
                            </div>
                        </div>
                    </div>
                </div>
                """
            
            html += "</div>"
        
        # 底部信息
        html += f"""
            <div style="text-align: center; color: #999; font-size: 12px; margin-top: 20px; padding: 20px;">
                <p>检查时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p style="margin-top: 10px;">🎉 恭喜获得新成绩！继续加油！</p>
            </div>
        </div>
        """
        
        return html
    
    def monitor_loop(self, semester_id="4324", interval=30):
        """持续监控成绩 - 增强版"""
        self.log(f"🚀 开始监控学期 {semester_id}，每 {interval} 分钟检查一次")
        self.log(f"📱 推送Token: {'已配置' if self.pushplus_token else '未配置'}")
        
        check_count = 0
        
        while True:
            try:
                check_count += 1
                self.log(f"\n{'='*60}")
                self.log(f"🔍 第 {check_count} 次检查 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                self.log(f"{'='*60}")
                
                # 登录检查
                if not self.login():
                    self.log("❌ 登录失败，等待下次检查")
                elif not self.access_eamis():
                    self.log("❌ 访问教务系统失败，等待下次检查")
                else:
                    # 检查成绩
                    has_changes = self.check_grades(semester_id)
                    
                    if has_changes:
                        self.log("🎊 本次检查发现成绩变化！")
                    else:
                        self.log("😴 本次检查无变化")
                
                # 计算下次检查时间
                next_check_time = datetime.now()
                next_check_time = next_check_time.replace(
                    hour=(next_check_time.hour + interval // 60) % 24,
                    minute=(next_check_time.minute + interval % 60) % 60,
                    second=0,
                    microsecond=0
                )
                
                self.log(f"⏰ 下次检查时间: {next_check_time.strftime('%H:%M:%S')}")
                self.log(f"💤 等待 {interval} 分钟...")
                
            except KeyboardInterrupt:
                self.log("\n⚡ 收到中断信号，停止监控")
                break
            except Exception as e:
                self.log(f"❌ 监控过程出错: {e}")
                self.log("⏱️ 等待1分钟后继续...")
                time.sleep(60)
                continue
            
            # 等待指定时间，每分钟显示一次剩余时间
            for i in range(interval):
                try:
                    time.sleep(60)  # 等待1分钟
                    remaining = interval - i - 1
                    if remaining > 0 and remaining % 5 == 0:  # 每5分钟显示一次
                        self.log(f"⏳ 还有 {remaining} 分钟进行下次检查...")
                except KeyboardInterrupt:
                    self.log("\n⚡ 收到中断信号，停止监控")
                    return


if __name__ == "__main__":
    # 配置信息
    USERNAME = ""  # 学号
    PASSWORD = ""  # WebVPN密码
    PUSHPLUS_TOKEN = ""  # PushPlus Token
    
    print("南开大学成绩查询工具")
    print("="*50)
    print("选择运行模式:")
    print("1. 普通查询")
    print("2. 成绩监控")
    
    mode = input("请选择 (1/2): ").strip()
    
    if mode == "2":
        # 监控模式
        print(f"\n🎯 启动成绩监控模式")
        print("🔧 功能特性:")
        print("   ✅ 自动检测新增课程")
        print("   ✅ 自动检测成绩更新")
        print("   ✅ 详细的HTML微信推送")
        print("   ✅ 完善的日志记录")
        print("   ✅ 兼容22级百分制和23级等级制")
        
        # 获取监控参数
        if not USERNAME:
            USERNAME = input("请输入学号: ").strip()
        if not PASSWORD:
            PASSWORD = input("请输入WebVPN密码: ").strip()
            
        semester_input = input(f"\n请输入要监控的学期ID (直接回车使用 4324): ").strip()
        semester_id = semester_input if semester_input else "4324"
        
        interval_input = input(f"请输入检查间隔(分钟，直接回车使用 30): ").strip()
        try:
            interval = int(interval_input) if interval_input else 30
            if interval < 5:
                print("⚠️ 间隔时间不能少于5分钟，自动设置为5分钟")
                interval = 5
        except ValueError:
            print("⚠️ 输入无效，使用默认间隔30分钟")
            interval = 30
        
        print(f"\n🚀 开始监控...")
        print(f"📚 监控学期: {semester_id}")
        print(f"⏱️ 检查间隔: {interval} 分钟")
        print(f"📱 推送状态: {'✅ 已配置' if PUSHPLUS_TOKEN else '❌ 未配置'}")
        print("💡 按 Ctrl+C 可以停止监控")
        print("="*50)
        
        monitor = GradeMonitor(USERNAME, PASSWORD, PUSHPLUS_TOKEN)
        monitor.monitor_loop(semester_id=semester_id, interval=interval)
        
    else:
        # 普通查询模式
        print(f"\n🎯 启动普通查询模式")
        if not USERNAME:
            USERNAME = input("请输入学号: ").strip()
        if not PASSWORD:
            PASSWORD = input("请输入WebVPN密码: ").strip()
            
        checker = WebVPNGradeChecker(USERNAME, PASSWORD)
        checker.run(pushplus_token=PUSHPLUS_TOKEN)
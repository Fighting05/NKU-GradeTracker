"""
NKU成绩查询 v3.0 - EAMIS教务系统直接登录模块（不经过WebVPN）
用于WebVPN限制关闭或作为备选方案
"""
import requests
import time
import re
from typing import Callable, Optional
from ..utils.crypto import encrypt_password


class EamisDirectLogin:
    """EAMIS教务系统直接登录类"""

    def __init__(self, username: str, password: str, log_callback: Optional[Callable] = None):
        """
        初始化

        Args:
            username: 学号
            password: 明文密码
            log_callback: 日志回调函数
        """
        self.username = username
        self.password = password
        self.encrypted_password = encrypt_password(password)
        self.session = requests.Session()
        self.iam_url = "https://iam.nankai.edu.cn"
        self.eamis_url = "https://eamis.nankai.edu.cn"
        self.log_callback = log_callback

    def log(self, message: str):
        """日志输出"""
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def login(self) -> bool:
        """
        执行CAS登录并获取教务系统session

        Returns:
            是否登录成功
        """
        self.log("正在通过CAS统一认证登录教务系统...")

        try:
            # 初始化session
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': '*/*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            })

            # 步骤1: 访问教务系统，获取跳转到CAS登录
            self.log("访问教务系统，准备CAS认证...")
            service_url = f"{self.eamis_url}/eams/login.action"
            cas_login_url = f"{self.iam_url}/api/cas/login?service={service_url}"

            # 访问CAS登录页面，获取csrf-token
            response = self.session.get(cas_login_url)

            # 从cookie中获取csrf-token
            csrf_token = None
            for cookie in self.session.cookies:
                if cookie.name == 'csrf-token':
                    csrf_token = cookie.value
                    break

            if not csrf_token:
                # 尝试从响应头中获取
                set_cookie = response.headers.get('Set-Cookie', '')
                csrf_match = re.search(r'csrf-token=([^;]+)', set_cookie)
                if csrf_match:
                    csrf_token = csrf_match.group(1)

            if not csrf_token:
                self.log("⚠️ 未获取到csrf-token，继续尝试登录...")
                csrf_token = ""
            else:
                self.log(f"✅ 获取到CSRF Token")

            # 步骤2: POST登录到CAS
            self.log("提交CAS登录...")
            login_url = f"{self.iam_url}/api/v1/login"
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
                'X-Fe-Version': '3.1.9.11464',
                'Accept-Language': 'zh-CN',
                'Referer': f'{self.iam_url}/login'
            }

            self.session.headers.update(headers)
            response = self.session.post(login_url, json=login_data,
                                        params={'os': 'web'}, timeout=10)

            if response.status_code != 200:
                self.log(f"❌ CAS登录失败，状态码: {response.status_code}")
                return False

            # 检查登录结果
            try:
                result = response.json()
                if result.get('code') == 0 and 'success' in result.get('data', {}).get('result', ''):
                    self.log("✅ CAS认证成功")
                else:
                    self.log(f"❌ CAS登录失败: {result}")
                    return False
            except:
                self.log("❌ CAS登录响应解析失败")
                return False

            # 步骤3: 获取CAS ticket并访问教务系统
            self.log("获取CAS ticket并进入教务系统...")
            cas_ticket_url = f"{self.iam_url}/api/cas/login"
            params = {
                'service': service_url,
                'lang': 'zh-CN'
            }

            response = self.session.get(cas_ticket_url, params=params,
                                       allow_redirects=False, timeout=10)

            # 检查是否重定向到教务系统（带ticket）
            if response.status_code in [301, 302, 303, 307, 308]:
                redirect_url = response.headers.get('Location', '')
                if 'ticket=' in redirect_url:
                    self.log("✅ 获取到CAS ticket")

                    # 访问教务系统登录URL（带ticket）
                    if redirect_url.startswith('http'):
                        ticket_url = redirect_url
                    else:
                        ticket_url = f"{self.eamis_url}{redirect_url}"

                    self.log("使用ticket登录教务系统...")
                    response = self.session.get(ticket_url, timeout=10)

                    if response.status_code == 200:
                        # 检查是否成功进入教务系统
                        if '教务系统' in response.text or 'home.action' in response.text:
                            self.log("✅ 成功登录教务系统")
                            return True
                        else:
                            self.log("⚠️ 访问到页面但不确定是否成功")
                            # 尝试访问home.action验证
                            home_response = self.session.get(f"{self.eamis_url}/eams/home.action")
                            if home_response.status_code == 200 and 'portal-fe' not in home_response.text:
                                self.log("✅ 验证成功，已进入教务系统")
                                return True

                    self.log("❌ 教务系统登录失败")
                    return False
                else:
                    self.log("❌ 未获取到ticket")
                    return False
            else:
                self.log(f"❌ CAS ticket获取失败，状态码: {response.status_code}")
                return False

        except Exception as e:
            self.log(f"❌ 登录过程出错: {e}")
            return False

    def get_session(self):
        """获取已登录的session"""
        return self.session

    def get_base_url(self):
        """获取教务系统基础URL"""
        return self.eamis_url

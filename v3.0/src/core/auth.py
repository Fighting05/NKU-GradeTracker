"""
NKU成绩查询 v3.0 - WebVPN 登录认证
从 nku_grades.py 移植
"""

import requests
import re
import time
from typing import Callable, Optional
from ..utils.crypto import encrypt_password


class WebVPNAuthenticator:
    """WebVPN 认证器"""

    def __init__(self, username: str, password: str, log_callback: Optional[Callable] = None):
        """
        初始化认证器

        Args:
            username: 学号
            password: 明文密码
            log_callback: 日志回调函数
        """
        self.username = username
        self.password = password
        self.encrypted_password = encrypt_password(password)
        self.session = requests.Session()
        self.base_url = "https://webvpn.nankai.edu.cn"
        self.log_callback = log_callback

    def log(self, message: str):
        """日志输出"""
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def login(self) -> bool:
        """
        执行完整的登录流程

        Returns:
            是否登录成功
        """
        self.log("正在登录 WebVPN...")

        try:
            # 重新创建 session（防止长时间监控导致 session 过期）
            self.log("初始化会话...")
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': '*/*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
            })
            self.session.get(f"{self.base_url}/")
            self.session.get(f"{self.base_url}/https/77726476706e69737468656265737421f9f64cd22931665b7f01c7a99c406d36af/login")

            # 获取 CSRF Token
            self.log("获取 CSRF Token...")
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
                self.log("获取 CSRF Token 失败")
                return False

            csrf_token = csrf_match.group(1)
            self.log(f"获取到 CSRF Token")

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
            response = self.session.post(login_url, json=login_data,
                                        params={'vpn-12-o2-iam.nankai.edu.cn': '', 'os': 'web'})

            if response.status_code == 200 and 'success' in response.text.lower():
                self.log("WebVPN 登录成功")
                return True
            else:
                self.log("WebVPN 登录失败")
                return False

        except Exception as e:
            self.log(f"登录过程出错: {e}")
            return False

    def access_eamis(self) -> bool:
        """
        访问教务系统

        Returns:
            是否成功访问
        """
        self.log("正在访问教务系统...")

        try:
            timestamp = int(time.time() * 1000)

            # 访问教务系统
            self.session.get(
                f"{self.base_url}/https/77726476706e69737468656265737421f5f64c95347e6651700388a5d6502720dc08a5/eams?wrdrecordvisit={timestamp}"
            )

            # 访问主页
            home_url = f"{self.base_url}/https/77726476706e69737468656265737421f5f64c95347e6651700388a5d6502720dc08a5/eams/home.action"
            home_response = self.session.get(home_url)

            if home_response.status_code == 200 or "教务系统" in home_response.text:
                self.log("成功进入教务系统")
                return True
            else:
                self.log("访问教务系统失败")
                return False

        except Exception as e:
            self.log(f"访问教务系统出错: {e}")
            return False

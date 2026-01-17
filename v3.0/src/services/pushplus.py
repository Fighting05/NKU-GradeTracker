"""
NKU成绩查询 v3.0 - PushPlus 推送服务
"""

import requests
from typing import Optional


class PushPlusService:
    """PushPlus 推送服务"""

    def __init__(self, token: str):
        """
        初始化 PushPlus 服务

        Args:
            token: PushPlus Token
        """
        self.token = token
        self.api_url = "http://www.pushplus.plus/send"

    def send_notification(self, title: str, content: str, template: str = "html") -> bool:
        """
        发送推送通知

        Args:
            title: 标题
            content: 内容（支持HTML）
            template: 模板类型，默认html

        Returns:
            是否发送成功
        """
        try:
            data = {
                "token": self.token,
                "title": title,
                "content": content,
                "template": template
            }

            response = requests.post(self.api_url, json=data, timeout=10)

            if response.status_code == 200:
                result = response.json()
                return result.get("code") == 200
            else:
                print(f"[PushPlus] 发送失败，状态码: {response.status_code}")
                return False

        except Exception as e:
            print(f"[PushPlus] 发送出错: {e}")
            return False

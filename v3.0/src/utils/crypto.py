"""
NKU成绩查询 v3.0 - AES 加密工具
从 nku_grades.py 移植
"""

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad


def encrypt_password(password: str) -> str:
    """
    使用 AES-CBC 加密密码（南开 WebVPN 专用）

    Args:
        password: 明文密码

    Returns:
        加密后的十六进制字符串
    """
    # 固定的 Key 和 IV（从 WebVPN 前端 JS 中提取）
    key = "8bfa9ad090fbbf87e518f1ce24a93eee".encode('utf-8')
    iv = "fbfae671950f423b58d49b91ff6a22b9".encode('utf-8')

    # 创建 AES-CBC 加密器
    cipher = AES.new(key, AES.MODE_CBC, iv[:16])

    # 加密并转换为十六进制
    encrypted = cipher.encrypt(pad(password.encode('utf-8'), AES.block_size))
    return encrypted.hex()

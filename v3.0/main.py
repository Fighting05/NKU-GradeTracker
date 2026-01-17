"""
NKU成绩查询 v3.0
主入口文件
"""

import flet as ft
from src.ui.app import main as app_main


if __name__ == "__main__":
    # 启动 Flet 应用
    ft.app(target=app_main)

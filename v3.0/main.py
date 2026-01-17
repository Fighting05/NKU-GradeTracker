"""
NKU成绩查询 v3.0
主入口文件
"""

import sys
import traceback

print("=" * 60)
print("[DEBUG] NKU成绩查询 v3.0 启动")
print(f"[DEBUG] Python版本: {sys.version}")
print(f"[DEBUG] 平台: {sys.platform}")
print("=" * 60)

try:
    print("[DEBUG] 正在导入 flet...")
    import flet as ft
    print("[DEBUG] flet 导入成功")

    print("[DEBUG] 正在导入 app_main...")
    from src.ui.app import main as app_main
    print("[DEBUG] app_main 导入成功")

    print("[DEBUG] 正在启动 Flet 应用...")
    ft.app(target=app_main)
    print("[DEBUG] Flet 应用启动成功")

except Exception as e:
    print(f"[ERROR] 启动失败: {e}")
    print(f"[ERROR] 详细错误:\n{traceback.format_exc()}")
    sys.exit(1)

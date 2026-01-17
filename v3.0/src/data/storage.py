"""
NKU成绩查询 v3.0 - 跨平台存储路径管理
"""

import os
import sys
from pathlib import Path


def get_app_data_dir() -> Path:
    """
    获取应用数据存储目录（跨平台）

    Returns:
        应用数据目录的 Path 对象
    """
    print("[DEBUG] storage.py - 开始获取应用数据目录")
    app_name = "NKUGrades"

    try:
        # 判断平台
        print(f"[DEBUG] storage.py - 系统平台: {sys.platform}")

        if sys.platform == "win32":
            # Windows: C:\Users\用户名\AppData\Local\NKUGrades
            base_dir = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
            app_dir = base_dir / app_name
            print(f"[DEBUG] storage.py - Windows 平台，目录: {app_dir}")

        elif sys.platform == "darwin":
            # macOS: ~/Library/Application Support/NKUGrades
            app_dir = Path.home() / "Library" / "Application Support" / app_name
            print(f"[DEBUG] storage.py - macOS 平台，目录: {app_dir}")

        elif sys.platform.startswith("linux"):
            # Linux/Android: ~/.local/share/NKUGrades
            xdg_data_home = os.getenv("XDG_DATA_HOME")
            print(f"[DEBUG] storage.py - Linux/Android 平台，XDG_DATA_HOME: {xdg_data_home}")

            if xdg_data_home:
                base_dir = Path(xdg_data_home)
            else:
                home = Path.home()
                print(f"[DEBUG] storage.py - Home 目录: {home}")
                base_dir = home / ".local" / "share"

            app_dir = base_dir / app_name
            print(f"[DEBUG] storage.py - Linux/Android 目录: {app_dir}")

        else:
            # 其他平台：使用用户目录
            app_dir = Path.home() / f".{app_name.lower()}"
            print(f"[DEBUG] storage.py - 其他平台，目录: {app_dir}")

        # 确保目录存在
        print(f"[DEBUG] storage.py - 正在创建目录: {app_dir}")
        app_dir.mkdir(parents=True, exist_ok=True)
        print(f"[DEBUG] storage.py - 目录创建成功")

        return app_dir

    except Exception as e:
        print(f"[ERROR] storage.py - 获取目录失败: {e}")
        import traceback
        print(f"[ERROR] 详细错误:\n{traceback.format_exc()}")
        raise


def get_database_path() -> Path:
    """
    获取数据库文件路径

    Returns:
        数据库文件的完整路径
    """
    return get_app_data_dir() / "nku_grades.db"


if __name__ == "__main__":
    # 测试
    print(f"应用数据目录: {get_app_data_dir()}")
    print(f"数据库路径: {get_database_path()}")

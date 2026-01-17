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
    app_name = "NKUGrades"

    # 判断平台
    if sys.platform == "win32":
        # Windows: C:\Users\用户名\AppData\Local\NKUGrades
        base_dir = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        app_dir = base_dir / app_name

    elif sys.platform == "darwin":
        # macOS: ~/Library/Application Support/NKUGrades
        app_dir = Path.home() / "Library" / "Application Support" / app_name

    elif sys.platform.startswith("linux"):
        # Linux/Android: ~/.local/share/NKUGrades
        xdg_data_home = os.getenv("XDG_DATA_HOME")
        if xdg_data_home:
            base_dir = Path(xdg_data_home)
        else:
            base_dir = Path.home() / ".local" / "share"
        app_dir = base_dir / app_name

    else:
        # 其他平台：使用用户目录
        app_dir = Path.home() / f".{app_name.lower()}"

    # 确保目录存在
    app_dir.mkdir(parents=True, exist_ok=True)

    return app_dir


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

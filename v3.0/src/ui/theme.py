"""
NKU成绩查询 v3.0 - 主题配置
蓝绿色系 Material Design 3 主题
"""

import flet as ft


# 颜色定义
class AppColors:
    """应用颜色常量"""
    # 主色调
    PRIMARY = "#1976D2"  # 蓝色，专业感
    SECONDARY = "#26A69A"  # 青绿色，活力感
    SURFACE = "#FFFFFF"  # 白色背景
    BACKGROUND = "#F5F5F5"  # 浅灰背景

    # 语义色
    SUCCESS = "#4CAF50"  # 绿色
    WARNING = "#FF9800"  # 橙色
    ERROR = "#F44336"  # 红色
    INFO = "#2196F3"  # 亮蓝

    # 成绩着色（保留旧版逻辑）
    GRADE_A = "#4CAF50"  # A/A-/95+ 绿色
    GRADE_B = "#2196F3"  # B+/B/B-/85-94 蓝色
    GRADE_C = "#FF9800"  # C+/C/C-/75-84 橙色
    GRADE_D = "#F44336"  # D/F/60-74 红色
    GRADE_PASS = "#4CAF50"  # 通过 绿色
    GRADE_FAIL = "#F44336"  # 不通过 红色


def get_app_theme() -> ft.Theme:
    """获取应用主题配置"""
    return ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=AppColors.PRIMARY,
            secondary=AppColors.SECONDARY,
            surface=AppColors.SURFACE,
            background=AppColors.BACKGROUND,
            error=AppColors.ERROR,
        ),
        use_material3=True,
    )


def get_grade_color(grade: str, grade_type: str) -> str:
    """
    根据成绩等级和类型返回对应的颜色

    Args:
        grade: 成绩等级（如 'A', '90分', '通过'）
        grade_type: 成绩类型（'百分制', '等级制', '通过制'）

    Returns:
        颜色十六进制字符串
    """
    if grade_type == "等级制":
        if grade in ["A", "A-"]:
            return AppColors.GRADE_A
        elif grade in ["B+", "B", "B-"]:
            return AppColors.GRADE_B
        elif grade in ["C+", "C", "C-"]:
            return AppColors.GRADE_C
        elif grade in ["D", "F"]:
            return AppColors.GRADE_D
        else:
            return AppColors.INFO

    elif grade_type == "百分制":
        try:
            score = float(grade.replace("分", ""))
            if score >= 95:
                return AppColors.GRADE_A
            elif score >= 85:
                return AppColors.GRADE_B
            elif score >= 75:
                return AppColors.GRADE_C
            elif score >= 60:
                return AppColors.GRADE_D
            else:
                return AppColors.ERROR
        except ValueError:
            return AppColors.INFO

    elif grade_type == "通过制":
        if grade in ["通过", "合格"]:
            return AppColors.GRADE_PASS
        elif grade in ["不通过", "不合格"]:
            return AppColors.GRADE_FAIL
        else:
            return AppColors.INFO

    else:
        return AppColors.INFO

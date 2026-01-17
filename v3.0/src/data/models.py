"""
NKU成绩查询 v3.0 - 数据模型
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Grade:
    """成绩数据模型"""
    semester_id: str
    semester_name: str
    course_code: str
    course_name: str
    course_type: str
    credits: float
    grade_type: str  # '百分制' | '等级制' | '通过制'
    grade: str  # 'A' | '90分' | '通过'
    gpa: Optional[float]
    score: Optional[float]  # 仅百分制有值
    query_time: Optional[str] = None  # ISO 格式时间戳

    def __post_init__(self):
        """初始化后处理"""
        if self.query_time is None:
            self.query_time = datetime.now().isoformat()


@dataclass
class Semester:
    """学期数据模型"""
    id: str
    display_name: str
    school_year: str
    term: str


@dataclass
class Config:
    """配置数据模型"""
    key: str
    value: str

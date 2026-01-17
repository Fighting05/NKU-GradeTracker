"""
NKU成绩查询 v3.0 - 推送HTML构建
支持PushPlus微信推送
"""

from datetime import datetime


def build_grade_change_html(new_courses, updated_courses) -> str:
    """
    构建成绩变化通知的精美HTML内容（查询模式）

    Args:
        new_courses: 新增课程列表 [Grade, ...]
        updated_courses: 更新课程列表 [{'old': Grade, 'new': Grade}, ...]

    Returns:
        HTML 字符串
    """
    # 如果没有更新课程，说明是查询模式
    if not updated_courses:
        return build_query_result_html(new_courses)

    # 否则是监控模式
    return build_monitor_change_html(new_courses, updated_courses)


def build_query_result_html(grades) -> str:
    """构建成绩查询结果HTML（精美版）"""
    if not grades:
        return "<p>没有成绩数据</p>"

    # 统计数据
    total_credits = sum(g.credits for g in grades)
    gpas = [g.gpa for g in grades if g.gpa is not None]
    avg_gpa = sum(gpas) / len(gpas) if gpas else 0
    gpa_color = "#4CAF50" if avg_gpa >= 3.5 else "#2196F3" if avg_gpa >= 3.0 else "#FF9800"

    # 学期信息（从第一门课程获取）
    semester_name = grades[0].semester_name if grades else "未知学期"

    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <!-- 标题卡片 -->
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; border-radius: 15px 15px 0 0; text-align: center;">
            <h2 style="margin: 0; font-size: 26px;">🎓 NKU 成绩查询</h2>
            <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 16px;">{semester_name}</p>
        </div>

        <!-- 统计卡片 -->
        <div style="background: white; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 15px;">
    """

    # 如果有绩点，显示大号GPA
    if avg_gpa > 0:
        html += f"""
            <div style="text-align: center;">
                <h1 style="margin: 0; color: {gpa_color}; font-size: 42px; font-weight: bold;">{avg_gpa:.2f}</h1>
                <p style="margin: 5px 0 15px 0; color: #666; font-size: 16px;">加权平均绩点</p>
            </div>
        """

    html += f"""
            <div style="display: flex; justify-content: space-around; text-align: center; border-top: 1px solid #eee; padding-top: 15px;">
                <div>
                    <p style="margin: 0; color: #999; font-size: 13px;">课程数</p>
                    <p style="margin: 5px 0 0 0; color: #333; font-size: 22px; font-weight: bold;">{len(grades)}</p>
                </div>
                <div>
                    <p style="margin: 0; color: #999; font-size: 13px;">总学分</p>
                    <p style="margin: 5px 0 0 0; color: #333; font-size: 22px; font-weight: bold;">{total_credits:.1f}</p>
                </div>
            </div>
        </div>

        <!-- 成绩详情 -->
        <div style="background: white; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); border-radius: 0 0 15px 15px;">
            <h3 style="margin: 0 0 15px 0; color: #333; font-size: 18px;">📚 课程成绩明细</h3>
    """

    # 添加每门课程
    for i, grade in enumerate(grades):
        grade_color = _get_grade_color(grade.grade, grade.grade_type)
        bg_color = "#f8f9fa" if i % 2 == 0 else "#ffffff"

        gpa_display = f"绩点 {grade.gpa:.1f}" if grade.gpa else "--"

        html += f"""
        <div style="display: flex; align-items: center; padding: 12px; background: {bg_color}; border-radius: 8px; margin-bottom: 8px;">
            <div style="flex: 1;">
                <h4 style="margin: 0; color: #333; font-size: 15px;">{grade.course_name}</h4>
                <p style="margin: 5px 0 0 0; color: #666; font-size: 13px;">
                    {grade.course_code} · {grade.course_type} · {grade.credits}学分
                </p>
            </div>
            <div style="text-align: right;">
                <span style="display: inline-block; padding: 5px 12px; background: {grade_color}; color: white; border-radius: 15px; font-weight: bold; font-size: 15px;">
                    {grade.grade}
                </span>
                <p style="margin: 5px 0 0 0; color: #666; font-size: 13px;">
                    {gpa_display}
                </p>
            </div>
        </div>
        """

    html += f"""
        </div>

        <!-- 底部信息 -->
        <div style="text-align: center; color: #999; font-size: 12px; margin-top: 15px; padding: 15px;">
            <p>查询时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p style="margin-top: 8px;">🎉 继续加油！</p>
        </div>
    </div>
    """

    return html


def build_monitor_change_html(new_courses, updated_courses) -> str:
    """构建成绩变化监控HTML（精美版）"""
    total_changes = len(new_courses) + len(updated_courses)

    html = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <!-- 标题卡片 -->
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 25px; border-radius: 15px 15px 0 0; text-align: center;">
            <h2 style="margin: 0; font-size: 26px;">🔔 成绩变化通知</h2>
            <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 16px;">检测到 {total_changes} 项变化</p>
        </div>

        <!-- 统计卡片 -->
        <div style="background: white; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 15px;">
            <div style="display: flex; justify-content: space-around; text-align: center;">
                <div>
                    <p style="margin: 0; color: #999; font-size: 13px;">新增课程</p>
                    <p style="margin: 5px 0 0 0; color: #4CAF50; font-size: 28px; font-weight: bold;">{len(new_courses)}</p>
                </div>
                <div>
                    <p style="margin: 0; color: #999; font-size: 13px;">成绩更新</p>
                    <p style="margin: 5px 0 0 0; color: #FF9800; font-size: 28px; font-weight: bold;">{len(updated_courses)}</p>
                </div>
            </div>
        </div>
    """

    # 新增课程
    if new_courses:
        html += f"""
        <div style="background: white; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); border-radius: 10px; margin-bottom: 15px;">
            <h3 style="margin: 0 0 15px 0; color: #4CAF50; font-size: 18px;">✨ 新增课程 ({len(new_courses)}门)</h3>
        """

        for i, grade in enumerate(new_courses):
            grade_color = _get_grade_color(grade.grade, grade.grade_type)
            bg_color = "#f0f9ff" if i % 2 == 0 else "#ffffff"
            gpa_display = f"绩点 {grade.gpa:.1f}" if grade.gpa else "--"

            html += f"""
            <div style="display: flex; align-items: center; padding: 12px; background: {bg_color}; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid #4CAF50;">
                <div style="flex: 1;">
                    <h4 style="margin: 0; color: #333; font-size: 15px;">{grade.course_name}</h4>
                    <p style="margin: 5px 0 0 0; color: #666; font-size: 13px;">
                        {grade.semester_name} | {grade.course_code} | {grade.course_type} | {grade.credits}学分
                    </p>
                </div>
                <div style="text-align: right;">
                    <span style="display: inline-block; padding: 5px 12px; background: {grade_color}; color: white; border-radius: 15px; font-weight: bold; font-size: 15px;">
                        {grade.grade}
                    </span>
                    <p style="margin: 5px 0 0 0; color: #666; font-size: 13px;">
                        {gpa_display}
                    </p>
                </div>
            </div>
            """

        html += "</div>"

    # 更新课程
    if updated_courses:
        html += f"""
        <div style="background: white; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); border-radius: 10px; margin-bottom: 15px;">
            <h3 style="margin: 0 0 15px 0; color: #FF9800; font-size: 18px;">🔄 成绩更新 ({len(updated_courses)}门)</h3>
        """

        for i, item in enumerate(updated_courses):
            old_g = item['old']
            new_g = item['new']
            old_color = _get_grade_color(old_g.grade, old_g.grade_type)
            new_color = _get_grade_color(new_g.grade, new_g.grade_type)
            bg_color = "#fff8e1" if i % 2 == 0 else "#ffffff"

            # 绩点变化
            if old_g.gpa and new_g.gpa:
                gpa_change = f"{old_g.gpa:.1f} → {new_g.gpa:.1f}"
                gpa_emoji = "📈" if new_g.gpa > old_g.gpa else "📉"
            else:
                gpa_change = "--"
                gpa_emoji = ""

            html += f"""
            <div style="padding: 12px; background: {bg_color}; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid #FF9800;">
                <h4 style="margin: 0; color: #333; font-size: 15px;">{new_g.course_name}</h4>
                <p style="margin: 5px 0 0 0; color: #666; font-size: 13px;">
                    {new_g.semester_name} | {new_g.course_code}
                </p>
                <div style="display: flex; align-items: center; margin-top: 10px;">
                    <span style="display: inline-block; padding: 5px 12px; background: {old_color}; color: white; border-radius: 15px; font-weight: bold; font-size: 14px; text-decoration: line-through; opacity: 0.7;">
                        {old_g.grade}
                    </span>
                    <span style="margin: 0 8px; color: #FF9800; font-size: 18px;">→</span>
                    <span style="display: inline-block; padding: 5px 12px; background: {new_color}; color: white; border-radius: 15px; font-weight: bold; font-size: 14px;">
                        {new_g.grade}
                    </span>
                </div>
                <p style="margin: 8px 0 0 0; color: #666; font-size: 13px;">
                    {gpa_emoji} 绩点: {gpa_change}
                </p>
            </div>
            """

        html += "</div>"

    html += f"""
        <!-- 底部信息 -->
        <div style="text-align: center; color: #999; font-size: 12px; margin-top: 15px; padding: 15px; background: white; border-radius: 10px;">
            <p>检测时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p style="margin-top: 8px;">🎉 继续努力！</p>
        </div>
    </div>
    """

    return html


def _get_grade_color(grade_text: str, grade_type: str) -> str:
    """根据成绩获取颜色"""
    if grade_type == "等级制":
        grade_colors = {
            'A': '#4CAF50', 'A-': '#66BB6A',
            'B+': '#42A5F5', 'B': '#2196F3', 'B-': '#1E88E5',
            'C+': '#FFA726', 'C': '#FF9800', 'C-': '#FB8C00',
            'D': '#EF5350', 'F': '#F44336'
        }
        return grade_colors.get(grade_text, '#757575')
    elif grade_type == "百分制":
        try:
            score = float(grade_text)
            if score >= 90:
                return '#4CAF50'
            elif score >= 80:
                return '#2196F3'
            elif score >= 70:
                return '#FF9800'
            elif score >= 60:
                return '#FFC107'
            else:
                return '#F44336'
        except:
            return '#757575'
    elif grade_type == "通过制":
        if grade_text in ['通过', '合格']:
            return '#4CAF50'
        else:
            return '#F44336'
    else:
        return '#757575'

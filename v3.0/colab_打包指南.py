# ======================================================== 
#          NKU 成绩查询系统 v3.0 - APK 云端打包指南 
# ======================================================== 
# 
# 使用方法：
# 1. 将 v3.0 文件夹内的所有内容（main.py, src 文件夹等）压缩成 v3.0.zip
# 2. 访问 https://colab.research.google.com/ 并新建笔记本
# 3. 点击左侧“文件”图标，将 v3.0.zip 上传
# 4. 将下方的代码全部复制到 Colab 的单元格中并运行
# 
# ======================================================== 

import os
from google.colab import files

# 1. 环境基础配置
print("正在配置系统环境...")
!apt-get update -qq
!apt-get install -y -qq libgtk-3-dev libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev ninja-build clang cmake

# 2. 安装 Flutter SDK
if not os.path.exists("/content/flutter"):
    print("正在安装 Flutter SDK (预计2分钟)...")
    !git clone https://github.com/flutter/flutter.git -b stable --depth 1 /content/flutter
    os.environ['PATH'] += ":/content/flutter/bin"
    !flutter config --no-analytics
    !flutter precache
else:
    os.environ['PATH'] += ":/content/flutter/bin"

# 3. 安装 Flet 命令行工具
print("正在安装 Flet...")
!pip install flet

# 4. 准备代码 (请确保已上传 v3.0.zip)
print("正在准备项目文件...")
if os.path.exists("/content/v3.0.zip"):
    !mkdir -p /content/app_project
    !unzip -o -q /content/v3.0.zip -d /content/app_project
else:
    print("❌ 错误：未在 Colab 根目录找到 v3.0.zip。请点击左侧文件夹图标并上传！")
    # 停止执行
    raise SystemExit

# 5. 安装依赖
print("正在安装项目依赖...")
if os.path.exists("/content/app_project/requirements.txt"):
    !pip install -r /content/app_project/requirements.txt

# 6. 执行打包
print("\n--- 开始构建 APK (大约需要5-10分钟，请不要关闭网页) ---")
os.chdir("/content/app_project")
os.environ['PATH'] += ":/content/flutter/bin"
!flet build apk --verbose

# 7. 下载产物
if os.path.exists("build/apk/app-release.apk"):
    print("✅ 打包成功！正在下载...")
    files.download("build/apk/app-release.apk")
else:
    print("❌ 打包失败，请检查上方日志输出。  ")

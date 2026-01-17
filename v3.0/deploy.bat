@echo off
chcp 65001 >nul
echo ========================================
echo   NKU成绩查询 v3.0 - GitHub 部署脚本
echo ========================================
echo.

echo [1/5] 初始化 Git 仓库...
git init
if errorlevel 1 (
    echo 错误：Git 初始化失败，请确认已安装 Git
    pause
    exit /b 1
)

echo [2/5] 添加所有文件...
git add .

echo [3/5] 创建首次提交...
git commit -m "Initial commit: NKU成绩查询 v3.0"

echo.
echo [4/5] 请输入您的 GitHub 仓库地址
echo 格式: https://github.com/YOUR_USERNAME/REPO_NAME.git
set /p REPO_URL="仓库地址: "

echo [5/5] 添加远程仓库并推送...
git remote add origin %REPO_URL%
git branch -M main
git push -u origin main

if errorlevel 1 (
    echo.
    echo 推送失败！可能的原因：
    echo 1. 仓库地址错误
    echo 2. 没有权限（需要登录 GitHub）
    echo 3. 网络问题
    echo.
    echo 请手动执行以下命令：
    echo   git remote add origin %REPO_URL%
    echo   git branch -M main
    echo   git push -u origin main
) else (
    echo.
    echo ========================================
    echo   推送成功！
    echo ========================================
    echo.
    echo 接下来：
    echo 1. 访问您的 GitHub 仓库
    echo 2. 点击 "Actions" 标签
    echo 3. 等待构建完成（约 10-15 分钟）
    echo 4. 下载构建好的 APK 文件
    echo.
)

pause

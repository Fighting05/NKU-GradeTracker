# 部署指南

## 使用 GitHub Actions 自动打包 Android APK

### 步骤 1: 创建 GitHub 仓库

1. 访问 [GitHub](https://github.com)，点击右上角 "+" → "New repository"
2. 填写仓库信息：
   - Repository name: `nku-grades-v3` (或其他名称)
   - Description: `南开大学成绩查询助手 v3.0`
   - 选择 Public 或 Private（推荐 Private）
3. 点击 "Create repository"

### 步骤 2: 推送代码到 GitHub

在项目目录下打开终端，执行：

```bash
# 初始化 git 仓库
git init

# 添加所有文件
git add .

# 创建第一次提交
git commit -m "Initial commit: NKU成绩查询 v3.0"

# 添加远程仓库（替换 YOUR_USERNAME 为你的 GitHub 用户名）
git remote add origin https://github.com/YOUR_USERNAME/nku-grades-v3.git

# 推送到 GitHub
git push -u origin main
```

**如果出现分支名称问题**（有些 git 版本默认是 master），执行：
```bash
git branch -M main
git push -u origin main
```

### 步骤 3: GitHub Actions 自动构建

代码推送后，GitHub Actions 会自动开始构建 Android APK。

**查看构建进度**：
1. 进入你的 GitHub 仓库
2. 点击顶部的 "Actions" 标签
3. 查看正在运行的工作流
4. 等待约 10-15 分钟（首次构建需要下载 Flutter SDK）

**下载 APK**：
1. 构建完成后，点击对应的工作流
2. 滚动到页面底部的 "Artifacts" 部分
3. 点击下载 `nku-grades-android`
4. 解压后得到 APK 文件

### 步骤 4: 手动触发构建

如果想手动触发构建（不需要推送代码）：

1. 进入 GitHub 仓库的 "Actions" 页面
2. 选择 "Build Android APK" 工作流
3. 点击右侧的 "Run workflow" 按钮
4. 选择分支（通常是 main）
5. 点击绿色的 "Run workflow"

### 步骤 5: 安装 APK 到手机

**方法一：直接下载**
1. 在手机浏览器打开 GitHub 仓库的 Actions 页面
2. 下载构建好的 APK
3. 安装（需要开启"允许安装未知来源应用"）

**方法二：通过电脑**
1. 在电脑下载 APK
2. 通过 USB 传输到手机
3. 在手机上安装

---

## 本地打包（可选）

### Windows exe 打包

```bash
# 确保已安装依赖
pip install -r requirements.txt

# 打包
pyinstaller --clean "NKU成绩查询v3.0.spec"

# 生成的 exe 在 dist/ 目录
```

### Android APK 本地打包

**前提条件**：
- 安装 Flutter SDK（约 12GB）
- 配置 Android SDK

**打包命令**：
```bash
flet build apk
```

**首次打包可能需要 1-2 小时**，因为需要下载大量依赖。

建议使用 GitHub Actions 云端打包，更省时省力。

---

## 常见问题

### Q: Actions 构建失败怎么办？
A:
1. 检查 requirements.txt 是否包含所有依赖
2. 查看 Actions 日志，找到具体错误信息
3. 确认 .github/workflows/build.yml 配置正确

### Q: APK 下载后无法安装？
A:
1. 检查手机是否开启"允许安装未知来源应用"
2. 确认 APK 文件没有损坏（重新下载）
3. 检查手机 Android 版本（需要 5.0+）

### Q: 如何更新版本？
A:
1. 修改代码
2. 提交并推送到 GitHub
3. Actions 自动重新构建
4. 下载新的 APK

### Q: Actions 构建时间太长？
A:
- 首次构建需要 10-15 分钟（下载 Flutter SDK）
- 后续构建会使用缓存，约 5-8 分钟
- 这是正常现象，耐心等待即可

### Q: 私有仓库可以用 Actions 吗？
A:
- 可以！GitHub 提供免费的 Actions 使用额度
- Private 仓库每月 2000 分钟免费
- 构建一次约 10 分钟，足够日常使用

---

## 技术支持

如有问题，请查看：
- GitHub Actions 日志（最详细的错误信息）
- Flet 官方文档：https://flet.dev/
- PyInstaller 文档：https://pyinstaller.org/

---

**祝使用愉快！** 🎓

# NKU成绩查询 v3.0

南开大学成绩查询助手 - 跨平台版本（Windows + Android）

## 功能特性

- ✅ WebVPN 自动登录
- ✅ 成绩查询（支持百分制/等级制/通过制）
- ✅ 成绩监控（自动检测新成绩）
- ✅ PushPlus 微信推送通知
- ✅ 统计数据（GPA、平均分、学分统计）
- ✅ 跨平台支持（Windows + Android）

## 下载

### Windows 版本
直接运行 `dist/NKU成绩查询v3.0.exe`

### Android 版本
1. 方式一：从 GitHub Actions 下载
   - 进入仓库的 Actions 页面
   - 点击最新的构建
   - 下载 `nku-grades-android` 文件

2. 方式二：本地打包（需要安装 Flutter SDK）
   ```bash
   flet build apk
   ```

## 使用说明

### 首次使用
1. 打开应用，进入"设置"页面
2. 输入学号和密码
3. 配置 PushPlus Token（可选，用于微信推送）
4. 点击"验证登录"确认账号正确

### 查询成绩
1. 进入"查询"页面
2. 选择学期
3. 点击"查询成绩"
4. 查看成绩列表和统计数据

### 开启监控
1. 进入"监控"页面
2. 设置监控间隔（建议30分钟以上）
3. 点击"开始监控"
4. 有新成绩时会自动推送到微信（需配置 PushPlus）

## PushPlus Token 获取方法

1. 访问 [PushPlus官网](http://www.pushplus.plus/)
2. 使用微信扫码登录
3. 关注"PushPlus推送加"公众号
4. 复制首页显示的 Token
5. 粘贴到应用设置页面

## 技术栈

- **UI框架**: Flet (基于 Flutter)
- **数据存储**: SQLite
- **加密**: AES-CBC (pycryptodome)
- **网络请求**: requests + BeautifulSoup4
- **打包工具**:
  - Windows: PyInstaller
  - Android: Flet build apk (Flutter)

## 开发

### 环境要求
- Python 3.9+
- Flet 0.24.1

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行开发版
```bash
flet run
```

### 打包

#### Windows
```bash
pyinstaller --clean "NKU成绩查询v3.0.spec"
```

#### Android
**方式一：GitHub Actions（推荐）**
- 推送代码到 GitHub
- Actions 自动构建 APK
- 从 Artifacts 下载

**方式二：本地打包**
```bash
flet build apk
```

## 项目结构

```
v3.0/
├── src/
│   ├── core/          # 核心业务逻辑
│   │   ├── auth.py    # WebVPN登录
│   │   ├── grades.py  # 成绩查询
│   │   ├── monitor.py # 监控功能
│   │   └── semester.py# 学期管理
│   ├── data/          # 数据层
│   │   ├── database.py# SQLite操作
│   │   ├── models.py  # 数据模型
│   │   └── storage.py # 跨平台存储
│   ├── services/      # 服务层
│   │   └── email.py   # HTML通知构建
│   ├── ui/            # UI层
│   │   ├── app.py     # 主应用
│   │   ├── theme.py   # 主题配置
│   │   └── pages/     # 各页面
│   └── utils/         # 工具函数
├── main.py            # 入口文件
└── requirements.txt   # 依赖列表
```

## 常见问题

### Windows exe 无法登录
确保 exe 文件包含了 SSL 库文件。重新打包时使用提供的 spec 文件。

### Android 打包失败
检查 Flutter SDK 是否正确安装，或使用 GitHub Actions 云端打包。

### 监控不生效
1. 检查网络连接
2. 确认账号密码正确
3. 查看监控日志了解详细错误

## 更新日志

### v3.0.0 (2026-01-16)
- ✅ 全新 UI 设计（Material Design 3）
- ✅ 跨平台支持（Windows + Android）
- ✅ 数据存储优化（SQLite 替代 JSON）
- ✅ 简化配置（仅保留 PushPlus 推送）
- ✅ 精美 HTML 推送模板
- ✅ 中文字体优化（微软雅黑）

## 许可证

本项目仅供学习交流使用，请勿用于商业用途。

## 致谢

感谢所有使用和支持本项目的同学！

# NKU成绩查询助手
[![zread](https://img.shields.io/badge/Ask_Zread-_.svg?style=for-the-badge&color=00b0aa&labelColor=000000&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQuOTYxNTYgMS42MDAxSDIuMjQxNTZDMS44ODgxIDEuNjAwMSAxLjYwMTU2IDEuODg2NjQgMS42MDE1NiAyLjI0MDFWNC45NjAxQzEuNjAxNTYgNS4zMTM1NiAxLjg4ODEgNS42MDAxIDIuMjQxNTYgNS42MDAxSDQuOTYxNTZDNS4zMTUwMiA1LjYwMDEgNS42MDE1NiA1LjMxMzU2IDUuNjAxNTYgNC45NjAxVjIuMjQwMUM1LjYwMTU2IDEuODg2NjQgNS4zMTUwMiAxLjYwMDEgNC45NjE1NiAxLjYwMDFaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik00Ljk2MTU2IDEwLjM5OTlIMi4yNDE1NkMxLjg4ODEgMTAuMzk5OSAxLjYwMTU2IDEwLjY4NjQgMS42MDE1NiAxMS4wMzk5VjEzLjc1OTlDMS42MDE1NiAxNC4xMTM0IDEuODg4MSAxNC4zOTk5IDIuMjQxNTYgMTQuMzk5OUg0Ljk2MTU2QzUuMzE1MDIgMTQuMzk5OSA1LjYwMTU2IDE0LjExMzQgNS42MDE1NiAxMy43NTk5VjExLjAzOTlDNS42MDE1NiAxMC42ODY0IDUuMzE1MDIgMTAuMzk5OSA0Ljk2MTU2IDEwLjM5OTlaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik0xMy43NTg0IDEuNjAwMUgxMS4wMzg0QzEwLjY4NSAxLjYwMDEgMTAuMzk4NCAxLjg4NjY0IDEwLjM5ODQgMi4yNDAxVjQuOTYwMUMxMC4zOTg0IDUuMzEzNTYgMTAuNjg1IDUuNjAwMSAxMS4wMzg0IDUuNjAwMUgxMy43NTg0QzE0LjExMTkgNS42MDAxIDE0LjM5ODQgNS4zMTM1NiAxNC4zOTg0IDQuOTYwMVYyLjI0MDFDMTQuMzk4NCAxLjg4NjY0IDE0LjExMTkgMS42MDAxIDEzLjc1ODQgMS42MDAxWiIgZmlsbD0iI2ZmZiIvPgo8cGF0aCBkPSJNNCAxMkwxMiA0TDQgMTJaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik00IDEyTDEyIDQiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIxLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPgo8L3N2Zz4K&logoColor=ffffff)](https://zread.ai/Fighting05/NKU-GradeTracker)


你还在为期末成绩每日登录上百次教务系统吗？快来使用我们隆重推出的NKU成绩查询助手，让你远离烦恼，不用一步一步登录教务系统，自动获取，自动提醒。妈妈再也不怕我不知道成绩出啦！！！

## 🎯 项目简介

NKU成绩查询助手是一款专为南开大学学生设计的自动化成绩查询工具。它通过模拟登录WebVPN和教务系统，能够自动获取和监控学生的成绩信息，并支持微信推送通知功能。

## ✨ 主要功能

### 🔍 成绩查询
- 自动登录南开大学WebVPN和教务系统
- 支持查询指定学期的所有课程成绩
- 兼容不同成绩制度（百分制、等级制、通过制）
- 详细的HTML格式成绩报告

### 📡 成绩监控
- 定时自动检查成绩更新
- 智能识别新增课程和成绩变更
- 支持自定义检查间隔（建议不低于5分钟）
- 后台持续运行监控

### 📱 微信推送
- 通过PushPlus服务将成绩推送到微信
- 美观的HTML格式推送内容
- 区分新增课程和更新课程的通知

### 🖥️ 图形界面
- 现代化的GUI界面（基于CustomTkinter）
- 账号信息配置和保存
- 实时日志显示
- 成绩统计和分析

## 🛠️ 技术特性

### 🔧 核心功能
- WebVPN登录模拟
- 教务系统数据抓取
- 动态学期数据获取
- 多种成绩制度解析
- 数据持久化存储

### 🎨 界面优化
- 深色模式主题
- 响应式布局设计
- 流畅的滚动体验
- 直观的状态指示

### 🔒 安全特性
- 加密密码获取工具
- 本地数据存储
- 隐私保护设计

## 📦 安装使用

### 方法一：使用打包版本（推荐）
直接下载并运行 `dist/NKU成绩查询助手.exe` 文件，或者release界面即可。
需要的就是你的学号，以及加密后的登陆密码<img width="298" height="258" alt="image" src="https://github.com/user-attachments/assets/bc50c8f4-e28e-4ea3-941d-28d7202b0ae0" />

获取加密密码步骤：

1. 打开浏览器访问 https://webvpn.nankai.edu.cn

2. 按 F12 打开开发者工具

3. 切换到 Network（网络）标签

4. 在登录页面输入：
   - 学号：输入错误的学号（如 99999）
   （这一步是为了阻止页面跳转，方便找到加密后的密码）
   - 密码：输入你的正确密码

5. 点击登录按钮

6. 在 Network 中找到 "login?vpn-12-o2-iam.nankai.edu.cn&os=web"
   (一般就是第一个请求)

7. 查看请求详情，点击负载(payload)，就可以找到 password 字段的值

8. 复制这个32位字符串即为加密密码

注意：
- 一旦获取到加密密码，就不需要再次获取（除非学校更改加密方式），或者有没有大佬把学校的js加密找出来

### 方法二：源码运行
1. 安装依赖：
```bash
pip install requests beautifulsoup4 customtkinter playwright
playwright install chromium
```

2. 运行GUI版本：
```bash
python nku_grades_gui.py
```

3. 运行命令行版本：
```bash
python nku_grades.py
```

## ⚙️ 配置说明

### 获取加密密码
有两种方式获取加密密码：

1. **手动获取**：通过浏览器开发者工具查看网络请求(更推荐用这个)
2. **自动获取**：使用程序内置的密码获取功能

### 配置PushPlus Token
1. 访问 [PushPlus官网](http://www.pushplus.plus/)
2. 微信扫码注册登录
3. 获取个人Token（不过需要一块钱认证，不是给我哦！！！）
4. 在程序中填入Token即可启用推送功能
5. 或者你自行修改非GUI版推送给你自己

## 📋 使用步骤

### GUI版本使用流程
1. 启动程序
2. 输入学号和加密密码
3. 验证账号（获取学期列表）
4. 选择要查询的学期
5. 点击"查询成绩"获取当前成绩
6. （可选）配置Token后启用监控功能

### 命令行版本使用
程序会引导你选择查询模式和学期。

## 🆕 更新日志

### 最新改进
- 完善日志系统，GUI可以获取详细日志
- 增强监控推送，使用HTML格式显示新成绩详情
- 统一日志接口，支持GUI和命令行双重输出
- 兼容22级百分制和23级等级制成绩

## 🤝 贡献与支持

如果你有任何建议或发现了bug，欢迎提交issue或pull request，或者联系我本人。

## ⚠️ 免责声明

本工具仅供学习交流使用，请合理合法使用。使用本工具造成的任何后果由使用者自行承担。

## 📄 许可证

MIT License

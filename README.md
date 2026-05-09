# Playwright 网络抓包工具

[![Build EXE](https://github.com/Charlielian/fetch_data/actions/workflows/build.yml/badge.svg)](https://github.com/Charlielian/fetch_data/actions/workflows/build.yml)
[![Downloads](https://img.shields.io/github/downloads/Charlielian/fetch_data/total)](https://github.com/Charlielian/fetch_data/releases)

基于 Playwright 的网络抓包工具，提供可视化 GUI 界面，支持一键打包为 EXE。

## 功能特性

- 启动 Chromium 浏览器，手动操作网页
- 实时捕获所有网络请求（XHR、Fetch、JS、CSS、图片等）
- 查看请求/响应头、请求体、响应体
- 按关键词、方法、状态码过滤请求
- 导出为 JSON 文件
- 支持 32 位 / 64 位 Windows

## 下载 EXE

前往 [Releases](https://github.com/Charlielian/fetch_data/releases) 页面下载：

| 文件 | 说明 |
|------|------|
| `PlaywrightCapture_x86.zip` | 32 位版本，适用于旧版 Windows |
| `PlaywrightCapture_x64.zip` | 64 位版本，适用于主流 Windows |

> 不确定选哪个？现代电脑请选择 **x64** 版本。

## 快速使用

1. 下载对应版本的 ZIP 并解压
2. 目标电脑需安装 Chromium 驱动：
   ```bash
   pip install playwright
   playwright install chromium
   ```
3. 双击 `PlaywrightCapture.exe` 启动
4. 输入 URL，点击「启动浏览器」，操作网页即可抓包

## 从源码运行

```bash
# 安装依赖
pip install -r requirements.txt
playwright install chromium

# 运行
python main.py
```

## 自动构建说明

本项目使用 GitHub Actions 自动构建 EXE，支持两种触发方式：

### 方式一：打 Tag 自动发布（推荐）

```bash
git tag v1.0.0
git push origin v1.0.0
```

推送 Tag 后，GitHub Actions 会自动构建 32 位和 64 位 EXE，并发布到 [Releases](https://github.com/Charlielian/fetch_data/releases)。

### 方式二：手动触发

1. 进入仓库的 **Actions** 页面
2. 选择 **Build EXE** 工作流
3. 点击 **Run workflow**

手动触发不会自动发布 Release，构建产物可在 Actions 页面的 Artifacts 中下载（保留 30 天）。

## 项目结构

```
playwright_capture_tool/
├── .github/workflows/build.yml  # GitHub Actions 自动构建
├── main.py                      # 程序入口
├── capture.py                   # 网络请求捕获核心模块
├── gui.py                       # GUI 界面（tkinter 暗色主题）
├── capture_tool.spec            # PyInstaller 打包配置
├── requirements.txt             # Python 依赖清单
├── install.bat                  # 一键安装依赖（Windows）
├── build.bat                    # 一键打包 EXE（Windows）
├── .gitignore                   # Git 忽略规则
└── README.md                    # 使用说明
```

## 使用方法

### 1. 启动工具
运行 `main.py` 或双击 `PlaywrightCapture.exe`

### 2. 打开目标网页
在 URL 输入框输入网址，点击「启动浏览器」

### 3. 操作网页并抓包
在浏览器中正常操作，所有网络请求实时显示在列表中

### 4. 查看请求详情
单击列表中的请求，查看通用信息、请求头、响应头、响应体、请求体

### 5. 过滤请求
- 关键词过滤：输入 URL 关键词
- 方法过滤：选择 GET/POST/PUT 等
- 状态码过滤：输入 200、404 等

### 6. 导出数据
点击「导出 JSON」，选择保存位置

## 常见问题

**Q: 启动时提示"缺少 Playwright 库"？**
```bash
pip install playwright && playwright install chromium
```

**Q: 打包后 EXE 无法启动浏览器？**
目标电脑需要安装 Chromium 驱动（见上方说明）。

**Q: 如何确认 EXE 是 32 位还是 64 位？**
下载时根据文件名区分：`x86` = 32 位，`x64` = 64 位。

## JSON 导出格式

```json
{
  "url": "请求的完整 URL",
  "method": "GET/POST/PUT/DELETE",
  "resource_type": "document/xhr/fetch/script 等",
  "timestamp": "HH:MM:SS.mmm",
  "request_headers": {},
  "request_body": "",
  "status_code": 200,
  "response_headers": {},
  "response_body": "",
  "response_size": 1234
}
```

## License

MIT

@echo off
chcp 65001 >nul
echo ============================================
echo   Playwright 网络抓包工具 - 自动安装脚本
echo ============================================
echo.

echo [1/5] 检查 Python 环境...
python --version
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)
echo.

echo [2/5] 安装 Playwright...
pip install playwright --break-system-packages
if %errorlevel% neq 0 (
    pip install playwright
)
echo.

echo [3/5] 安装浏览器驱动...
playwright install chromium
echo.

echo [4/5] 安装 PyInstaller...
pip install pyinstaller --break-system-packages
if %errorlevel% neq 0 (
    pip install pyinstaller
)
echo.

echo [5/5] 安装完成！
echo.
echo ============================================
echo   使用方法：
echo   1. 直接运行: python main.py
echo   2. 打包 EXE: pyinstaller capture_tool.spec
echo ============================================
echo.
pause

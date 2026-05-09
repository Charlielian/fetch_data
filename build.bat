@echo off
chcp 65001 >nul
echo ============================================
echo   Playwright 网络抓包工具 - 打包脚本
echo ============================================
echo.

echo [注意] 此脚本需要在 32 位 Python 环境下运行
echo        才能生成 32 位的 EXE 文件
echo.
echo 当前 Python 信息：
python -c "import struct; print(f'  位数: {struct.calcsize(\"P\") * 8} 位')"
python --version
echo.

set /p confirm=确认开始打包？(Y/N): 
if /i not "%confirm%"=="Y" (
    echo 已取消打包
    pause
    exit /b 0
)

echo.
echo [1/3] 清理旧的打包文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo.

echo [2/3] 开始打包...
pyinstaller capture_tool.spec --clean
echo.

if %errorlevel% equ 0 (
    echo [3/3] 打包成功！
    echo.
    echo ============================================
    echo   输出目录: dist\PlaywrightCapture\
    echo   可执行文件: dist\PlaywrightCapture\PlaywrightCapture.exe
    echo ============================================
    echo.
    echo [重要] 分发时需要将以下内容一起打包：
    echo   1. dist\PlaywrightCapture\ 整个文件夹
    echo   2. 目标电脑需要安装 Chromium 浏览器驱动
    echo      运行命令: playwright install chromium
    echo.
) else (
    echo [错误] 打包失败，请检查错误信息
)

pause

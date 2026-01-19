@echo off
chcp 65001 >nul
title Musk Tweet ETF Monitor

echo ========================================
echo    Musk Tweet ETF Monitor 启动脚本
echo ========================================
echo.

:: 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

:: 切换到脚本所在目录
cd /d "%~dp0"

:: 检查虚拟环境是否存在
if not exist "venv" (
    echo [信息] 创建虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败
        pause
        exit /b 1
    )
)

:: 激活虚拟环境
echo [信息] 激活虚拟环境...
call venv\Scripts\activate.bat

:: 安装依赖
echo [信息] 检查并安装依赖...
pip install -r requirements.txt -q

:: 安装 Playwright 浏览器（如果需要）
echo [信息] 检查 Playwright 浏览器...
playwright install chromium --with-deps >nul 2>&1

:: 检查配置文件
if not exist "config.json" (
    echo [错误] 未找到 config.json 配置文件
    echo [提示] 请复制 config.example.json 并配置相关参数
    pause
    exit /b 1
)

:: 启动监控程序
echo.
echo [信息] 启动监控程序...
echo [提示] 按 Ctrl+C 可停止程序
echo ========================================
echo.

python -m src.main %*

pause

#!/bin/bash

echo "========================================"
echo "   Musk Tweet ETF Monitor 启动脚本"
echo "========================================"
echo

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到 Python3，请先安装 Python 3.8+"
    exit 1
fi

# 切换到脚本所在目录
cd "$(dirname "$0")"

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "[信息] 创建虚拟环境..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[错误] 创建虚拟环境失败"
        exit 1
    fi
fi

# 激活虚拟环境
echo "[信息] 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "[信息] 检查并安装依赖..."
pip install -r requirements.txt -q

# 安装 Playwright 浏览器（如果需要）
echo "[信息] 检查 Playwright 浏览器..."
playwright install chromium --with-deps 2>/dev/null

# 检查配置文件
if [ ! -f "config.json" ]; then
    echo "[错误] 未找到 config.json 配置文件"
    echo "[提示] 请复制 config.example.json 并配置相关参数"
    exit 1
fi

# 启动监控程序
echo
echo "[信息] 启动监控程序..."
echo "[提示] 按 Ctrl+C 可停止程序"
echo "========================================"
echo

python -m src.main "$@"

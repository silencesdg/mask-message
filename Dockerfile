# 使用 Python 3.10 Slim 作为基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量，防止 Python 产生 .pyc 文件并关闭缓冲输出
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 安装系统级依赖库（Playwright 运行浏览器所需的库）
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# 拷贝依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装 Playwright 的 Chromium 浏览器及其系统依赖库
RUN playwright install chromium
RUN playwright install-deps chromium

# 拷贝项目代码
COPY . .

# 创建数据目录（如果不存在）
RUN mkdir -p data

# 声明容器内部使用的端口（如果以后有 Web UI 的话，目前暂不需要）
# EXPOSE 8000

# 运行监控程序
CMD ["python", "-m", "src.main"]

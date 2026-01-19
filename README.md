# Musk Tweet ETF Monitor

监控 Elon Musk 的推文，使用 LLM 分析财经相关性，查找相关 ETF 及其持仓，并通过企业微信机器人发送通知。

## 功能特性

- 🐦 **推文监控** - 通过 Nitter 实例抓取 Musk 最新推文
- 🤖 **AI 分析** - 使用 LLM (DeepSeek) 分析推文的财经相关性
- 📊 **ETF 检索** - 基于关键词搜索相关 A 股 ETF
- 📈 **持仓分析** - 获取 ETF 前十大持仓并计算股票交集
- 💬 **即时通知** - 通过企业微信机器人推送分析结果

## 快速开始

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd mask-message
```

### 2. 配置文件

复制配置模板并编辑：

```bash
cp config.example.json config.json
```

配置项说明：

```json
{
  "nitter_instances": ["https://nitter.example.com"],  // Nitter 实例列表
  "wechat_webhook_url": "https://qyapi.weixin.qq.com/...",  // 企业微信机器人 Webhook
  "check_interval": 300,  // 检查间隔（秒）
  "llm_config": {
    "api_base": "https://api.deepseek.com/v1",  // LLM API 地址
    "api_key": "your-api-key",  // API 密钥
    "model": "deepseek-chat"  // 模型名称
  }
}
```

### 3. 启动服务

**Windows:**
```batch
start.bat
```

**Linux/macOS:**
```bash
chmod +x start.sh
./start.sh
```

## Docker 部署

### 构建镜像

```bash
docker build -t musk-monitor .
```

### 运行容器

```bash
docker run -d \
  --name musk-monitor \
  -v $(pwd)/config.json:/app/config.json:ro \
  -v $(pwd)/data:/app/data \
  --restart unless-stopped \
  musk-monitor
```

### 查看日志

```bash
docker logs -f musk-monitor
```

## 命令行参数

| 参数 | 说明 |
|------|------|
| `--dry-run` | 运行一次后退出，不保存已处理记录 |
| `--test-notify` | 发送测试通知后退出 |

示例：
```bash
python -m src.main --dry-run
python -m src.main --test-notify
```

## 项目结构

```
mask-message/
├── src/
│   ├── main.py          # 主程序入口
│   ├── monitor.py       # 推文监控模块
│   ├── analyzer.py      # LLM 分析模块
│   ├── market_data.py   # 市场数据模块 (AKShare)
│   ├── notifier.py      # 通知模块
│   └── utils.py         # 工具函数
├── data/                # 数据缓存目录
├── config.json          # 配置文件（需自行创建）
├── requirements.txt     # Python 依赖
├── Dockerfile           # Docker 构建文件
├── start.bat            # Windows 启动脚本
└── start.sh             # Linux 启动脚本
```

## 依赖

- Python 3.8+
- playwright - 浏览器自动化
- feedparser - RSS 解析
- openai - LLM API 调用
- akshare - A 股数据接口
- schedule - 定时任务

## 许可证

MIT License

# 📊 Intraday Market Analyzer

自动交易日盘中市场分析与复盘系统

[![GitHub](https://img.shields.io/badge/GitHub-intraday--market--analyzer-blue)](https://github.com/hu619340515/intraday-market-analyzer)
[![Python](https://img.shields.io/badge/Python-3.7%2B-green)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## ✨ 功能特性

- 📈 **实时指数监控** - 上证指数、深证成指、创业板指、科创50、沪深300
- 💰 **板块资金流向** - TOP10主力净流入板块排行
- 🎯 **机会标的挖掘** - 涨停/跌停、强势股、主力净流入个股
- ⏰ **定时自动报告** - 支持7个时间节点全时段覆盖
- 📱 **飞书群推送** - 自动生成报告并推送到指定群聊
- 🔧 **OpenClaw Skill** - 支持AI Agent直接调用

## 📅 交易日报告时间线

```
09:00 ───────┬─── 📰 券商晨报（研报汇总）
09:25 ───────┼─── 📊 盘前市场分析（开盘前预览）
10:00 ───────┼─── 📊 盘中分析（早盘观察）
11:00 ───────┼─── 📊 盘中分析（上午收盘前）
13:30 ───────┼─── 📊 盘中分析（下午开盘）
14:30 ───────┼─── 📊 盘中分析（尾盘观察）
15:10 ───────┴─── 📋 盘后复盘（全天总结）
```

## 🚀 快速开始

### 安装

```bash
git clone https://github.com/hu619340515/intraday-market-analyzer.git
cd intraday-market-analyzer
```

### 手动执行

```bash
python3 scripts/market_analyzer.py
```

### 设置定时任务

```bash
# 编辑 crontab
crontab -e

# 添加以下行（交易日自动执行）
0 9 * * 1-5 cd /path/to/intraday-market-analyzer && python3 scripts/market_analyzer.py
25 9 * * 1-5 cd /path/to/intraday-market-analyzer && python3 scripts/market_analyzer.py
0 10 * * 1-5 cd /path/to/intraday-market-analyzer && python3 scripts/market_analyzer.py
0 11 * * 1-5 cd /path/to/intraday-market-analyzer && python3 scripts/market_analyzer.py
30 13 * * 1-5 cd /path/to/intraday-market-analyzer && python3 scripts/market_analyzer.py
30 14 * * 1-5 cd /path/to/intraday-market-analyzer && python3 scripts/market_analyzer.py
10 15 * * 1-5 cd /path/to/intraday-market-analyzer && python3 scripts/market_analyzer.py
```

## 📋 报告内容

```
📊 盘中市场分析报告
├── 📈 核心指数表现（5大指数实时数据）
├── 🏭 板块资金流向（TOP10净流入板块）
├── 🎯 机会标的监控
│   ├── 🔥 热点板块（涨幅TOP5）
│   ├── 📈 涨停个股（≥9.8%）
│   ├── 📉 跌停个股（≤-9.8%）
│   ├── 💰 主力净流入TOP10
│   └── 🚀 强势上攻（5%-9.8%）
├── ⚠️ 风险提示
└── 📝 操作建议
```

## 🛠️ 技术架构

### 数据源
- **东方财富实时行情API** - 提供指数、板块、个股实时数据

### API字段映射

| 字段 | 含义 | 单位 |
|------|------|------|
| f43 | 最新价 | /100 |
| f44 | 最高价 | /100 |
| f45 | 最低价 | /100 |
| f46 | 开盘价 | /100 |
| f47 | 成交量 | 手 |
| f48 | 成交额 | 元 |
| f60 | 昨收价 | /100 |
| f170 | 涨跌额 | /100 |
| f22 | 涨跌幅 | % |
| f62 | 主力净流入 | 元 |

### 核心模块

```
market_analyzer.py
├── get_index_data()      # 获取5大指数
├── get_sector_flow()     # 获取板块资金流向
├── get_opportunities()   # 获取机会标的
└── generate_report()     # 生成Markdown报告
```

## 🤖 OpenClaw Skill 使用

作为OpenClaw Skill使用时：

```python
# 执行分析
subprocess.run([
    "python3", 
    "~/.openclaw/workspace/skills/intraday-market-analyzer/scripts/market_analyzer.py"
])

# 读取最新报告
from pathlib import Path
import glob

reports = sorted(Path("memory").glob("market_analysis_*.md"))
if reports:
    with open(reports[-1]) as f:
        report = f.read()
```

## ⚙️ 配置

编辑 `scripts/market_analyzer.py` 中的配置项：

```python
# 飞书群ID（用于推送）
FEISHU_CHAT_ID = "oc_39349fc0e5f46b7c60ea8113da9590df"

# 报告保存路径
MEMORY_DIR = Path("~/.openclaw/workspace/memory").expanduser()
```

## 📝 使用示例

### 生成报告并保存

```bash
python3 scripts/market_analyzer.py
# 输出: memory/market_analysis_20260320_1030.md
```

### 发送到飞书群

```bash
python3 scripts/market_analyzer.py --send-feishu
```

### 指定输出路径

```bash
python3 scripts/market_analyzer.py --output /path/to/report.md
```

## 🔧 故障排查

### 获取不到数据
- 检查是否为交易时间（9:30-11:30, 13:00-15:00）
- 非交易时间接口可能返回空数据
- 检查网络连接：`curl -I https://push2.eastmoney.com`

### 脚本执行失败
```bash
# 检查Python版本
python3 --version  # 需要3.7+

# 检查依赖
curl --version
```

### 定时任务不执行
- 检查crontab配置：`crontab -l`
- 确保使用绝对路径
- 检查脚本权限：`chmod +x market_analyzer.py`

## 📜 许可证

MIT License

## 👤 作者

**旺大神** - [hu619340515](https://github.com/hu619340515)

---

<p align="center">Made with ❤️ by 金角大王 🎣</p>

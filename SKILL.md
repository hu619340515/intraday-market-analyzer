---
name: intraday-market-analyzer
description: 自动交易日盘中市场分析与复盘系统。支持定时获取实时行情数据，生成包含指数走势、板块资金流向、涨停跌停个股、主力净流入等多维度分析报告。适用于交易日盘前（9:25）、盘中（10:00/11:00/13:30/14:30）、盘后（15:10）全时段监控。使用场景：(1) 盘前开盘前预览 (2) 盘中实时跟踪 (3) 盘后全天复盘。
read_when:
  - 用户需要盘中市场分析
  - 用户需要盘后复盘
  - 用户需要涨停跌停监控
  - 用户需要板块资金流向
  - 用户需要设置定时市场报告
  - 用户需要技术分析
  - 用户需要情绪指标
metadata:
  version: 1.2.0
  author: 旺大神
  requires:
    - python3
    - curl
    - agent-browser
---

# Intraday Market Analyzer - 盘中市场分析器

自动交易日行情监控与报告生成系统。

## 功能特性

- ✅ 定时获取实时行情数据（指数、板块、个股）
- ✅ 多维度分析：指数走势、资金流向、涨停跌停、主力净流入
- ✅ 支持7个时间节点：9:00(晨报)、9:25(盘前)、10:00、11:00、13:30、14:30、15:10(复盘)
- ✅ 自动生成Markdown格式报告
- ✅ 可配置定时任务自动推送到飞书群

## 核心数据源

- **首选**：腾讯财经实时行情API（curl）
- **备用**：东方财富数据爬虫（agent-browser模拟浏览器）
- 指数：上证指数、深证成指、创业板指、科创50、沪深300
- 板块：行业板块资金流向排行
- 个股：涨停/跌停、强势股、主力净流入

## 数据获取策略

本技能采用**三层数据获取策略**：

1. **第一层 - 腾讯API**（curl）：快速、轻量，首选方案
2. **第二层 - agent-browser**：模拟真实浏览器访问，避免反爬限制
3. **第三层 - 备用统计**：基于涨停数据估算板块热度

当API返回空数据或连接失败时，自动切换到下一层方案。

## 快速开始

### 1. 运行报告（增强版）

```bash
python3 ~/.openclaw/workspace/skills/intraday-market-analyzer/scripts/market_analyzer.py
```

输出：`memory/market_enhanced_YYYYMMDD_HHMM.md`

**报告包含：**
- ✅ 核心指数表现（5大指数实时数据）
- ✅ 技术分析（RSI、支撑/阻力位、趋势判断）
- ✅ 情绪指标（市场情绪评分、涨跌比、恐慌/贪婪指数）
- ✅ 板块深度分析（热门板块、资金流向、涨停分布）
- ✅ 涨停跌停监控（封板时间、连板数、流通市值）
- ✅ 历史对比（与昨日、上周同日对比）
- ✅ 智能操作建议（基于情绪评分）

### 2. 设置定时任务

添加交易日定时报告：

```bash
# 9:25 盘前分析
25 9 * * 1-5 python3 ~/.openclaw/workspace/skills/intraday-market-analyzer/scripts/market_analyzer.py

# 盘中分析
0 10 * * 1-5 python3 ~/.openclaw/workspace/skills/intraday-market-analyzer/scripts/market_analyzer.py
0 11 * * 1-5 python3 ~/.openclaw/workspace/skills/intraday-market-analyzer/scripts/market_analyzer.py
30 13 * * 1-5 python3 ~/.openclaw/workspace/skills/intraday-market-analyzer/scripts/market_analyzer.py
30 14 * * 1-5 python3 ~/.openclaw/workspace/skills/intraday-market-analyzer/scripts/market_analyzer.py

# 15:10 盘后复盘
10 15 * * 1-5 python3 ~/.openclaw/workspace/skills/intraday-market-analyzer/scripts/market_analyzer.py
```

或使用自动配置脚本：

```bash
python3 ~/.openclaw/workspace/skills/intraday-market-analyzer/scripts/cron_config.py --install
```

### 3. 通过Agent调用

```python
# 执行分析
subprocess.run([
    "python3", 
    "~/.openclaw/workspace/skills/intraday-market-analyzer/scripts/market_analyzer.py"
])

# 读取最新报告
import glob
from pathlib import Path
reports = sorted(Path("memory").glob("market_analysis_*.md"))
if reports:
    with open(reports[-1]) as f:
        report = f.read()
```

## 报告内容结构

### 基础版报告

```markdown
📊 盘中市场分析报告
├── 📈 核心指数表现（5大指数实时数据）
├── 💰 板块资金流向（TOP10净流入板块）
├── 🎯 机会标的监控
│   ├── 🔥 热点板块（涨幅TOP5）
│   ├── 📈 涨停个股（≥9.8%）
│   ├── 📉 跌停个股（≤-9.8%）
│   ├── 💰 主力净流入TOP10
│   └── 🚀 强势上攻（5%-9.8%）
├── ⚠️ 风险提示
└── 📝 操作建议
```

### 增强版报告

```markdown
📊 盘中市场分析报告（增强版）
├── 📈 一、核心指数表现（5大指数）
├── 🔬 二、技术分析
│   ├── 指数技术指标（MA5/10/20, RSI, 支撑/阻力）
│   ├── 趋势判断（多头/空头/震荡）
│   └── RSI指标说明
├── 🎭 三、市场情绪指标
│   ├── 情绪总览（评分、涨跌比、涨跌停比）
│   └── 涨跌家数统计
├── 📊 四、板块分析
│   ├── 热门板块（涨幅TOP10 + 涨停分布）
│   └── 板块资金流向（主力净流入TOP10）
├── 🎯 五、涨停跌停监控
│   ├── 涨停个股（前20，含封板时间、连板数、流通市值）
│   └── 跌停个股
├── 📅 六、历史对比
│   ├── 与昨日对比
│   └── 与上周同日对比
└── 📝 七、操作建议与风险提示
    ├── 智能操作建议（基于情绪评分）
    └── 风险提示
```

## API字段说明

| 字段 | 含义 |
|------|------|
| f43 | 最新价（需/100）|
| f44 | 最高价（需/100）|
| f45 | 最低价（需/100）|
| f46 | 开盘价（需/100）|
| f47 | 成交量（手）|
| f48 | 成交额（元）|
| f60 | 昨收价（需/100）|
| f170 | 涨跌额（需/100）|
| f22 | 涨跌幅（%）|
| f62 | 主力净流入（元）|

## 故障排查

### 获取不到数据
- 检查是否为交易时间（9:30-11:30, 13:00-15:00）
- 检查网络连接：`curl -I https://push2.eastmoney.com`
- 非交易时间接口可能返回空数据
- 尝试agent-browser备用方案：`python3 eastmoney_crawler_browser.py --test`

### agent-browser获取数据失败
```bash
# 检查agent-browser是否安装
agent-browser --version

# 如果没有安装
npm install -g agent-browser
agent-browser install
```

### 脚本执行失败
```bash
# 检查Python版本
python3 --version  # 需要3.7+

# 检查依赖
curl --version
agent-browser --version
```

### 定时任务不执行
- 检查crontab配置：`crontab -l`
- 检查脚本路径是否为绝对路径
- 检查脚本权限：`chmod +x market_analyzer.py`
- agent-browser需要在PATH中：使用绝对路径或确保全局安装

## 技术架构

```
market_analyzer.py (增强版主脚本)
├── technical_analysis.py         # 技术分析引擎
│   ├── TechnicalAnalyzer         # 技术指标计算（MA/RSI/MACD）
│   ├── SentimentAnalyzer         # 市场情绪分析
│   └── HistoryComparator         # 历史数据对比
├── eastmoney_crawler_browser.py  # agent-browser数据获取
│   ├── crawl_index_data()        # 获取指数
│   ├── crawl_limit_up_stocks()   # 获取涨停股
│   ├── crawl_limit_down_stocks() # 获取跌停股
│   ├── crawl_sector_flow()       # 获取板块资金流向
│   ├── crawl_sector_ranking()    # 获取板块排行
│   └── crawl_updown_stats()      # 获取涨跌统计
└── generate_enhanced_report()    # 生成增强版报告

eastmoney_crawler.py (旧版curl备用)
└── (原有curl实现，作为最后备用)

cron_config.py (定时任务配置)
└── 自动设置盘中各时间节点报告
```

### 使用agent-browser直接生成报告

如果主脚本API获取失败，会自动调用agent-browser版本。也可以手动运行：

```bash
# 生成完整市场数据报告（agent-browser版）
python3 ~/.openclaw/workspace/skills/intraday-market-analyzer/scripts/eastmoney_crawler_browser.py

# 测试各模块
python3 ~/.openclaw/workspace/skills/intraday-market-analyzer/scripts/eastmoney_crawler_browser.py --test
```

报告保存位置：`~/.openclaw/workspace/memory/market_crawler_browser_YYYYMMDD_HHMM.md`

## 更新日志

### v1.2.0 (2026-03-25) - 增强版
- ✅ **新增增强版报告** (`enhanced_report.py`)
- ✅ **技术分析引擎** (`technical_analysis.py`)
  - MA移动平均线计算（5日/10日/20日）
  - RSI相对强弱指标
  - 支撑/阻力位计算
  - 趋势判断（多头/空头/震荡）
- ✅ **情绪分析引擎**
  - 市场情绪评分（0-100）
  - 恐慌/贪婪指数
  - 涨跌比、涨跌停比
  - 板块情绪分析
- ✅ **历史对比功能**
  - 与昨日数据对比
  - 与上周同日对比
  - 涨跌停数量变化追踪
- ✅ **智能操作建议**
  - 基于情绪评分的操作提示
  - 动态风险提示

### v1.1.0 (2026-03-25)
- ✅ 新增agent-browser备用数据获取方案
- ✅ 自动三层回退：API → agent-browser → 统计估算
- ✅ 支持完整的涨停数据（含封板时间、连板数、行业）
- ✅ 支持板块资金流向和涨幅排行（API/统计双方案）
- ✅ 支持涨跌家数统计（API/估算双方案）
- ✅ 优化报告格式，封板时间显示为HH:MM

### v1.0.0 (2026-03-20)
- ✅ 初始版本
- ✅ 支持5大指数实时监控
- ✅ 支持涨跌停个股监控
- ✅ 支持板块资金流向
- ✅ 支持定时任务

## 许可证

MIT License

## 作者

旺大神

# 东方财富市场数据爬虫

备用数据获取方案，当标准API失效时通过网页爬取获取市场数据。

## 功能模块

### 1. 涨停榜爬虫 `crawl_limit_up_stocks()`
- 来源：东方财富涨停池API
- 数据：涨停个股列表（代码、名称、价格、连板数、行业、封板时间）
- 备用：无（API稳定）

### 2. 跌停榜爬虫 `crawl_limit_down_stocks()`
- 来源：东方财富跌停池API
- 数据：跌停个股列表

### 3. 板块资金流向爬虫 `crawl_sector_flow()`
- 首选：东方财富板块资金API
- 备用：基于涨停个股统计板块热度
- 数据：板块名称、涨跌幅、主力净流入

### 4. 板块涨幅排行爬虫 `crawl_sector_ranking()`
- 首选：东方财富板块排行API
- 备用：基于涨停个股统计热点板块
- 数据：板块名称、涨跌幅、涨停家数

### 5. 大盘指数爬虫 `crawl_index_data()`
- 首选：腾讯财经API
- 备用：东方财富指数API
- 数据：6大核心指数（上证、深证、创业板、科创50、沪深300、上证50）

## 使用方法

### 生成完整报告
```bash
cd ~/.openclaw/workspace/skills/intraday-market-analyzer/scripts
python3 eastmoney_crawler.py
```

报告保存位置：`~/.openclaw/workspace/memory/market_crawler_YYYYMMDD_HHMM.md`

### 测试各模块
```bash
python3 eastmoney_crawler.py --test
```

### 在Python中调用
```python
from eastmoney_crawler import (
    crawl_index_data,
    crawl_limit_up_stocks,
    crawl_sector_flow,
    generate_full_report
)

# 获取指数数据
index_data = crawl_index_data()

# 获取涨停列表
limit_up = crawl_limit_up_stocks()

# 获取板块资金
sectors = crawl_sector_flow()

# 生成完整报告
result = generate_full_report()
```

## 数据源说明

| 数据类型 | 首选来源 | 备用方案 |
|---------|---------|---------|
| 指数实时行情 | 腾讯财经 API | 东方财富 API |
| 涨停个股 | 东方财富 API | - |
| 跌停个股 | 东方财富 API | - |
| 板块资金流向 | 东方财富 API | 涨停股统计 |
| 板块涨幅排行 | 东方财富 API | 涨停股统计 |
| 涨跌家数统计 | 东方财富 API | - |

## 注意事项

1. **数据延迟**：网页爬取数据可能有1-5分钟延迟
2. **API限制**：频繁请求可能触发限流，建议合理控制调用频率
3. **备用方案**：当主要API失效时，部分数据会基于涨停股统计，可能不完整
4. **交易时间**：非交易时间部分API可能返回空数据

## 故障排查

### 获取不到数据
- 检查网络连接
- 检查是否为交易时间（9:30-11:30, 13:00-15:00）
- 查看具体错误信息

### 板块数据为空
- 东方财富板块API不稳定时会自动切换到备用统计方案
- 备用方案基于涨停股行业分布统计，可能不够全面

## 更新日志

### v1.0.0 (2026-03-24)
- 初始版本
- 支持指数、涨停、跌停、板块数据爬取
- 多层级备用方案

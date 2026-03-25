#!/usr/bin/env python3
"""
Enhanced Market Report Generator - 增强版市场报告生成器
整合技术分析、情绪指标、历史对比
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# 添加脚本目录到路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from eastmoney_crawler_browser import (
    crawl_index_data,
    crawl_limit_up_stocks,
    crawl_limit_down_stocks,
    crawl_sector_flow,
    crawl_sector_ranking,
    crawl_updown_stats
)
from technical_analysis import TechnicalAnalyzer, SentimentAnalyzer, HistoryComparator

MEMORY_DIR = Path("~/.openclaw/workspace/memory").expanduser()


def generate_enhanced_report():
    """生成增强版市场分析报告"""
    print("\n" + "="*70)
    print("📊 增强版盘中市场分析报告")
    print("="*70 + "\n")
    
    now = datetime.now()
    
    # 初始化分析器
    tech_analyzer = TechnicalAnalyzer()
    sentiment_analyzer = SentimentAnalyzer()
    history_comparator = HistoryComparator(MEMORY_DIR)
    
    # 获取基础数据
    print("⏳ 正在获取市场数据...")
    index_data = crawl_index_data()
    limit_up = crawl_limit_up_stocks()
    limit_down = crawl_limit_down_stocks()
    sector_flow = crawl_sector_flow()
    sector_rank = crawl_sector_ranking()
    updown_stats = crawl_updown_stats()
    
    # 技术分析（简化版，基于当前数据）
    print("⏳ 正在进行技术分析...")
    tech_analysis = {}
    for code, name in [
        ("sh000001", "上证指数"),
        ("sz399001", "深证成指"),
        ("sz399006", "创业板指"),
    ]:
        if name in index_data:
            current_price = index_data[name]['price']
            tech_data = tech_analyzer.analyze_index(code, name, current_price)
            
            # 如果K线数据获取失败，用当前数据做简化分析
            if not tech_data.get('ma5'):
                tech_data = _simplified_tech_analysis(index_data[name], name)
            
            tech_analysis[name] = tech_data
    
    # 情绪分析
    print("⏳ 正在计算情绪指标...")
    market_sentiment = sentiment_analyzer.calculate_market_sentiment(
        up_count=updown_stats['up'],
        down_count=updown_stats['down'],
        limit_up=updown_stats['limit_up'],
        limit_down=updown_stats['limit_down']
    )
    
    sector_sentiment = sentiment_analyzer.calculate_sector_sentiment(
        sector_rank.get('all_sectors', [])
    )
    
    # 历史对比
    print("⏳ 正在对比历史数据...")
    current_summary = {
        'limit_up_count': len(limit_up),
        'limit_down_count': len(limit_down),
    }
    history_comparison = history_comparator.compare_with_history(current_summary)
    
    # 生成报告
    print("⏳ 正在生成报告...\n")
    report = _build_report(
        now=now,
        index_data=index_data,
        limit_up=limit_up,
        limit_down=limit_down,
        sector_flow=sector_flow,
        sector_rank=sector_rank,
        updown_stats=updown_stats,
        tech_analysis=tech_analysis,
        market_sentiment=market_sentiment,
        sector_sentiment=sector_sentiment,
        history_comparison=history_comparison
    )
    
    # 保存报告
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"market_enhanced_{now.strftime('%Y%m%d_%H%M')}.md"
    filepath = MEMORY_DIR / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 报告已保存: {filepath}")
    print("\n" + "="*70)
    print(report)
    print("="*70)
    
    return {
        'filepath': str(filepath),
        'report': report,
        'data': {
            'index': index_data,
            'limit_up': limit_up,
            'limit_down': limit_down,
            'tech_analysis': tech_analysis,
            'sentiment': market_sentiment,
        }
    }


def _simplified_tech_analysis(index_data: Dict, name: str) -> Dict:
    """基于当前数据进行简化技术分析"""
    current = index_data['price']
    prev_close = index_data['prev_close']
    high = index_data['high']
    low = index_data['low']
    change_pct = index_data['change_pct']
    
    # 基于涨跌幅判断趋势
    if change_pct > 1.5:
        trend = "📈 强势上涨"
    elif change_pct > 0.5:
        trend = "📊 温和上涨"
    elif change_pct > -0.5:
        trend = "↔️ 震荡整理"
    elif change_pct > -1.5:
        trend = "📊 温和下跌"
    else:
        trend = "📉 弱势下跌"
    
    # 计算今日振幅位置
    amplitude = high - low
    position = (current - low) / amplitude if amplitude > 0 else 0.5
    
    # 估算支撑和阻力（基于今日高低点）
    support = low
    resistance = high
    
    # 基于涨跌幅估算RSI（非常简化的算法）
    # 假设连续同方向运动会累积RSI
    base_rsi = 50
    if change_pct > 0:
        rsi = min(80, base_rsi + change_pct * 5)  # 上涨增加RSI
    else:
        rsi = max(20, base_rsi + change_pct * 5)  # 下跌减少RSI
    
    return {
        'name': name,
        'current': current,
        'ma5': None,
        'ma10': None,
        'ma20': None,
        'rsi': rsi,
        'macd': None,
        'support': support,
        'resistance': resistance,
        'trend': trend,
        'position': position,  # 0-1，当前在今日振幅中的位置
        'is_simplified': True,
    }


def _build_report(now, index_data, limit_up, limit_down, sector_flow, sector_rank,
                  updown_stats, tech_analysis, market_sentiment, sector_sentiment,
                  history_comparison) -> str:
    """构建完整报告"""
    
    report = f"""# 📊 盘中市场分析报告（增强版）

**生成时间**：{now.strftime('%Y-%m-%d %H:%M')}（{now.strftime('%a')}）  
**数据源**：东方财富实时行情 + 技术分析引擎

---

## 📈 一、核心指数表现

| 指数 | 最新价 | 涨跌 | 涨跌幅 | 开盘 | 最高 | 最低 |
|------|--------|------|--------|------|------|------|
"""
    
    for name in ["上证指数", "深证成指", "创业板指", "科创50", "沪深300"]:
        data = index_data.get(name, {})
        if data.get('price'):
            report += f"| **{name}** | {data['price']:.2f} | {data['change']:+.2f} | **{data['change_pct']:+.2f}%** | {data['open']:.2f} | {data['high']:.2f} | {data['low']:.2f} |\n"
        else:
            report += f"| **{name}** | - | - | - | - | - | - |\n"
    
    # 技术分析部分
    report += """
---

## 🔬 二、技术分析

### 📊 指数技术指标

| 指数 | 趋势判断 | MA5 | MA10 | MA20 | RSI | 支撑/阻力 |
|------|----------|-----|------|------|-----|-----------|
"""
    
    for name in ["上证指数", "深证成指", "创业板指"]:
        if name in tech_analysis:
            ta = tech_analysis[name]
            ma5_str = f"{ta['ma5']:.1f}" if ta['ma5'] else "-"
            ma10_str = f"{ta['ma10']:.1f}" if ta['ma10'] else "-"
            ma20_str = f"{ta['ma20']:.1f}" if ta['ma20'] else "-"
            rsi_str = f"{ta['rsi']:.1f}" if ta['rsi'] else "-"
            support_str = f"{ta['support']:.0f}" if ta['support'] else "-"
            resistance_str = f"{ta['resistance']:.0f}" if ta['resistance'] else "-"
            
            report += f"| **{name}** | {ta['trend']} | {ma5_str} | {ma10_str} | {ma20_str} | {rsi_str} | {support_str}/{resistance_str} |\n"
    
    # RSI说明
    has_ma_data = any(ta.get('ma5') for ta in tech_analysis.values())
    
    if has_ma_data:
        report += """
**RSI指标说明**：
- RSI > 70：超买区域，注意回调风险
- RSI 50-70：强势区域
- RSI 30-50：弱势区域  
- RSI < 30：超卖区域，可能存在反弹机会

**移动平均线说明**：
- 📈 多头排列（当前 > MA5 > MA10 > MA20）：强势上涨趋势
- 📉 空头排列（当前 < MA5 < MA10 < MA20）：弱势下跌趋势
- ↔️ 震荡整理：均线交织，趋势不明
"""
    else:
        report += """
> ⚠️ **简化技术分析**：MA数据暂不可用，使用基于今日实时数据的简化分析

**简化指标说明**：
- **RSI（估算）**：基于今日涨跌幅估算，实际值可能有所偏差
- **支撑/阻力**：基于今日高低点
- **趋势判断**：基于涨跌幅和盘中位置
"""
    
    report += """
---

## 🎭 三、市场情绪指标

### 📊 情绪总览

| 指标 | 数值 | 解读 |
|------|------|------|
"""
    
    sentiment = market_sentiment
    report += f"| **市场情绪** | {sentiment['sentiment']} | 评分: {sentiment['score']}/100 |\n"
    report += f"| **涨跌比** | {sentiment['up_down_ratio']:.2f} | 上涨家数/下跌家数 |\n"
    report += f"| **涨跌停比** | {sentiment['limit_ratio']:.1f} | 涨停/跌停 |\n"
    report += f"| **上涨占比** | {sentiment['up_percentage']:.1f}% | 占全市场比例 |\n"
    
    # 涨跌统计
    report += f"""
### 📈 涨跌家数统计

| 上涨家数 | 下跌家数 | 平盘家数 | 涨停 | 跌停 |
|----------|----------|----------|------|------|
| 🔴 {updown_stats['up']} | 🟢 {updown_stats['down']} | ⚪ {updown_stats['flat']} | 🔥 {updown_stats['limit_up']} | ❄️ {updown_stats['limit_down']} |

---

## 📊 四、板块分析

### 🔥 热门板块（涨幅TOP10）

| 排名 | 板块 | 涨跌幅 | 涨停家数 | 情绪 |
|------|------|--------|----------|------|
"""
    
    # 从sector_flow统计涨停家数
    sector_limit_up = {}
    for stock in limit_up:
        industry = stock.get('industry', '其他')
        sector_limit_up[industry] = sector_limit_up.get(industry, 0) + 1
    
    hot_sectors = sector_sentiment.get('hot_sectors', [])
    for i, sector in enumerate(hot_sectors[:10], 1):
        change = sector.get('change_pct', 0)
        limit_count = sector_limit_up.get(sector.get('name', ''), 0)
        
        if change >= 3:
            mood = "🔥 强势"
        elif change >= 1:
            mood = "📈 活跃"
        elif change >= 0:
            mood = "😐 平淡"
        else:
            mood = "📉 弱势"
        
        report += f"| {i} | {sector.get('name', '-')} | **{change:+.2f}%** | {limit_count} | {mood} |\n"
    
    report += f"""
### 💰 板块资金流向（主力净流入TOP10）

| 排名 | 板块 | 主力净流入(亿) | 涨跌幅 | 信号 |
|------|------|----------------|--------|------|
"""
    
    for i, sector in enumerate(sector_flow[:10], 1):
        inflow = sector['main_inflow'] / 10000  # 转换为亿
        change = sector['change_pct']
        
        if inflow > 10 and change > 2:
            signal = "🚀 资金抢筹"
        elif inflow > 5:
            signal = "📥 资金流入"
        elif inflow < -5:
            signal = "📤 资金流出"
        else:
            signal = "➡️ 资金平衡"
        
        report += f"| {i} | **{sector['name']}** | {inflow:+.2f} | {change:+.2f}% | {signal} |\n"
    
    report += f"""
**板块平均涨跌幅**：{sector_sentiment.get('avg_change', 0):+.2f}%

---

## 🎯 五、涨停跌停监控

### 🔥 涨停个股（前20）

| 代码 | 名称 | 价格 | 涨跌幅 | 连板 | 行业 | 封板时间 | 流通市值(亿) |
|------|------|------|--------|------|------|----------|--------------|
"""
    
    for stock in limit_up[:20]:
        lb = f"{stock['lb_count']}连板" if stock['lb_count'] > 1 else "首板"
        fb_time = stock.get('fb_time', 0)
        try:
            fb_time_int = int(fb_time)
            hours = fb_time_int // 10000
            minutes = (fb_time_int % 10000) // 100
            fb_time_str = f"{hours:02d}:{minutes:02d}"
        except:
            fb_time_str = str(fb_time)
        
        circ_mv = stock.get('circ_mv', 0)
        circ_mv_str = f"{circ_mv:.1f}" if circ_mv else "-"
        
        report += f"| {stock['code']} | {stock['name']} | {stock['price']:.2f} | +{stock['change_pct']:.2f}% | {lb} | {stock['industry']} | {fb_time_str} | {circ_mv_str} |\n"
    
    report += f"""
### ❄️ 跌停个股

| 代码 | 名称 | 价格 | 涨跌幅 | 行业 |
|------|------|------|--------|------|
"""
    
    if limit_down:
        for stock in limit_down[:10]:
            report += f"| {stock['code']} | {stock['name']} | {stock['price']:.2f} | {stock['change_pct']:.2f}% | {stock['industry']} |\n"
    else:
        report += "| - | 今日无跌停股 | - | - | - |\n"
    
    # 历史对比
    report += """
---

## 📅 六、历史对比

### 📊 与昨日对比

"""
    
    yesterday = history_comparison.get('yesterday', {})
    if yesterday.get('available'):
        changes = yesterday.get('changes', {})
        hist = yesterday.get('historical', {})
        
        report += "| 指标 | 今日 | 昨日 | 变化 |\n"
        report += "|------|------|------|------|\n"
        
        limit_up_change = changes.get('limit_up', 0)
        limit_up_arrow = "📈" if limit_up_change > 0 else "📉" if limit_up_change < 0 else "➡️"
        report += f"| 涨停家数 | {len(limit_up)} | {hist.get('limit_up_count', '-')} | {limit_up_arrow} {limit_up_change:+.0f} |\n"
        
        limit_down_change = changes.get('limit_down', 0)
        limit_down_arrow = "📈" if limit_down_change > 0 else "📉" if limit_down_change < 0 else "➡️"
        report += f"| 跌停家数 | {len(limit_down)} | {hist.get('limit_down_count', '-')} | {limit_down_arrow} {limit_down_change:+.0f} |\n"
    else:
        report += "> ⚠️ 暂无昨日数据可供对比\n"
    
    report += """
### 📈 与上周同日对比

"""
    
    last_week = history_comparison.get('last_week', {})
    if last_week.get('available'):
        changes = last_week.get('changes', {})
        hist = last_week.get('historical', {})
        
        report += "| 指标 | 今日 | 上周 | 变化 |\n"
        report += "|------|------|------|------|\n"
        
        limit_up_change = changes.get('limit_up', 0)
        limit_up_arrow = "📈" if limit_up_change > 0 else "📉" if limit_up_change < 0 else "➡️"
        report += f"| 涨停家数 | {len(limit_up)} | {hist.get('limit_up_count', '-')} | {limit_up_arrow} {limit_up_change:+.0f} |\n"
        
        limit_down_change = changes.get('limit_down', 0)
        limit_down_arrow = "📈" if limit_down_change > 0 else "📉" if limit_down_change < 0 else "➡️"
        report += f"| 跌停家数 | {len(limit_down)} | {hist.get('limit_down_count', '-')} | {limit_down_arrow} {limit_down_arrow} {limit_down_change:+.0f} |\n"
    else:
        report += "> ⚠️ 暂无上周数据可供对比\n"
    
    # 操作建议
    report += """
---

## 📝 七、操作建议与风险提示

### 💡 操作建议

"""
    
    # 根据情绪生成建议
    score = market_sentiment['score']
    if score >= 70:
        report += """**当前市场情绪高涨，建议：**
- ✅ 适当参与热点板块，但避免追高
- ✅ 关注放量突破的品种，设置止盈位
- ⚠️ 注意控制仓位，留足机动资金
- 📊 重点关注涨停连板股的持续性
"""
    elif score >= 50:
        report += """**当前市场情绪中性偏暖，建议：**
- ✅ 精选个股，关注业绩确定性
- ✅ 可适当加仓优质标的
- 📊 关注板块轮动节奏
- ⏰ 耐心等待回调买入机会
"""
    elif score >= 30:
        report += """**当前市场情绪偏弱，建议：**
- ⚠️ 控制仓位，降低风险敞口
- 🔍 关注超跌反弹机会
- 💰 保留现金，等待更佳买点
- 📉 避免追热点，关注防御性板块
"""
    else:
        report += """**当前市场情绪恐慌，建议：**
- 🛡️ 大幅减仓或空仓观望
- 💰 保留充足现金
- 👀 等待恐慌情绪释放后的机会
- ❌ 避免盲目抄底
"""
    
    report += """
### ⚠️ 风险提示

1. **数据延迟**：行情数据可能存在1-3分钟延迟，请以券商软件为准
2. **技术分析局限**：技术指标仅供参考，不构成买卖建议
3. **情绪指标波动**：市场情绪可能快速变化，需动态跟踪
4. **历史对比偏差**：历史数据不代表未来表现
5. **市场风险**：股市有风险，投资需谨慎

---

*📱 本报告由 Intraday Market Analyzer（增强版）自动生成*  
*🔬 技术分析引擎 v1.0 | 情绪分析引擎 v1.0*  
*📊 数据源：东方财富 + 腾讯财经*
"""
    
    return report


if __name__ == "__main__":
    generate_enhanced_report()

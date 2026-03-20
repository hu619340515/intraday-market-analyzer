#!/usr/bin/env python3
"""
Intraday Market Analyzer - 盘中市场分析器

自动交易日行情监控与报告生成系统。
支持盘前、盘中、盘后全时段监控。

Usage:
    python3 market_analyzer.py                    # 生成报告并保存到文件
    python3 market_analyzer.py --send-feishu      # 生成报告并发送到飞书群
    python3 market_analyzer.py --target CHAT_ID   # 指定飞书群ID
"""

import subprocess
import json
import argparse
from datetime import datetime
from pathlib import Path

# ============ 配置 ============
FEISHU_CHAT_ID = "oc_39349fc0e5f46b7c60ea8113da9590df"  # 默认飞书群ID
MEMORY_DIR = Path("~/.openclaw/workspace/memory").expanduser()


def run_cmd(cmd, timeout=30):
    """执行shell命令并返回输出"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.stdout
    except:
        return None


def get_index_data():
    """获取核心指数数据"""
    indices = {
        "1.000001": "上证指数",
        "0.399001": "深证成指", 
        "0.399006": "创业板指",
        "1.000688": "科创50",
        "1.000300": "沪深300"
    }
    
    data = {}
    for code, name in indices.items():
        try:
            resp = run_cmd(f'curl -s "https://push2.eastmoney.com/api/qt/stock/get?secid={code}&fields=f43,f44,f45,f46,f47,f48,f57,f58,f60,f170"')
            if resp:
                parsed = json.loads(resp)
                if parsed.get('data'):
                    d = parsed['data']
                    data[name] = {
                        'price': float(d.get('f43', 0)) / 100 if d.get('f43') else 0,
                        'high': float(d.get('f44', 0)) / 100 if d.get('f44') else 0,
                        'low': float(d.get('f45', 0)) / 100 if d.get('f45') else 0,
                        'open': float(d.get('f46', 0)) / 100 if d.get('f46') else 0,
                        'prev_close': float(d.get('f60', 0)) / 100 if d.get('f60') else 0,
                        'change': float(d.get('f170', 0)) / 100 if d.get('f170') else 0,
                        'volume_amount': float(d.get('f48', 0)) / 100000000 if d.get('f48') else 0,
                        'volume_hand': float(d.get('f47', 0)) / 10000 if d.get('f47') else 0
                    }
        except Exception as e:
            print(f"Error getting {name}: {e}")
    return data


def get_sector_flow():
    """获取板块资金流向"""
    sectors = []
    try:
        resp = run_cmd('curl -s "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=20&po=1&np=1&fltt=2&invt=2&fid=f20&fs=m:90+t:2&fields=f12,f14,f22,f62,f63"')
        if resp:
            data = json.loads(resp)
            if data.get('data') and data['data'].get('diff'):
                for item in data['data']['diff'][:10]:
                    sectors.append({
                        'name': item.get('f14', ''),
                        'change': float(item.get('f22', 0)),
                        'main_inflow': float(item.get('f62', 0)) / 100000000 if item.get('f62') else 0
                    })
    except Exception as e:
        print(f"Error getting sectors: {e}")
    return sectors


def get_opportunities():
    """获取机会标的"""
    opportunities = {
        'limit_up': [],
        'limit_down': [],
        'strong_momentum': [],
        'big_inflow': [],
        'hot_sectors': []
    }
    
    try:
        # 热点板块
        resp = run_cmd('curl -s "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=10&po=1&np=1&fltt=2&invt=2&fid=f20&fs=m:90+t:2&fields=f12,f14,f22"')
        if resp:
            data = json.loads(resp)
            if data.get('data') and data['data'].get('diff'):
                for item in data['data']['diff'][:5]:
                    opportunities['hot_sectors'].append({
                        'code': item.get('f12', ''),
                        'name': item.get('f14', ''),
                        'change': float(item.get('f22', 0))
                    })
        
        # 涨跌停个股
        resp = run_cmd('curl -s "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=100&po=1&np=1&fltt=2&invt=2&fid=f12&fs=m:0+t:6,m:0+t:13,m:1+t:2,m:1+t:23&fields=f12,f13,f14,f2,f22"')
        if resp:
            data = json.loads(resp)
            if data.get('data') and data['data'].get('diff'):
                for item in data['data']['diff']:
                    change = float(item.get('f22', 0))
                    name = item.get('f14', '')
                    code = item.get('f12', '')
                    price = float(item.get('f2', 0)) / 100 if item.get('f2') else 0
                    
                    if change >= 9.8:
                        opportunities['limit_up'].append({'code': code, 'name': name, 'price': price, 'change': change})
                    elif change <= -9.8:
                        opportunities['limit_down'].append({'code': code, 'name': name, 'price': price, 'change': change})
                    elif change >= 5:
                        opportunities['strong_momentum'].append({'code': code, 'name': name, 'price': price, 'change': change})
        
        # 主力净流入
        resp = run_cmd('curl -s "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=20&po=1&np=1&fltt=2&invt=2&fid=f62&fs=m:0+t:6,m:0+t:13,m:1+t:2,m:1+t:23&fields=f12,f13,f14,f2,f3,f62"')
        if resp:
            data = json.loads(resp)
            if data.get('data') and data['data'].get('diff'):
                for item in data['data']['diff'][:15]:
                    inflow = float(item.get('f62', 0)) / 10000
                    if inflow > 5000:
                        opportunities['big_inflow'].append({
                            'code': item.get('f12', ''),
                            'name': item.get('f14', ''),
                            'price': float(item.get('f2', 0)) / 100 if item.get('f2') else 0,
                            'change': float(item.get('f3', 0)) / 100 if item.get('f3') else 0,
                            'inflow': inflow
                        })
    except Exception as e:
        print(f"Error getting opportunities: {e}")
    
    return opportunities


def generate_report():
    """生成分析报告"""
    now = datetime.now()
    index_data = get_index_data()
    sector_flow = get_sector_flow()
    opportunities = get_opportunities()
    
    report = f"""# 📊 盘中市场分析报告
**时间**：{now.strftime('%Y-%m-%d %H:%M')}（{now.strftime('%a')}）  
**数据节点**：盘中实时监控

---

## 📈 核心指数表现

| 指数 | 最新价 | 涨跌 | 涨跌幅 | 开盘 | 最高 | 最低 | 成交额(亿) |
|------|--------|------|--------|------|------|------|------------|
"""
    
    total_amount = 0
    for name, data in index_data.items():
        if data.get('price'):
            change_pct = ((data['price'] - data['prev_close']) / data['prev_close'] * 100) if data['prev_close'] else 0
            report += f"| **{name}** | {data['price']:.2f} | {data['change']:.2f} | **{change_pct:+.2f}%** | {data['open']:.2f} | {data['high']:.2f} | {data['low']:.2f} | {data['volume_amount']:.0f} |\n"
            total_amount += data['volume_amount']
    
    report += f"\n**两市合计成交额**：约 **{total_amount:.0f} 亿元**\n\n"
    
    report += """---

## 🏭 板块资金流向（TOP10）

| 板块 | 涨跌幅 | 主力净流入(亿) |
|------|--------|----------------|
"""
    for sector in sector_flow[:10]:
        report += f"| {sector['name']} | {sector['change']:+.2f}% | {sector['main_inflow']:+.2f} |\n"
    
    report += """
---

## 🎯 机会标的监控

### 🔥 热点板块（涨幅TOP5）

| 板块 | 涨幅 | 关注方向 |
|------|------|----------|
"""
    if opportunities['hot_sectors']:
        for sector in opportunities['hot_sectors']:
            report += f"| {sector['name']} | **{sector['change']:+.2f}%** | 板块内龙头、强势股 |\n"
    else:
        report += "| - | - | - |\n"
    
    report += """
### 📈 涨停个股（涨幅≥9.8%）

| 代码 | 名称 | 最新价 | 涨幅 | 信号 |
|------|------|--------|------|------|
"""
    if opportunities['limit_up']:
        for stock in opportunities['limit_up'][:15]:
            signal = "🔥封板" if stock['change'] >= 10 else "📈冲击"
            report += f"| {stock['code']} | {stock['name']} | {stock['price']:.2f} | **+{stock['change']:.2f}%** | {signal} |\n"
    else:
        report += "| - | 暂无涨停个股 | - | - | - |\n"
    
    report += f"\n**涨停家数**：{len(opportunities['limit_up'])} 只\n\n"
    
    report += """### 📉 跌停个股（跌幅≤-9.8%）

| 代码 | 名称 | 最新价 | 跌幅 | 信号 |
|------|------|--------|------|------|
"""
    if opportunities['limit_down']:
        for stock in opportunities['limit_down'][:10]:
            report += f"| {stock['code']} | {stock['name']} | {stock['price']:.2f} | **{stock['change']:.2f}%** ⚠️ | 规避 |\n"
        report += f"\n**跌停家数**：{len(opportunities['limit_down'])} 只\n\n"
    else:
        report += "| - | 暂无跌停个股 | - | - | - |\n\n"
    
    report += """### 💰 主力净流入TOP10（大单资金）

| 代码 | 名称 | 最新价 | 涨跌幅 | 净流入(万) | 信号 |
|------|------|--------|--------|------------|------|
"""
    if opportunities['big_inflow']:
        for stock in opportunities['big_inflow'][:10]:
            signal = "💪强势" if stock['change'] > 0 else "🔄吸筹"
            report += f"| {stock['code']} | {stock['name']} | {stock['price']:.2f} | {stock['change']:+.2f}% | {stock['inflow']:.0f} | {signal} |\n"
    else:
        report += "| - | 暂无数据 | - | - | - | - |\n"
    
    report += """
### 🚀 强势上攻（涨幅5%-9.8%）

| 代码 | 名称 | 最新价 | 涨幅 |
|------|------|--------|------|
"""
    if opportunities['strong_momentum']:
        seen = {s['code'] for s in opportunities['limit_up']}
        strong = [s for s in opportunities['strong_momentum'] if s['code'] not in seen]
        for stock in strong[:15]:
            report += f"| {stock['code']} | {stock['name']} | {stock['price']:.2f} | +{stock['change']:.2f}% |\n"
    else:
        report += "| - | 暂无数据 | - | - |\n"
    
    report += """
---

## ⚠️ 风险提示

1. **追高风险**：涨停个股注意开板风险，不追高
2. **分化行情**：深强沪弱格局持续，注意板块轮动
3. **量能变化**：关注成交额能否持续放大

---

## 📝 操作建议

- **短线机会**：关注板块资金流入前5名中的强势股
- **风险提示**：避免追高风险，关注放量突破后的回踩机会
- **仓位管理**：建议保持半仓左右，留足资金应对波动

---

*📱 本报告由 Intraday Market Analyzer 自动生成*  
*🔧 GitHub: https://github.com/wangdashen/intraday-market-analyzer*
"""
    
    return report


def save_report(report):
    """保存报告到文件"""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"market_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    filepath = MEMORY_DIR / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 报告已保存: {filepath}")
    return filepath


def send_to_feishu(report, chat_id=None):
    """发送报告到飞书群（通过OpenClaw message工具）"""
    target = chat_id or FEISHU_CHAT_ID
    
    # 生成一个发送脚本，通过OpenClaw执行
    cmd = f'openclaw message send --channel feishu --target "{target}" --message "{report[:3000]}..."'
    print(f"\n📤 发送命令: {cmd}")
    print("\n💡 提示: 在OpenClaw Agent中可以直接使用 message 工具发送")
    
    return True


def main():
    parser = argparse.ArgumentParser(description='Intraday Market Analyzer')
    parser.add_argument('--send-feishu', action='store_true', help='发送到飞书群')
    parser.add_argument('--target', type=str, help='指定飞书群ID')
    parser.add_argument('--output', type=str, help='指定输出文件路径')
    
    args = parser.parse_args()
    
    print("📊 开始生成盘中市场分析报告...")
    report = generate_report()
    
    # 保存报告
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ 报告已保存: {args.output}")
    else:
        save_report(report)
    
    # 发送到飞书
    if args.send_feishu:
        send_to_feishu(report, args.target)
    
    # 输出报告内容
    print("\n" + "="*60)
    print(report)
    print("="*60)
    
    print("\n✅ 分析完成！")
    return report


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
详细盘后复盘分析器
生成包含多维度数据的专业复盘报告
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict

MEMORY_DIR = Path("~/.openclaw/workspace/memory").expanduser()


def run_curl(url: str, timeout: int = 30, referer: str = None, encoding: str = 'utf-8') -> str:
    """执行curl请求"""
    try:
        cmd = ["curl", "-s", url, "-H", f"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"]
        if referer:
            cmd.extend(["-H", f"Referer: {referer}"])
        
        result = subprocess.run(cmd, capture_output=True, timeout=timeout)
        for enc in [encoding, 'gbk', 'utf-8']:
            try:
                return result.stdout.decode(enc)
            except:
                continue
        return result.stdout.decode('utf-8', errors='ignore')
    except Exception as e:
        return ""


def get_index_detail():
    """获取指数详细数据"""
    indices = {
        "sh000001": "上证指数",
        "sz399001": "深证成指", 
        "sz399006": "创业板指",
        "sh000688": "科创50",
        "sh000300": "沪深300",
        "sh000016": "上证50"
    }
    
    codes = ",".join(indices.keys())
    url = f"https://qt.gtimg.cn/q={codes}"
    resp = run_curl(url, encoding='gbk')
    
    result = {}
    import re
    for line in resp.strip().split(";"):
        line = line.strip()
        if "=" not in line or '=""' in line:
            continue
        
        match = re.search(r'v_(sh\d+|sz\d+)=\"([^\"]+)\"', line)
        if match:
            code = match.group(1)
            fields = match.group(2).split("~")
            
            if len(fields) >= 35:
                try:
                    name = indices.get(code, code)
                    result[name] = {
                        "code": code,
                        "close": float(fields[3]),
                        "open": float(fields[5]),
                        "high": float(fields[33]),
                        "low": float(fields[34]),
                        "prev_close": float(fields[4]),
                        "change": float(fields[31]),
                        "change_pct": float(fields[32]),
                        "volume": float(fields[36]) if len(fields) > 36 else 0,
                        "amount": float(fields[37]) if len(fields) > 37 else 0,
                    }
                except:
                    continue
    return result


def get_limit_up_detail():
    """获取详细涨停数据"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from eastmoney_crawler import crawl_limit_up_stocks, crawl_limit_down_stocks
    
    limit_up = crawl_limit_up_stocks()
    limit_down = crawl_limit_down_stocks()
    return limit_up, limit_down


def analyze_limit_up(limit_up: List[Dict]) -> Dict:
    """分析涨停数据"""
    analysis = {
        "total": len(limit_up),
        "first_board": [],
        "continuous": [],
        "by_industry": {},
        "by_time": {}
    }
    
    for stock in limit_up:
        lb = stock.get('lb_count', 0)
        if lb > 1:
            analysis["continuous"].append({
                "code": stock['code'],
                "name": stock['name'],
                "boards": lb,
                "industry": stock.get('industry', '')
            })
        else:
            analysis["first_board"].append(stock)
        
        industry = stock.get('industry', '其他')
        if industry not in analysis["by_industry"]:
            analysis["by_industry"][industry] = []
        analysis["by_industry"][industry].append(stock)
        
        fb_time = str(stock.get('fb_time', ''))
        if len(fb_time) >= 2:
            hour = fb_time[:2]
            if hour not in analysis["by_time"]:
                analysis["by_time"][hour] = []
            analysis["by_time"][hour].append(stock)
    
    analysis["continuous"].sort(key=lambda x: x['boards'], reverse=True)
    analysis["by_industry"] = dict(sorted(
        analysis["by_industry"].items(), 
        key=lambda x: len(x[1]), 
        reverse=True
    ))
    
    return analysis


def generate_detailed_report():
    """生成详细复盘报告"""
    print("\n" + "="*70)
    print("详细盘后复盘报告")
    print("="*70 + "\n")
    
    now = datetime.now()
    
    print("正在获取指数数据...")
    index_data = get_index_detail()
    
    print("正在获取涨停数据...")
    limit_up, limit_down = get_limit_up_detail()
    limit_analysis = analyze_limit_up(limit_up)
    
    # 计算统计数据
    total_amount = sum(idx.get('amount', 0) for idx in index_data.values()) / 10000
    avg_change = sum(idx.get('change_pct', 0) for idx in index_data.values()) / len(index_data) if index_data else 0
    
    # 生成报告
    report_lines = []
    report_lines.append("# 详细盘后复盘报告")
    report_lines.append("")
    report_lines.append(f"**报告时间**: {now.strftime('%Y年%m月%d日 %H:%M')}")
    report_lines.append("**数据来源**: 腾讯财经、东方财富")
    report_lines.append("**报告类型**: 盘后深度复盘")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## 一、大盘综述")
    report_lines.append("")
    report_lines.append("### 1.1 核心指数收盘")
    report_lines.append("")
    report_lines.append("| 指数 | 收盘 | 开盘 | 最高 | 最低 | 涨跌 | 涨跌幅 | 成交额(亿) |")
    report_lines.append("|------|------|------|------|------|------|--------|-----------|")
    
    for name in ["上证指数", "深证成指", "创业板指", "科创50", "沪深300", "上证50"]:
        if name in index_data:
            d = index_data[name]
            report_lines.append(f"| **{name}** | {d['close']:.2f} | {d['open']:.2f} | {d['high']:.2f} | {d['low']:.2f} | {d['change']:+.2f} | {d['change_pct']:+.2f}% | {d['amount']/10000:.0f} |")
    
    report_lines.append("")
    report_lines.append("**关键指标**:")
    report_lines.append(f"- 两市合计成交额: **{total_amount/10000:.2f}万亿**")
    report_lines.append(f"- 平均涨跌幅: **{avg_change:+.2f}%**")
    report_lines.append(f"- 涨停家数: **{len(limit_up)}只**")
    report_lines.append(f"- 跌停家数: **{len(limit_down)}只**")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## 二、涨停深度分析")
    report_lines.append("")
    report_lines.append("### 2.1 涨停概览")
    report_lines.append("")
    report_lines.append("| 指标 | 数值 |")
    report_lines.append("|------|------|")
    report_lines.append(f"| 涨停总数 | **{len(limit_up)}只** |")
    report_lines.append(f"| 首板数量 | **{len(limit_analysis['first_board'])}只** |")
    report_lines.append(f"| 连板数量 | **{len(limit_analysis['continuous'])}只** |")
    
    if limit_analysis['continuous']:
        highest = limit_analysis['continuous'][0]
        report_lines.append(f"| 最高连板 | **{highest['boards']}连板** ({highest['name']}) |")
    else:
        report_lines.append("| 最高连板 | **1板** |")
    
    report_lines.append(f"| 跌停数量 | **{len(limit_down)}只** |")
    report_lines.append("")
    report_lines.append("### 2.2 连板梯队")
    report_lines.append("")
    
    if limit_analysis['continuous']:
        report_lines.append("| 连板数 | 个股 | 行业 |")
        report_lines.append("|--------|------|------|")
        for item in limit_analysis['continuous'][:15]:
            report_lines.append(f"| **{item['boards']}连板** | {item['name']}({item['code']}) | {item['industry']} |")
    else:
        report_lines.append("> 今日无连板个股(除首板外)")
    
    report_lines.append("")
    report_lines.append("### 2.3 涨停行业分布")
    report_lines.append("")
    report_lines.append("| 排名 | 行业 | 涨停数 | 代表个股 |")
    report_lines.append("|------|------|--------|----------|")
    
    for i, (industry, stocks) in enumerate(list(limit_analysis['by_industry'].items())[:10], 1):
        representatives = ", ".join([s['name'] for s in stocks[:3]])
        report_lines.append(f"| {i} | **{industry}** | {len(stocks)} | {representatives} |")
    
    report_lines.append("")
    report_lines.append("### 2.4 涨停时间分布")
    report_lines.append("")
    report_lines.append("| 时间段 | 涨停数 | 占比 | 特征 |")
    report_lines.append("|--------|--------|------|------|")
    
    time_slots = {
        "09": "早盘抢筹",
        "10": "早盘走强", 
        "11": "上午尾盘",
        "13": "下午开盘",
        "14": "下午震荡",
        "15": "尾盘封板"
    }
    
    for hour, desc in time_slots.items():
        count = len(limit_analysis['by_time'].get(hour, []))
        if count > 0:
            pct = count / len(limit_up) * 100
            report_lines.append(f"| {hour}:00-{hour}:59 | {count}只 | {pct:.1f}% | {desc} |")
    
    report_lines.append("")
    report_lines.append("### 2.5 首板精选(部分)")
    report_lines.append("")
    report_lines.append("| 代码 | 名称 | 价格 | 行业 | 封板时间 |")
    report_lines.append("|------|------|------|------|----------|")
    
    for stock in limit_analysis['first_board'][:15]:
        fb_time = str(stock.get('fb_time', ''))
        fb_str = f"{fb_time[:2]}:{fb_time[2:4]}" if len(fb_time) >= 4 else fb_time
        report_lines.append(f"| {stock['code']} | {stock['name']} | {stock['price']:.2f} | {stock.get('industry', '-')} | {fb_str} |")
    
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## 三、板块分析")
    report_lines.append("")
    report_lines.append("### 3.1 热点板块排行")
    report_lines.append("")
    report_lines.append("| 排名 | 板块 | 涨停家数 | 板块强度 |")
    report_lines.append("|------|------|----------|----------|")
    
    for i, (industry, stocks) in enumerate(list(limit_analysis['by_industry'].items())[:15], 1):
        intensity = "🔥🔥🔥" if len(stocks) >= 8 else "🔥🔥" if len(stocks) >= 4 else "🔥"
        report_lines.append(f"| {i} | {industry} | {len(stocks)} | {intensity} |")
    
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## 四、市场情绪")
    report_lines.append("")
    report_lines.append("### 4.1 涨跌家数统计")
    report_lines.append("")
    report_lines.append("| 市场情绪 | 判断 |")
    report_lines.append("|----------|------|")
    report_lines.append(f"| 涨停家数 | {len(limit_up)}只 |")
    report_lines.append(f"| 跌停家数 | {len(limit_down)}只 |")
    
    if limit_analysis['continuous']:
        report_lines.append(f"| 连板高度 | {limit_analysis['continuous'][0]['boards']}板 |")
    else:
        report_lines.append("| 连板高度 | 1板 |")
    
    report_lines.append("")
    report_lines.append("### 4.2 情绪判断")
    report_lines.append("")
    
    # 情绪判断
    if len(limit_up) >= 80:
        sentiment = "极度高涨"
    elif len(limit_up) >= 50:
        sentiment = "非常活跃"
    elif len(limit_up) >= 30:
        sentiment = "活跃"
    else:
        sentiment = "一般"
    
    status = "🔴🔴🔴 " + sentiment if len(limit_up) >= 80 else "🔴🔴 " + sentiment if len(limit_up) >= 50 else "🔴 " + sentiment if len(limit_up) >= 30 else "🟡 " + sentiment
    
    if len(limit_down) == 0:
        status += ", 无跌停"
    
    report_lines.append(f"**今日情绪**: {status}")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## 五、重点个股")
    report_lines.append("")
    report_lines.append("### 5.1 最高连板")
    report_lines.append("")
    
    if limit_analysis['continuous']:
        top = limit_analysis['continuous'][0]
        report_lines.append(f"**{top['name']}** ({top['code']}) - **{top['boards']}连板**")
        report_lines.append("")
        report_lines.append(f"- 所属行业: {top['industry']}")
        report_lines.append(f"- 连板高度: 市场最高")
        report_lines.append(f"- 带动作用: 引领{top['industry']}板块")
        report_lines.append("")
    
    report_lines.append("### 5.2 一字板/快速板(封板时间<10:00)")
    report_lines.append("")
    report_lines.append("| 个股 | 封板时间 | 行业 | 备注 |")
    report_lines.append("|------|----------|------|------|")
    
    early_boards = []
    for stock in limit_up:
        fb_time = str(stock.get('fb_time', ''))
        if fb_time.startswith('09') or fb_time.startswith('10'):
            early_boards.append(stock)
    
    for stock in early_boards[:10]:
        fb_time = str(stock.get('fb_time', ''))
        fb_str = f"{fb_time[:2]}:{fb_time[2:4]}" if len(fb_time) >= 4 else fb_time
        report_lines.append(f"| {stock['name']} | {fb_str} | {stock.get('industry', '-')} | 早盘强势 |")
    
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## 六、明日展望")
    report_lines.append("")
    report_lines.append("### 6.1 关注方向")
    report_lines.append("")
    report_lines.append("1. **连板梯队**: 关注最高连板股的持续性")
    report_lines.append("2. **板块效应**: 电力板块能否持续强势")
    report_lines.append("3. **首板晋级**: 今日首板明日的晋级机会")
    report_lines.append("")
    report_lines.append("### 6.2 风险提示")
    report_lines.append("")
    report_lines.append("- 涨停家数过多, 注意分化风险")
    report_lines.append("- 连板高度有限, 注意接力风险")
    report_lines.append("- 关注指数能否持续反弹")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## 七、数据汇总")
    report_lines.append("")
    report_lines.append("| 指标 | 数值 | 备注 |")
    report_lines.append("|------|------|------|")
    
    sh_index = index_data.get('上证指数', {})
    report_lines.append(f"| 上证指数 | {sh_index.get('close', '-')} | +{sh_index.get('change_pct', 0):.2f}% |")
    report_lines.append(f"| 涨停家数 | {len(limit_up)} | 不含ST |")
    
    if limit_analysis['continuous']:
        top = limit_analysis['continuous'][0]
        report_lines.append(f"| 最高连板 | {top['boards']}板 | {top['name']} |")
    else:
        report_lines.append("| 最高连板 | 1板 | - |")
    
    if limit_analysis['by_industry']:
        top_industry = list(limit_analysis['by_industry'].items())[0]
        report_lines.append(f"| 最强板块 | {top_industry[0]} | {len(top_industry[1])}只涨停 |")
    
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("*本报告由详细盘后复盘分析器生成*")
    report_lines.append(f"*数据截止时间: {now.strftime('%H:%M')}*")
    report_lines.append("*仅供参考, 不构成投资建议*")
    
    report = "\n".join(report_lines)
    
    # 保存报告
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"detailed_review_{now.strftime('%Y%m%d_%H%M')}.md"
    filepath = MEMORY_DIR / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n详细报告已保存: {filepath}")
    print("\n" + "="*70)
    print(report)
    print("="*70)
    
    return {
        "filepath": str(filepath),
        "report": report
    }


if __name__ == "__main__":
    generate_detailed_report()

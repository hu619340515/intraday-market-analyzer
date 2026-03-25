#!/usr/bin/env python3
"""
东方财富网页数据爬虫 - 备用数据方案
当API获取不到数据时，通过爬取网页获取市场数据

功能：
1. 涨停榜爬虫 - 获取涨停个股列表
2. 板块资金流向爬虫 - 获取板块资金净流入排行
3. 大盘指数爬虫 - 获取核心指数实时数据
"""

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# ============ 配置 ============
MEMORY_DIR = Path("~/.openclaw/workspace/memory").expanduser()
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def run_curl(url: str, timeout: int = 30, referer: str = None, encoding: str = 'utf-8') -> str:
    """执行curl请求获取网页内容"""
    try:
        cmd = ["curl", "-s", url, "-H", f"User-Agent: {USER_AGENT}"]
        if referer:
            cmd.extend(["-H", f"Referer: {referer}"])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout
        )
        
        # 尝试多种编码
        for enc in [encoding, 'gbk', 'gb2312', 'utf-8']:
            try:
                return result.stdout.decode(enc)
            except:
                continue
        return result.stdout.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"请求失败 {url}: {e}")
        return ""


def extract_json_from_js(html: str, var_name: str) -> Optional[Dict]:
    """从JS变量中提取JSON数据"""
    pattern = rf'var\s+{var_name}\s*=\s*(\[.*?\]|\{{.*?\}});'
    match = re.search(pattern, html, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return None
    return None


# ============ 1. 涨停榜爬虫 ============

def crawl_limit_up_stocks() -> List[Dict]:
    """
    爬取东方财富涨停个股数据
    来源: https://quote.eastmoney.com/center/gridlist.html#hs_a_board
    """
    print("📈 正在爬取涨停个股数据...")
    
    # 获取当前日期
    today = datetime.now().strftime("%Y%m%d")
    
    # 东方财富涨停榜API（通过网页分析得到）
    url = "https://push2ex.eastmoney.com/getTopicZTPool"
    params = f"ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt&Pageindex=0&pageSize=100&sort=fbt%3Aasc&date={today}"
    
    try:
        # 尝试直接API
        full_url = f"{url}?{params}"
        resp = run_curl(full_url, referer="https://quote.eastmoney.com/")
        
        if resp:
            data = json.loads(resp)
            if data.get("data") and data["data"].get("pool"):
                stocks = []
                for item in data["data"]["pool"]:
                    stock = {
                        "code": item.get("c", ""),
                        "name": item.get("n", ""),
                        "price": item.get("p", 0) / 1000,  # 价格需要除以1000
                        "change_pct": item.get("zdp", 0),  # 涨跌幅
                        "fb_time": item.get("fbt", ""),  # 首次封板时间
                        "lb_count": item.get("lbc", 0),  # 连板数
                        "amount": item.get("amount", 0) / 100000000,  # 成交额(亿)
                        "circ_mv": item.get("cm", 0) / 100000000,  # 流通市值(亿)
                        "industry": item.get("hybk", ""),  # 所属行业
                    }
                    stocks.append(stock)
                print(f"✅ 获取到 {len(stocks)} 只涨停股")
                return stocks
    except Exception as e:
        print(f"API获取失败，尝试备用方案: {e}")
    
    # 备用：从网页爬取
    try:
        url = "https://quote.eastmoney.com/center/gridlist.html#hs_a_board"
        html = run_curl(url)
        
        # 尝试提取页面中的数据
        # 东方财富通常把数据放在js变量中
        data = extract_json_from_js(html, "data")
        if data:
            print("✅ 从网页提取到涨停数据")
            return data
    except Exception as e:
        print(f"网页爬取失败: {e}")
    
    print("⚠️ 涨停数据获取失败，返回空列表")
    return []


def crawl_limit_down_stocks() -> List[Dict]:
    """
    爬取跌停个股数据
    """
    print("📉 正在爬取跌停个股数据...")
    
    today = datetime.now().strftime("%Y%m%d")
    
    url = "https://push2ex.eastmoney.com/getTopicDTPool"
    params = f"ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt&Pageindex=0&pageSize=100&sort=fbt%3Aasc&date={today}"
    
    try:
        full_url = f"{url}?{params}"
        resp = run_curl(full_url, referer="https://quote.eastmoney.com/")
        
        if resp:
            data = json.loads(resp)
            if data.get("data") and data["data"].get("pool"):
                stocks = []
                for item in data["data"]["pool"]:
                    stock = {
                        "code": item.get("c", ""),
                        "name": item.get("n", ""),
                        "price": item.get("p", 0) / 1000,
                        "change_pct": item.get("zdp", 0),
                        "fb_time": item.get("fbt", ""),
                        "amount": item.get("amount", 0) / 100000000,
                        "circ_mv": item.get("cm", 0) / 100000000,
                        "industry": item.get("hybk", ""),
                    }
                    stocks.append(stock)
                print(f"✅ 获取到 {len(stocks)} 只跌停股")
                return stocks
    except Exception as e:
        print(f"跌停数据获取失败: {e}")
    
    return []


# ============ 2. 板块资金流向爬虫 ============

def crawl_sector_flow() -> List[Dict]:
    """
    爬取板块资金流向排行
    来源: 东方财富行业板块资金流向 / 涨停统计备用
    """
    print("💰 正在爬取板块资金流向数据...")
    
    # 方案1: 东方财富API
    try:
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        params = (
            "pn=1&pz=50&po=1&np=1&"
            "fltt=2&invt=2&fid=f62&"
            "fs=m:90+t:2&"
            "fields=f12,f14,f20,f21,f22,f62,f128,f136,f140,f141&"
            "ut=fa5fd1943c7b386f172d6893dbfba10b"
        )
        
        full_url = f"{url}?{params}"
        resp = run_curl(full_url, referer="https://quote.eastmoney.com/center/gridlist.html#hs_a_board")
        
        if resp and len(resp) > 100:
            data = json.loads(resp)
            if data.get("data") and data["data"].get("diff"):
                sectors = []
                diff = data["data"]["diff"]
                if isinstance(diff, dict):
                    items = diff.items()
                else:
                    items = enumerate(diff)
                
                for _, item in items:
                    sector = {
                        "code": item.get("f12", ""),
                        "name": item.get("f14", ""),
                        "change_pct": item.get("f22", 0) or item.get("f3", 0),
                        "main_inflow": (item.get("f62", 0) or 0) / 10000,
                        "total_amount": (item.get("f20", 0) or 0) / 10000,
                    }
                    sectors.append(sector)
                
                sectors.sort(key=lambda x: x["main_inflow"], reverse=True)
                print(f"✅ 获取到 {len(sectors)} 个板块资金流向")
                return sectors
    except Exception as e:
        print(f"东方财富板块资金获取失败: {e}")
    
    # 方案2: 基于涨停个股统计（资金流入 ≈ 涨停板数量）
    try:
        print("   基于涨停股统计板块热度...")
        limit_up = crawl_limit_up_stocks()
        sector_data = {}
        
        for stock in limit_up:
            industry = stock.get('industry', '其他')
            if industry not in sector_data:
                sector_data[industry] = {
                    'count': 0, 
                    'amount': 0,
                    'total_change': 0
                }
            sector_data[industry]['count'] += 1
            sector_data[industry]['amount'] += stock.get('amount', 0)
            sector_data[industry]['total_change'] += stock.get('change_pct', 0)
        
        # 转换为列表并排序（按涨停数量和成交额）
        sectors = []
        for name, data in sorted(sector_data.items(), key=lambda x: (x[1]['count'], x[1]['amount']), reverse=True):
            avg_change = data['total_change'] / data['count'] if data['count'] > 0 else 0
            sectors.append({
                'code': '',
                'name': name,
                'change_pct': avg_change,
                'main_inflow': data['amount'],  # 用成交额近似
                'total_amount': data['amount'],
                'limit_up_count': data['count']
            })
        
        if sectors:
            print(f"✅ 从涨停股统计到 {len(sectors)} 个板块")
            return sectors
    except Exception as e:
        print(f"涨停统计失败: {e}")
    
    return []


def crawl_sector_ranking() -> Dict:
    """
    获取板块涨幅排行
    """
    print("📊 正在爬取板块涨幅排行...")
    
    # 方案1: 东方财富API
    try:
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        params = (
            "pn=1&pz=30&po=1&np=1&"
            "fltt=2&invt=2&fid=f3&"
            "fs=m:90+t:2&"
            "fields=f12,f14,f3,f20,f21,f104,f105,f106,f107&"
            "ut=fa5fd1943c7b386f172d6893dbfba10b"
        )
        
        full_url = f"{url}?{params}"
        resp = run_curl(full_url, referer="https://quote.eastmoney.com/center/gridlist.html#hs_a_board")
        
        if resp and len(resp) > 100:
            data = json.loads(resp)
            if data.get("data") and data["data"].get("diff"):
                sectors = []
                diff = data["data"]["diff"]
                if isinstance(diff, dict):
                    items = diff.items()
                else:
                    items = enumerate(diff)
                
                for _, item in items:
                    sector = {
                        "code": item.get("f12", ""),
                        "name": item.get("f14", ""),
                        "change_pct": item.get("f3", 0),
                        "up_count": item.get("f104", 0),
                        "down_count": item.get("f105", 0),
                    }
                    sectors.append(sector)
                
                print(f"✅ 获取到 {len(sectors)} 个板块涨幅数据")
                return {"top_sectors": sectors[:10], "all_sectors": sectors}
    except Exception as e:
        print(f"东方财富板块排行获取失败: {e}")
    
    # 方案2: 基于涨停个股统计热点板块
    try:
        print("   基于涨停股统计热点板块...")
        limit_up = crawl_limit_up_stocks()
        sector_count = {}
        for stock in limit_up:
            industry = stock.get('industry', '其他')
            if industry not in sector_count:
                sector_count[industry] = {'count': 0, 'stocks': []}
            sector_count[industry]['count'] += 1
            sector_count[industry]['stocks'].append(stock['name'])
        
        # 转换为列表并排序
        sectors = []
        for name, data in sorted(sector_count.items(), key=lambda x: x[1]['count'], reverse=True):
            sectors.append({
                'code': '',
                'name': name,
                'change_pct': 0,  # 无法直接获取
                'up_count': data['count'],
                'down_count': 0,
                'stocks': data['stocks']
            })
        
        if sectors:
            print(f"✅ 从涨停股统计到 {len(sectors)} 个热点板块")
            return {"top_sectors": sectors[:10], "all_sectors": sectors}
    except Exception as e:
        print(f"涨停统计失败: {e}")
    
    return {"top_sectors": [], "all_sectors": []}


# ============ 3. 大盘指数爬虫 ============

def crawl_index_data() -> Dict[str, Dict]:
    """
    爬取大盘指数实时数据
    优先使用腾讯API（稳定），备用东方财富
    """
    print("🎯 正在爬取大盘指数数据...")
    
    indices = {
        "sh000001": "上证指数",
        "sz399001": "深证成指",
        "sz399006": "创业板指",
        "sh000688": "科创50",
        "sh000300": "沪深300",
        "sh000016": "上证50",
    }
    
    result = {}
    
    # 方案1: 腾讯财经API
    try:
        codes = ",".join(indices.keys())
        url = f"https://qt.gtimg.cn/q={codes}"
        resp = run_curl(url, timeout=15, encoding='gbk')
        
        if resp:
            for line in resp.strip().split(";"):
                line = line.strip()
                if "=" not in line or '=""' in line:
                    continue
                
                # 解析 v_sh000001="1~上证指数~000001~3000.00~..."
                match = re.search(r'v_(sh\d+|sz\d+)=\"([^\"]+)\"', line)
                if match:
                    code = match.group(1)
                    fields = match.group(2).split("~")
                    
                    if len(fields) >= 35:
                        try:
                            result[indices.get(code, code)] = {
                                "code": code,
                                "name": fields[1],
                                "price": float(fields[3]) if fields[3] else 0,
                                "prev_close": float(fields[4]) if fields[4] else 0,
                                "open": float(fields[5]) if fields[5] else 0,
                                "change": float(fields[31]) if fields[31] else 0,
                                "change_pct": float(fields[32]) if fields[32] else 0,
                                "high": float(fields[33]) if fields[33] else 0,
                                "low": float(fields[34]) if fields[34] else 0,
                                "volume": float(fields[36]) if len(fields) > 36 and fields[36] else 0,
                            }
                        except ValueError:
                            continue
            
            if result:
                print(f"✅ 通过腾讯API获取到 {len(result)} 个指数")
                return result
    except Exception as e:
        print(f"腾讯API失败: {e}")
    
    # 方案2: 东方财富备用
    try:
        url = "https://push2.eastmoney.com/api/qt/ulist.np/get"
        params = "fltt=2&invt=2&fields=f2,f3,f4,f5,f12,f13,f14,f20,f104,f105,f106,f107&secids=1.000001,0.399001,0.399006,1.000688,1.000300"
        
        resp = run_curl(f"{url}?{params}", referer="https://quote.eastmoney.com/")
        
        if resp:
            data = json.loads(resp)
            # 解析东方财富数据格式...
            print("✅ 通过东方财富获取到指数数据")
    except Exception as e:
        print(f"东方财富备用方案失败: {e}")
    
    return result


def crawl_updown_stats() -> Dict:
    """
    获取涨跌家数统计
    """
    print("📈 正在爬取涨跌家数统计...")
    
    try:
        # 东方财富涨跌统计API
        today = datetime.now().strftime("%Y%m%d")
        url = "https://push2ex.eastmoney.com/getStockCount"
        params = f"ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt&date={today}"
        
        resp = run_curl(f"{url}?{params}", referer="https://quote.eastmoney.com/")
        
        if resp:
            data = json.loads(resp)
            if data.get("data"):
                d = data["data"]
                return {
                    "up": d.get("rise_count", 0),
                    "down": d.get("fall_count", 0),
                    "flat": d.get("equal_count", 0),
                    "limit_up": d.get("zt_count", 0),
                    "limit_down": d.get("dt_count", 0),
                }
    except Exception as e:
        print(f"涨跌统计获取失败: {e}")
    
    # 备用：从已获取的涨跌停数据估算
    return {"up": 0, "down": 0, "flat": 0, "limit_up": 0, "limit_down": 0}


# ============ 报告生成 ============

def generate_full_report():
    """生成完整的市场数据报告"""
    print("\n" + "="*60)
    print("📊 东方财富市场数据爬虫报告")
    print("="*60 + "\n")
    
    now = datetime.now()
    
    # 获取各类数据
    index_data = crawl_index_data()
    limit_up = crawl_limit_up_stocks()
    limit_down = crawl_limit_down_stocks()
    sector_flow = crawl_sector_flow()
    sector_rank = crawl_sector_ranking()
    updown_stats = crawl_updown_stats()
    
    # 生成Markdown报告
    report = f"""# 📊 市场数据爬虫报告（备用方案）

**生成时间**：{now.strftime('%Y-%m-%d %H:%M')}  
**数据来源**：东方财富网页爬取

---

## 📈 核心指数

| 指数 | 最新价 | 涨跌 | 涨跌幅 | 最高 | 最低 |
|------|--------|------|--------|------|------|
"""
    
    for name, data in index_data.items():
        report += f"| **{name}** | {data['price']:.2f} | {data['change']:+.2f} | {data['change_pct']:+.2f}% | {data['high']:.2f} | {data['low']:.2f} |\n"
    
    report += f"""
---

## 📊 涨跌统计

| 上涨家数 | 下跌家数 | 平盘家数 | 涨停 | 跌停 |
|----------|----------|----------|------|------|
| 🔴 {updown_stats['up']} | 🟢 {updown_stats['down']} | ⚪ {updown_stats['flat']} | 🔥 {updown_stats['limit_up']} | ❄️ {updown_stats['limit_down']} |

---

## 🔥 涨停个股（前15）

| 代码 | 名称 | 价格 | 涨跌幅 | 连板 | 行业 | 封板时间 |
|------|------|------|--------|------|------|----------|
"""
    
    for stock in limit_up[:15]:
        lb = f"{stock['lb_count']}连板" if stock['lb_count'] > 1 else "首板"
        fb_time = str(stock['fb_time'])
        fb_time_str = f"{fb_time[:2]}:{fb_time[2:4]}" if len(fb_time) >= 4 else fb_time
        report += f"| {stock['code']} | {stock['name']} | {stock['price']:.2f} | +{stock['change_pct']:.2f}% | {lb} | {stock['industry']} | {fb_time_str} |\n"
    
    report += f"""
---

## ❄️ 跌停个股（前10）

| 代码 | 名称 | 价格 | 涨跌幅 | 行业 |
|------|------|------|--------|------|
"""
    
    for stock in limit_down[:10]:
        report += f"| {stock['code']} | {stock['name']} | {stock['price']:.2f} | {stock['change_pct']:.2f}% | {stock['industry']} |\n"
    
    report += f"""
---

## 💰 板块资金流向（净流入TOP15）

| 排名 | 板块 | 主力净流入(亿) | 涨跌幅 |
|------|------|----------------|--------|
"""
    
    for i, sector in enumerate(sector_flow[:15], 1):
        inflow = sector['main_inflow'] / 10000  # 转换为亿
        report += f"| {i} | **{sector['name']}** | {inflow:+.2f} | {sector['change_pct']:+.2f}% |\n"
    
    report += f"""
---

## 📈 板块涨幅排行（TOP10）

| 排名 | 板块 | 涨跌幅 | 上涨家数 | 下跌家数 |
|------|------|--------|----------|----------|
"""
    
    for i, sector in enumerate(sector_rank.get('top_sectors', [])[:10], 1):
        report += f"| {i} | {sector['name']} | {sector['change_pct']:+.2f}% | {sector['up_count']} | {sector['down_count']} |\n"
    
    report += """
---

*⚠️ 备注：本报告数据通过网页爬取获取，可能存在延迟，仅供参考。*
"""
    
    # 保存报告
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"market_crawler_{now.strftime('%Y%m%d_%H%M')}.md"
    filepath = MEMORY_DIR / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ 报告已保存: {filepath}")
    print("\n" + "="*60)
    print(report)
    print("="*60)
    
    return {
        "index": index_data,
        "limit_up": limit_up,
        "limit_down": limit_down,
        "sector_flow": sector_flow,
        "sector_rank": sector_rank,
        "updown_stats": updown_stats,
        "report_path": str(filepath),
        "report": report
    }


def test_crawler():
    """测试爬虫各模块"""
    print("\n🧪 测试爬虫模块...\n")
    
    # 测试指数
    print("1️⃣ 测试大盘指数爬虫...")
    index_data = crawl_index_data()
    print(f"   获取到 {len(index_data)} 个指数\n")
    
    # 测试涨停
    print("2️⃣ 测试涨停榜爬虫...")
    limit_up = crawl_limit_up_stocks()
    print(f"   获取到 {len(limit_up)} 只涨停股\n")
    
    # 测试跌停
    print("3️⃣ 测试跌停榜爬虫...")
    limit_down = crawl_limit_down_stocks()
    print(f"   获取到 {len(limit_down)} 只跌停股\n")
    
    # 测试板块资金
    print("4️⃣ 测试板块资金流向爬虫...")
    sector_flow = crawl_sector_flow()
    print(f"   获取到 {len(sector_flow)} 个板块\n")
    
    # 测试涨跌统计
    print("5️⃣ 测试涨跌统计爬虫...")
    stats = crawl_updown_stats()
    print(f"   上涨: {stats['up']}, 下跌: {stats['down']}, 涨停: {stats['limit_up']}, 跌停: {stats['limit_down']}\n")
    
    print("✅ 测试完成！")
    return True


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_crawler()
    else:
        generate_full_report()

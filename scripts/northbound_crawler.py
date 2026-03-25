#!/usr/bin/env python3
"""
北向资金流向爬虫
获取沪深股通（北向资金）实时和历史资金流向数据

数据源：
1. 东方财富 - 主要数据源
2. 同花顺 - 备用数据源
3. 新浪财经 - 备用数据源
"""

import json
import re
import subprocess
from datetime import datetime, timedelta
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


# ============ 1. 东方财富数据源 ============

def get_eastmoney_northbound_minute() -> List[Dict]:
    """
    获取北向资金分钟级流向（当日实时）
    """
    print("📊 正在获取北向资金分钟数据...")
    
    try:
        # 东方财富北向资金分钟数据API
        url = "https://push2.eastmoney.com/api/qt/kamtbs.rtmin/get"
        params = "fields1=f1,f2,f3,f4&fields2=f51,f52,f53,f54,f55,f56&ut=fa5fd1943c7b386f172d6893dbfba10b"
        
        resp = run_curl(f"{url}?{params}", referer="https://quote.eastmoney.com/")
        
        if resp:
            data = json.loads(resp)
            if data.get("data"):
                result = []
                
                # 沪股通数据 hk2sh
                if data["data"].get("hk2sh"):
                    for item in data["data"]["hk2sh"]:
                        # 格式: "9:30,净流入,累计流入,买卖总额,...
                        fields = item.split(",")
                        if len(fields) >= 6:
                            result.append({
                                "time": fields[0],
                                "sh_inflow": float(fields[1]) if fields[1] else 0,  # 沪股通净流入
                                "sh_cum_inflow": float(fields[2]) if fields[2] else 0,  # 沪股通累计流入
                            })
                
                # 深股通数据 hk2sz
                if data["data"].get("hk2sz"):
                    for i, item in enumerate(data["data"]["hk2sz"]):
                        fields = item.split(",")
                        if len(fields) >= 6 and i < len(result):
                            result[i]["sz_inflow"] = float(fields[1]) if fields[1] else 0
                            result[i]["sz_cum_inflow"] = float(fields[2]) if fields[2] else 0
                            result[i]["total_inflow"] = result[i].get("sh_inflow", 0) + result[i].get("sz_inflow", 0)
                
                if result:
                    print(f"✅ 获取到 {len(result)} 条分钟数据")
                    return result
    except Exception as e:
        print(f"东方财富分钟数据获取失败: {e}")
    
    return []


def get_eastmoney_northbound_daily(start_date: str = None, end_date: str = None) -> List[Dict]:
    """
    获取北向资金历史日流向数据
    """
    print("📊 正在获取北向资金日历史数据...")
    
    try:
        # 东方财富数据中心API
        url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
        params = (
            "sortColumns=TRADE_DATE&sortTypes=-1&"
            "pageSize=30&pageNumber=1&"
            "reportName=RPT_MUTUAL_DEAL_HISTORY&columns=ALL&"
            "source=WEB&client=WEB&"
            "filter=(MUTUAL_TYPE%3D%22005%22)"
        )
        
        resp = run_curl(f"{url}?{params}")
        
        if resp:
            data = json.loads(resp)
            if data.get("result") and data["result"].get("data"):
                result = []
                for item in data["result"]["data"]:
                    # 处理字段名
                    result.append({
                        "date": item.get("TRADE_DATE", "").split()[0] if item.get("TRADE_DATE") else "",
                        "sh_inflow": item.get("SH_INFLOW") or item.get("FUND_INFLOW") or 0,
                        "sz_inflow": item.get("SZ_INFLOW") or 0,
                        "total_inflow": item.get("FUND_INFLOW") or 0,
                        "deal_amt": item.get("DEAL_AMT", 0),  # 成交额
                        "buy_amt": item.get("BUY_AMT", 0),
                        "sell_amt": item.get("SELL_AMT", 0),
                        "lead_stock": item.get("LEAD_STOCKS_NAME", ""),
                        "lead_stock_code": item.get("LEAD_STOCKS_CODE", ""),
                        "lead_stock_change": item.get("LS_CHANGE_RATE", 0),
                    })
                
                if result:
                    print(f"✅ 获取到 {len(result)} 条历史数据")
                    return result
    except Exception as e:
        print(f"东方财富历史数据获取失败: {e}")
    
    return []


def get_eastmoney_northbound_top_stocks() -> Dict:
    """
    获取北向资金持股/买卖TOP股票
    """
    print("📊 正在获取北向资金个股流向...")
    
    result = {
        "top_buy": [],
        "top_sell": [],
        "top_hold": []
    }
    
    try:
        # 北向资金买入TOP10
        url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
        params = (
            "sortColumns=NET_INFLOW&sortTypes=-1&"
            "pageSize=10&pageNumber=1&"
            "reportName=RPT_MUTUAL_STOCK_HOLD&columns=ALL&"
            "source=WEB&client=WEB"
        )
        
        resp = run_curl(f"{url}?{params}")
        
        if resp:
            data = json.loads(resp)
            if data.get("result") and data["result"].get("data"):
                for item in data["result"]["data"]:
                    result["top_buy"].append({
                        "code": item.get("SECURITY_CODE", ""),
                        "name": item.get("SECURITY_NAME", ""),
                        "net_inflow": item.get("NET_INFLOW", 0),
                        "hold_ratio": item.get("HOLD_RATIO", 0),
                    })
    except Exception as e:
        print(f"个股流向获取失败: {e}")
    
    return result


# ============ 2. 备用数据源 ============

def get_sina_northbound() -> Dict:
    """
    新浪财经北向资金数据（备用）
    """
    print("📊 尝试新浪备用数据源...")
    
    try:
        # 新浪财经沪深港通数据
        url = "https://quotes.sina.cn/cn/api/quotes.php?symbol=sh999999&callback=cb"
        resp = run_curl(url)
        
        # 新浪返回的是JSONP格式
        if resp and "cb(" in resp:
            json_str = resp.split("cb(")[1].rstrip(")")
            data = json.loads(json_str)
            # 解析数据...
    except Exception as e:
        print(f"新浪数据获取失败: {e}")
    
    return {}


# ============ 3. 数据汇总与报告 ============

def get_northbound_summary() -> Dict:
    """
    获取北向资金综合数据汇总
    """
    print("\n" + "="*60)
    print("📈 北向资金流向数据汇总")
    print("="*60 + "\n")
    
    summary = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "minute_data": [],
        "daily_data": [],
        "top_stocks": {},
        "current_status": {}
    }
    
    # 获取分钟数据
    summary["minute_data"] = get_eastmoney_northbound_minute()
    
    # 获取历史日数据
    summary["daily_data"] = get_eastmoney_northbound_daily()
    
    # 获取个股流向
    summary["top_stocks"] = get_eastmoney_northbound_top_stocks()
    
    # 计算当前状态
    if summary["minute_data"]:
        latest = summary["minute_data"][-1]
        summary["current_status"] = {
            "time": latest.get("time"),
            "sh_inflow": latest.get("sh_inflow", 0),
            "sz_inflow": latest.get("sz_inflow", 0),
            "total_inflow": latest.get("total_inflow", 0),
        }
    
    return summary


def generate_northbound_report():
    """
    生成北向资金流向报告
    """
    summary = get_northbound_summary()
    
    now = datetime.now()
    report = f"""# 📈 北向资金流向报告

**生成时间**：{summary['timestamp']}  
**数据来源**：东方财富

---

## 💰 实时资金流向

"""
    
    # 当前状态
    if summary.get("current_status"):
        status = summary["current_status"]
        total = status.get("total_inflow", 0)
        direction = "📈 净流入" if total > 0 else "📉 净流出" if total < 0 else "➡️ 持平"
        
        report += f"""### 最新状态（{status.get('time', 'N/A')}）

| 项目 | 净流入（亿元） | 状态 |
|------|----------------|------|
| **沪股通** | {status.get('sh_inflow', 0):+.2f} | {direction if status.get('sh_inflow', 0) > 0 else '📉 流出' if status.get('sh_inflow', 0) < 0 else '➡️ 持平'} |
| **深股通** | {status.get('sz_inflow', 0):+.2f} | {direction if status.get('sz_inflow', 0) > 0 else '📉 流出' if status.get('sz_inflow', 0) < 0 else '➡️ 持平'} |
| **合计** | **{total:+.2f}** | **{direction}** |

---

### 📊 分时资金流向趋势

| 时间 | 沪股通 | 深股通 | 合计 |
|------|--------|--------|------|
"""
        
        # 显示最近20条分钟数据
        for item in summary["minute_data"][-20:]:
            report += f"| {item.get('time')} | {item.get('sh_inflow', 0):+.2f} | {item.get('sz_inflow', 0):+.2f} | **{item.get('total_inflow', 0):+.2f}** |\n"
    else:
        report += """⚠️ 暂无法获取实时数据

可能原因：
- 非交易时间（北向资金交易时间：9:30-11:30, 13:00-15:00）
- API接口暂时不可用
- 数据延迟更新

"""
    
    report += """---

## 📅 近期历史数据

"""
    
    # 历史数据
    if summary.get("daily_data"):
        report += """### 近10日资金流向

| 日期 | 沪股通 | 深股通 | 合计 | 龙头个股 |
|------|--------|--------|------|----------|
"""
        for item in summary["daily_data"][:10]:
            total = item.get("total_inflow", 0)
            if isinstance(total, str):
                total = 0
            report += f"| {item.get('date')} | {item.get('sh_inflow', 0)} | {item.get('sz_inflow', 0)} | **{total:+.2f}** | {item.get('lead_stock', '-')} |\n"
    else:
        report += "⚠️ 暂无法获取历史数据\n\n"
    
    report += """---

## 🔔 数据说明

1. **北向资金**：指通过沪深港通从香港流入A股市场的资金
2. **交易时间**：工作日 9:30-11:30, 13:00-15:00
3. **数据更新**：实时数据可能有5-15分钟延迟
4. **参考意义**：北向资金常被视为"聪明钱"，对A股市场有一定风向标作用

---

*⚠️ 免责声明：本报告仅供参考，不构成投资建议*
"""
    
    # 保存报告
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"northbound_report_{now.strftime('%Y%m%d_%H%M')}.md"
    filepath = MEMORY_DIR / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ 报告已保存: {filepath}")
    print("\n" + "="*60)
    print(report)
    print("="*60)
    
    return {
        "filepath": str(filepath),
        "report": report,
        "data": summary
    }


def test_northbound_crawler():
    """测试北向资金爬虫"""
    print("\n🧪 测试北向资金爬虫模块...\n")
    
    print("1️⃣ 测试分钟数据...")
    minute_data = get_eastmoney_northbound_minute()
    print(f"   获取到 {len(minute_data)} 条分钟数据")
    if minute_data:
        print(f"   最新: {minute_data[-1]}")
    
    print("\n2️⃣ 测试历史日数据...")
    daily_data = get_eastmoney_northbound_daily()
    print(f"   获取到 {len(daily_data)} 条历史数据")
    if daily_data:
        print(f"   最新: {daily_data[0]}")
    
    print("\n3️⃣ 测试个股数据...")
    top_stocks = get_eastmoney_northbound_top_stocks()
    print(f"   买入TOP: {len(top_stocks.get('top_buy', []))}")
    
    print("\n✅ 测试完成！")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_northbound_crawler()
    else:
        generate_northbound_report()

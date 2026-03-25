#!/usr/bin/env python3
"""
北向资金流向爬虫 - 网页版
通过解析东方财富网页JS变量获取数据
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
        
        for enc in [encoding, 'gbk', 'gb2312', 'utf-8']:
            try:
                return result.stdout.decode(enc)
            except:
                continue
        return result.stdout.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"请求失败: {e}")
        return ""


def extract_js_variable(html: str, var_name: str) -> Optional[Dict]:
    """从HTML中提取JavaScript变量"""
    # 匹配 var name = {...}; 或 var name = [...];
    pattern = rf'var\s+{var_name}\s*=\s*(\{{.*?\}}|\[.*?\]);'
    match = re.search(pattern, html, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None
    return None


def get_northbound_from_page() -> Dict:
    """
    从东方财富页面获取北向资金数据
    """
    print("🌐 正在从网页获取北向资金数据...")
    
    result = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "sh_inflow": 0,
        "sz_inflow": 0,
        "total_inflow": 0,
        "sh_buy": 0,
        "sh_sell": 0,
        "sz_buy": 0,
        "sz_sell": 0,
    }
    
    # 尝试多个页面
    urls = [
        "https://quote.eastmoney.com/center/gridlist.html#hs_a_board",
        "https://quote.eastmoney.com/center/",
    ]
    
    for url in urls:
        try:
            print(f"   尝试: {url}")
            html = run_curl(url, referer="https://quote.eastmoney.com/")
            
            if not html:
                continue
            
            # 查找北向资金相关数据
            # 东方财富通常会在页面中嵌入数据
            
            # 尝试查找资金流数据
            # 格式通常是: var northMoney = {...} 或其他变量名
            patterns = [
                r'"沪股通([^"]*)":\s*"?([^",}]+)"?',
                r'"深股通([^"]*)":\s*"?([^",}]+)"?',
                r'"北向([^"]*)":\s*"?([^",}]+)"?',
                r'([\d\.]+)亿',
            ]
            
            # 尝试查找包含"亿"的数字，可能是资金数据
            money_pattern = r'([+-]?[\d\.]+)\s*亿'
            matches = re.findall(money_pattern, html)
            if matches:
                print(f"   找到可能的资金数据: {matches[:5]}")
            
            # 查找json数据
            json_pattern = r'"data":(\{[^}]+\})'
            json_matches = re.findall(json_pattern, html)
            if json_matches:
                for m in json_matches[:3]:
                    try:
                        data = json.loads(m)
                        print(f"   找到数据: {data}")
                    except:
                        pass
                        
        except Exception as e:
            print(f"   页面获取失败: {e}")
    
    return result


def get_northbound_from_api() -> Dict:
    """
    通过API获取北向资金数据
    """
    print("📡 正在通过API获取北向资金数据...")
    
    result = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "minute_data": [],
        "daily_data": [],
    }
    
    # 1. 获取实时分钟数据
    try:
        url = "https://push2.eastmoney.com/api/qt/kamtbs.rtmin/get"
        params = "fields1=f1,f2,f3,f4&fields2=f51,f52,f53,f54,f55,f56&ut=fa5fd1943c7b386f172d6893dbfba10b"
        
        resp = run_curl(f"{url}?{params}", referer="https://quote.eastmoney.com/")
        
        if resp:
            data = json.loads(resp)
            if data.get("data"):
                # 沪股通 hk2sh
                if data["data"].get("hk2sh"):
                    for item in data["data"]["hk2sh"]:
                        fields = item.split(",")
                        if len(fields) >= 3:
                            result["minute_data"].append({
                                "time": fields[0],
                                "sh_inflow": float(fields[1]) if fields[1] else 0,
                                "sh_cum": float(fields[2]) if fields[2] else 0,
                            })
                
                # 深股通 hk2sz
                if data["data"].get("hk2sz"):
                    for i, item in enumerate(data["data"]["hk2sz"]):
                        fields = item.split(",")
                        if len(fields) >= 3 and i < len(result["minute_data"]):
                            result["minute_data"][i]["sz_inflow"] = float(fields[1]) if fields[1] else 0
                            result["minute_data"][i]["sz_cum"] = float(fields[2]) if fields[2] else 0
                            result["minute_data"][i]["total"] = (
                                result["minute_data"][i].get("sh_inflow", 0) + 
                                result["minute_data"][i].get("sz_inflow", 0)
                            )
    except Exception as e:
        print(f"   分钟数据获取失败: {e}")
    
    # 2. 获取历史日数据
    try:
        url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
        params = (
            "sortColumns=TRADE_DATE&sortTypes=-1&"
            "pageSize=20&pageNumber=1&"
            "reportName=RPT_MUTUAL_DEAL_HISTORY&columns=ALL&"
            "source=WEB&client=WEB&"
            "filter=(MUTUAL_TYPE%3D%22005%22)"
        )
        
        resp = run_curl(f"{url}?{params}")
        
        if resp:
            data = json.loads(resp)
            if data.get("result") and data["result"].get("data"):
                for item in data["result"]["data"]:
                    result["daily_data"].append({
                        "date": item.get("TRADE_DATE", "").split()[0] if item.get("TRADE_DATE") else "",
                        "deal_amt": item.get("DEAL_AMT", 0),  # 成交额
                        "deal_num": item.get("DEAL_NUM", 0),  # 成交笔数
                        "lead_stock": item.get("LEAD_STOCKS_NAME", ""),
                        "lead_stock_code": item.get("LEAD_STOCKS_CODE", ""),
                        "lead_stock_change": item.get("LS_CHANGE_RATE", 0),
                        "index_close": item.get("INDEX_CLOSE_PRICE", 0),
                        "index_change": item.get("INDEX_CHANGE_RATE", 0),
                    })
    except Exception as e:
        print(f"   历史数据获取失败: {e}")
    
    # 计算当前状态
    if result["minute_data"]:
        latest = result["minute_data"][-1]
        result["current"] = {
            "time": latest.get("time"),
            "sh_inflow": latest.get("sh_inflow", 0),
            "sz_inflow": latest.get("sz_inflow", 0),
            "total_inflow": latest.get("total", 0),
        }
    
    return result


def generate_report():
    """生成北向资金报告"""
    print("\n" + "="*60)
    print("📈 北向资金流向报告")
    print("="*60 + "\n")
    
    # 获取数据
    data = get_northbound_from_api()
    
    now = datetime.now()
    report = f"""# 📈 北向资金流向报告

**生成时间**：{data.get('timestamp', now.strftime('%Y-%m-%d %H:%M'))}  
**数据来源**：东方财富网页/API

---

"""
    
    # 实时数据
    if data.get("current"):
        curr = data["current"]
        total = curr.get("total_inflow", 0)
        direction = "📈 净流入" if total > 0 else "📉 净流出" if total < 0 else "➡️ 持平"
        
        report += f"""## 💰 实时资金流向（{curr.get('time', 'N/A')}）

| 渠道 | 净流入（亿元） | 方向 |
|------|----------------|------|
| **沪股通** | {curr.get('sh_inflow', 0):.2f} | {'📈' if curr.get('sh_inflow', 0) > 0 else '📉' if curr.get('sh_inflow', 0) < 0 else '➡️'} |
| **深股通** | {curr.get('sz_inflow', 0):.2f} | {'📈' if curr.get('sz_inflow', 0) > 0 else '📉' if curr.get('sz_inflow', 0) < 0 else '➡️'} |
| **合计** | **{total:.2f}** | **{direction}** |

---

### 📊 分时数据（最近15分钟）

| 时间 | 沪股通 | 深股通 | 合计 |
|------|--------|--------|------|
"""
        # 显示最近15条
        for item in data.get("minute_data", [])[-15:]:
            total = item.get("total", 0)
            report += f"| {item.get('time')} | {item.get('sh_inflow', 0):+.2f} | {item.get('sz_inflow', 0):+.2f} | **{total:+.2f}** |\n"
    
    else:
        report += """## 💰 实时资金流向

⚠️ **暂无法获取实时数据**

可能原因：
- 非交易时间（北向资金交易时间：工作日 9:30-11:30, 13:00-15:00）
- API接口限制或数据延迟
- 节假日休市

"""
    
    # 历史数据
    if data.get("daily_data"):
        report += """
---

## 📅 近期历史数据

### 近10日资金流向

| 日期 | 成交额(亿) | 成交笔数 | 领涨个股 | 个股涨幅 | 上证指数 |
|------|-----------|----------|----------|----------|----------|
"""
        for item in data["daily_data"][:10]:
            report += f"| {item.get('date')} | {item.get('deal_amt', 0):,.0f} | {item.get('deal_num', 0):,} | {item.get('lead_stock', '-')} | {item.get('lead_stock_change', 0)}% | {item.get('index_change', 0)}% |\n"
    
    report += """
---

## 🔔 数据说明

1. **北向资金**：通过沪深港通从香港流入A股市场的资金
2. **交易时间**：工作日 9:30-11:30, 13:00-15:00
3. **数据更新**：实时数据可能有延迟
4. **参考意义**：北向资金常被视作市场风向标

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
        "data": data
    }


if __name__ == "__main__":
    generate_report()

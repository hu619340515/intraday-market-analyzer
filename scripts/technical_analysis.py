#!/usr/bin/env python3
"""
技术分析模块 - 提供技术指标计算和分析
"""

import json
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def run_browser(cmd: str, timeout: int = 60) -> str:
    """执行agent-browser命令"""
    try:
        full_cmd = f"agent-browser {cmd}"
        result = subprocess.run(
            full_cmd,
            shell=True,
            capture_output=True,
            timeout=timeout
        )
        for enc in ['utf-8', 'gbk', 'gb2312']:
            try:
                return result.stdout.decode(enc)
            except:
                continue
        return result.stdout.decode('utf-8', errors='ignore')
    except:
        return ""


def browser_open(url: str, wait_ms: int = 3000) -> bool:
    """使用agent-browser打开页面"""
    result = run_browser(f'open "{url}" --timeout {wait_ms}')
    return "error" not in result.lower() or "timeout" in result.lower()


def browser_close():
    """关闭浏览器"""
    run_browser('close')


def extract_json_from_response(text: str) -> Optional[Dict]:
    """从响应文本中提取JSON数据"""
    try:
        return json.loads(text)
    except:
        pass
    
    import re
    json_pattern = r'StaticText\s*"(\{[\s\S]*?\})"'
    matches = re.findall(json_pattern, text)
    
    longest_json = ""
    for match in matches:
        if len(match) > len(longest_json):
            longest_json = match
    
    if longest_json:
        try:
            return json.loads(longest_json)
        except:
            pass
    
    brace_pattern = r'(\{[\s\S]{100,}?\})'
    matches = re.findall(brace_pattern, text)
    for match in sorted(matches, key=len, reverse=True):
        try:
            return json.loads(match)
        except:
            continue
    
    return None


class TechnicalAnalyzer:
    """技术分析器"""
    
    def __init__(self):
        self.index_history = {}  # 缓存历史数据
    
    def get_index_kline(self, code: str, days: int = 20) -> List[Dict]:
        """
        获取指数K线数据
        来源：东方财富
        注：此API不稳定，可能返回空数据
        """
        print(f"📊 获取{code}历史K线数据...")
        
        # 东方财富K线API - 经常不稳定
        secid = f"1.{code[2:]}" if code.startswith('sh') else f"0.{code[2:]}"
        
        url = (
            f"https://push2.eastmoney.com/api/qt/stock/kline/get?"
            f"secid={secid}&"
            f"fields1=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13&"
            f"fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&"
            f"klt=101&fqt=0&end=20500101&limit={days}&"
            f"ut=fa5fd1943c7b386f172d6893dbfba10b"
        )
        
        try:
            import subprocess
            # 快速测试API是否可用
            result = subprocess.run(
                f'agent-browser open "{url}" --timeout 3000',
                shell=True, capture_output=True, timeout=10
            )
            if result.returncode != 0:
                print(f"   K线API暂不可用，跳过技术分析")
                return []
            
            page_text = run_browser('snapshot')
            browser_close()
            
            data = extract_json_from_response(page_text)
            if not data or not data.get('data'):
                return []
            
            klines = data['data'].get('klines', [])
            result = []
            
            for kline in klines:
                parts = kline.split(',')
                if len(parts) >= 9:
                    result.append({
                        'date': parts[0],
                        'open': float(parts[1]),
                        'close': float(parts[2]),
                        'high': float(parts[3]),
                        'low': float(parts[4]),
                        'volume': float(parts[5]),
                        'amount': float(parts[6]),
                        'amplitude': float(parts[7]),
                        'change_pct': float(parts[8]),
                    })
            
            return result
            
        except Exception as e:
            print(f"   K线数据获取失败，使用简化分析")
            browser_close()
            return []
    
    def calculate_ma(self, prices: List[float], period: int) -> Optional[float]:
        """计算移动平均线"""
        if len(prices) < period:
            return None
        return sum(prices[-period:]) / period
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> Optional[float]:
        """计算RSI指标"""
        if len(prices) < period + 1:
            return None
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if len(gains) < period:
            return None
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, prices: List[float]) -> Dict[str, Optional[float]]:
        """计算MACD指标（简化版）"""
        if len(prices) < 26:
            return {'macd': None, 'signal': None, 'histogram': None}
        
        # 计算EMA12和EMA26（简化使用SMA）
        ema12 = self.calculate_ma(prices, 12)
        ema26 = self.calculate_ma(prices, 26)
        
        if ema12 is None or ema26 is None:
            return {'macd': None, 'signal': None, 'histogram': None}
        
        macd = ema12 - ema26
        
        # 计算信号线（MACD的9日EMA，简化使用最近9个MACD的均值）
        # 这里简化处理，只返回当前MACD值
        return {
            'macd': macd,
            'signal': None,  # 需要更多历史数据
            'histogram': None
        }
    
    def analyze_index(self, code: str, name: str, current_price: float) -> Dict:
        """分析单个指数的技术指标"""
        klines = self.get_index_kline(code, days=30)
        
        if not klines:
            return {
                'name': name,
                'ma5': None,
                'ma10': None,
                'ma20': None,
                'rsi': None,
                'macd': None,
                'support': None,
                'resistance': None,
                'trend': '未知',
            }
        
        closes = [k['close'] for k in klines]
        highs = [k['high'] for k in klines]
        lows = [k['low'] for k in klines]
        
        # 计算移动平均线
        ma5 = self.calculate_ma(closes, 5)
        ma10 = self.calculate_ma(closes, 10)
        ma20 = self.calculate_ma(closes, 20)
        
        # 计算RSI
        rsi = self.calculate_rsi(closes, 14)
        
        # 计算MACD
        macd_data = self.calculate_macd(closes)
        
        # 计算支撑和阻力位（最近5日高低点）
        recent_highs = highs[-5:]
        recent_lows = lows[-5:]
        resistance = max(recent_highs) if recent_highs else None
        support = min(recent_lows) if recent_lows else None
        
        # 判断趋势
        trend = self._determine_trend(current_price, ma5, ma10, ma20)
        
        return {
            'name': name,
            'current': current_price,
            'ma5': ma5,
            'ma10': ma10,
            'ma20': ma20,
            'rsi': rsi,
            'macd': macd_data['macd'],
            'support': support,
            'resistance': resistance,
            'trend': trend,
            'history': klines[-5:],  # 最近5日数据
        }
    
    def _determine_trend(self, current: float, ma5: Optional[float], 
                         ma10: Optional[float], ma20: Optional[float]) -> str:
        """判断趋势"""
        if ma5 is None or ma10 is None or ma20 is None:
            return '未知'
        
        # 多头排列：当前 > MA5 > MA10 > MA20
        if current > ma5 > ma10 > ma20:
            return '📈 强势上涨'
        
        # 空头排列：当前 < MA5 < MA10 < MA20
        if current < ma5 < ma10 < ma20:
            return '📉 弱势下跌'
        
        # 金叉信号
        if ma5 > ma10 and ma10 > ma20:
            return '📊 多头趋势'
        
        # 死叉信号
        if ma5 < ma10 and ma10 < ma20:
            return '📊 空头趋势'
        
        # 震荡
        return '↔️ 震荡整理'
    
    def analyze_volume(self, klines: List[Dict]) -> Dict:
        """分析成交量"""
        if not klines or len(klines) < 5:
            return {'avg_volume': 0, 'current_ratio': 0, 'status': '无数据'}
        
        volumes = [k['volume'] for k in klines]
        avg_volume = sum(volumes[:-1]) / len(volumes[:-1])  # 排除今日的均值
        current_volume = volumes[-1]
        
        ratio = current_volume / avg_volume if avg_volume > 0 else 0
        
        if ratio > 1.5:
            status = '🔥 放量'
        elif ratio > 1.2:
            status = '📈 温和放量'
        elif ratio < 0.7:
            status = '💤 缩量'
        else:
            status = '➡️ 常态'
        
        return {
            'avg_volume': avg_volume,
            'current_volume': current_volume,
            'current_ratio': ratio,
            'status': status
        }


class SentimentAnalyzer:
    """市场情绪分析器"""
    
    def calculate_market_sentiment(self, up_count: int, down_count: int, 
                                   limit_up: int, limit_down: int,
                                   total_stocks: int = 5100) -> Dict:
        """计算市场情绪指标"""
        
        # 涨跌比
        if down_count > 0:
            up_down_ratio = up_count / down_count
        else:
            up_down_ratio = float('inf') if up_count > 0 else 1
        
        # 涨停跌停比
        if limit_down > 0:
            limit_ratio = limit_up / limit_down
        else:
            limit_ratio = float('inf') if limit_up > 0 else 1
        
        # 上涨家数占比
        if total_stocks > 0:
            up_percentage = (up_count / total_stocks) * 100
        else:
            up_percentage = 0
        
        # 情绪判断
        if limit_up >= 50 and up_percentage > 60:
            sentiment = '🔥 极度贪婪'
            score = 85
        elif limit_up >= 30 and up_percentage > 50:
            sentiment = '📈 贪婪'
            score = 70
        elif limit_up >= 10 and up_down_ratio > 1.5:
            sentiment = '😊 乐观'
            score = 60
        elif limit_down >= 10 and up_down_ratio < 0.7:
            sentiment = '😰 恐慌'
            score = 30
        elif limit_down >= 30:
            sentiment = '❄️ 极度恐慌'
            score = 15
        else:
            sentiment = '😐 中性'
            score = 50
        
        return {
            'up_down_ratio': up_down_ratio,
            'limit_ratio': limit_ratio,
            'up_percentage': up_percentage,
            'sentiment': sentiment,
            'score': score,
        }
    
    def calculate_sector_sentiment(self, sectors: List[Dict]) -> Dict:
        """计算板块情绪"""
        if not sectors:
            return {'hot_sectors': [], 'cold_sectors': [], 'avg_change': 0}
        
        # 涨幅前5的板块
        hot_sectors = sorted(sectors, key=lambda x: x.get('change_pct', 0), reverse=True)[:5]
        
        # 跌幅前5的板块
        cold_sectors = sorted(sectors, key=lambda x: x.get('change_pct', 0))[:5]
        
        # 平均涨跌幅
        avg_change = sum(s.get('change_pct', 0) for s in sectors) / len(sectors)
        
        return {
            'hot_sectors': hot_sectors,
            'cold_sectors': cold_sectors,
            'avg_change': avg_change,
        }


class HistoryComparator:
    """历史对比分析器"""
    
    def __init__(self, memory_dir: Path = None):
        self.memory_dir = memory_dir or Path("~/.openclaw/workspace/memory").expanduser()
    
    def get_previous_report(self, days_ago: int = 1) -> Optional[Dict]:
        """获取历史报告数据"""
        target_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y%m%d')
        
        # 查找对应日期的报告
        for report_file in self.memory_dir.glob(f"market_analysis_{target_date}_*.md"):
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 简单解析提取数据
                return self._parse_report_content(content)
            except:
                continue
        
        return None
    
    def _parse_report_content(self, content: str) -> Dict:
        """解析报告内容提取关键数据"""
        import re
        
        data = {
            'index_data': {},
            'limit_up_count': 0,
            'limit_down_count': 0,
        }
        
        # 尝试提取涨停跌停数量
        limit_up_match = re.search(r'涨停家数\s*\|\s*(\d+)', content)
        if limit_up_match:
            data['limit_up_count'] = int(limit_up_match.group(1))
        
        limit_down_match = re.search(r'跌停家数\s*\|\s*(\d+)', content)
        if limit_down_match:
            data['limit_down_count'] = int(limit_down_match.group(1))
        
        return data
    
    def compare_with_history(self, current_data: Dict) -> Dict:
        """与历史数据对比"""
        yesterday = self.get_previous_report(1)
        last_week = self.get_previous_report(7)
        
        comparisons = {
            'yesterday': self._calculate_change(current_data, yesterday),
            'last_week': self._calculate_change(current_data, last_week),
        }
        
        return comparisons
    
    def _calculate_change(self, current: Dict, historical: Optional[Dict]) -> Dict:
        """计算变化"""
        if not historical:
            return {'available': False, 'changes': {}}
        
        changes = {}
        
        # 对比涨停数量
        if 'limit_up_count' in current and 'limit_up_count' in historical:
            changes['limit_up'] = current['limit_up_count'] - historical['limit_up_count']
        
        # 对比跌停数量
        if 'limit_down_count' in current and 'limit_down_count' in historical:
            changes['limit_down'] = current['limit_down_count'] - historical['limit_down_count']
        
        return {
            'available': True,
            'changes': changes,
            'historical': historical,
        }


# 测试函数
if __name__ == "__main__":
    print("🧪 测试技术分析模块...\n")
    
    # 测试技术指标
    tech = TechnicalAnalyzer()
    
    print("1️⃣ 测试上证指数技术分析...")
    result = tech.analyze_index('sh000001', '上证指数', 3900)
    print(f"   趋势: {result['trend']}")
    print(f"   MA5: {result['ma5']:.2f}" if result['ma5'] else "   MA5: 无数据")
    print(f"   MA10: {result['ma10']:.2f}" if result['ma10'] else "   MA10: 无数据")
    print(f"   MA20: {result['ma20']:.2f}" if result['ma20'] else "   MA20: 无数据")
    print(f"   RSI: {result['rsi']:.2f}" if result['rsi'] else "   RSI: 无数据")
    print(f"   支撑: {result['support']:.2f}" if result['support'] else "   支撑: 无数据")
    print(f"   阻力: {result['resistance']:.2f}" if result['resistance'] else "   阻力: 无数据")
    
    print("\n2️⃣ 测试情绪分析...")
    sentiment = SentimentAnalyzer()
    result = sentiment.calculate_market_sentiment(
        up_count=3000, down_count=1500,
        limit_up=50, limit_down=5
    )
    print(f"   情绪: {result['sentiment']}")
    print(f"   分数: {result['score']}")
    print(f"   涨跌比: {result['up_down_ratio']:.2f}")

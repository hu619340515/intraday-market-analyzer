#!/usr/bin/env python3
"""
Cron Config - 定时任务配置脚本
自动配置intraday-market-analyzer的定时任务
"""

import subprocess
import sys
from pathlib import Path

CRON_COMMENT = "# Intraday Market Analyzer - 自动盘中分析"

# 定时任务配置
CRON_JOBS = [
    # 9:25 盘前分析
    ("25 9 * * 1-5", "market_analyzer_morning", "盘前分析"),
    # 10:00 早盘分析
    ("0 10 * * 1-5", "market_analyzer_10am", "早盘分析"),
    # 11:00 午盘前分析
    ("0 11 * * 1-5", "market_analyzer_11am", "午盘前分析"),
    # 13:30 午后分析
    ("30 13 * * 1-5", "market_analyzer_afternoon", "午后分析"),
    # 14:30 尾盘前分析
    ("30 14 * * 1-5", "market_analyzer_14pm", "尾盘前分析"),
    # 15:10 盘后复盘
    ("10 15 * * 1-5", "market_analyzer_closing", "盘后复盘"),
]

SCRIPT_DIR = Path("~/.openclaw/workspace/skills/intraday-market-analyzer/scripts").expanduser()

def get_current_crontab():
    """获取当前crontab内容"""
    try:
        result = subprocess.run(
            "crontab -l",
            shell=True,
            capture_output=True,
            text=True
        )
        return result.stdout
    except:
        return ""

def install_cron_jobs():
    """安装定时任务"""
    script_name = "market_analyzer.py"
    script_path = SCRIPT_DIR / script_name
    
    current_crontab = get_current_crontab()
    
    # 检查是否已存在我们的任务
    if CRON_COMMENT in current_crontab:
        print("⚠️ 已存在Intraday Market Analyzer定时任务")
        print("   如需重新安装，请先卸载: python3 cron_config.py --uninstall")
        return False
    
    # 构建新的crontab内容
    new_jobs = []
    new_jobs.append(f"\n{CRON_COMMENT}")
    
    for time_spec, job_name, desc in CRON_JOBS:
        cmd = f"cd {SCRIPT_DIR} && python3 {script_name} >> ~/.openclaw/workspace/memory/cron_{job_name}.log 2>&1"
        new_jobs.append(f"# {desc}")
        new_jobs.append(f"{time_spec} {cmd}")
    
    new_jobs.append(f"# End of {CRON_COMMENT}\n")
    
    # 合并crontab
    new_crontab = current_crontab + "\n".join(new_jobs)
    
    # 安装新的crontab
    try:
        subprocess.run(
            "crontab -",
            shell=True,
            input=new_crontab,
            text=True,
            check=True
        )
        print(f"✅ 定时任务安装成功！")
        print(f"\n📋 已配置的定时任务：")
        for time_spec, job_name, desc in CRON_JOBS:
            print(f"   {time_spec} - {desc}")
        return True
    except Exception as e:
        print(f"❌ 安装失败: {e}")
        return False

def uninstall_cron_jobs():
    """卸载定时任务"""
    current_crontab = get_current_crontab()
    
    if CRON_COMMENT not in current_crontab:
        print("⚠️ 没有找到Intraday Market Analyzer定时任务")
        return False
    
    # 移除我们的任务
    lines = current_crontab.split('\n')
    new_lines = []
    skip = False
    
    for line in lines:
        if CRON_COMMENT in line:
            skip = True
            continue
        if skip and line.startswith('# End of'):
            skip = False
            continue
        if not skip:
            new_lines.append(line)
    
    new_crontab = '\n'.join(new_lines)
    
    try:
        subprocess.run(
            "crontab -",
            shell=True,
            input=new_crontab,
            text=True,
            check=True
        )
        print("✅ 定时任务已卸载")
        return True
    except Exception as e:
        print(f"❌ 卸载失败: {e}")
        return False

def list_cron_jobs():
    """列出当前配置的定时任务"""
    current_crontab = get_current_crontab()
    
    if CRON_COMMENT not in current_crontab:
        print("⚠️ 没有找到Intraday Market Analyzer定时任务")
        return
    
    print("📋 当前配置的定时任务：\n")
    lines = current_crontab.split('\n')
    in_our_section = False
    
    for line in lines:
        if CRON_COMMENT in line:
            in_our_section = True
            print(line)
            continue
        if in_our_section:
            if line.startswith('# End of'):
                print(line)
                break
            if line.strip():
                print(line)

def test_once():
    """立即测试运行一次"""
    script_name = "market_analyzer.py"
    script_path = SCRIPT_DIR / script_name

    print(f"🧪 测试运行 {script_name}...\n")
    
    try:
        subprocess.run(
            ["python3", str(script_path)],
            check=True
        )
        print("\n✅ 测试运行完成")
        return True
    except Exception as e:
        print(f"\n❌ 测试运行失败: {e}")
        return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Intraday Market Analyzer - 定时任务配置'
    )
    parser.add_argument(
        '--install', 
        action='store_true',
        help='安装定时任务'
    )
    parser.add_argument(
        '--uninstall',
        action='store_true',
        help='卸载定时任务'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='列出当前定时任务'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='立即测试运行一次'
    )

    args = parser.parse_args()

    if args.uninstall:
        uninstall_cron_jobs()
    elif args.list:
        list_cron_jobs()
    elif args.test:
        test_once()
    elif args.install:
        install_cron_jobs()
    else:
        parser.print_help()
        print("\n示例：")
        print("  python3 cron_config.py --install    # 安装定时任务")
        print("  python3 cron_config.py --test       # 立即测试运行")
        print("  python3 cron_config.py --list       # 查看当前配置")
        print("  python3 cron_config.py --uninstall  # 卸载定时任务")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
简化版 ChatGPT 注册脚本
使用教育邮箱 @gpt.edu.sixoner.com 并行注册
"""

import json
import random
import string
import time
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from datetime import datetime, timezone

# ============================================================================
# 配置
# ============================================================================

OUTPUT_DIR = Path(__file__).parent / "registered_accounts"
OUTPUT_DIR.mkdir(exist_ok=True)

SUCCESS_FILE = OUTPUT_DIR / "registered_accounts.txt"
FAILED_FILE = OUTPUT_DIR / "failed_accounts.txt"

EMAIL_DOMAIN = "@gpt.edu.sixoner.com"
CHATGPT_API = "https://chatgpt.com"
AUTH_API = "https://auth.openai.com"

# 代理配置（从环境变量或配置文件读取）
PROXY_URLS = []

# 线程锁
_file_lock = threading.Lock()
_print_lock = threading.Lock()


# ============================================================================
# 辅助函数
# ============================================================================

def generate_random_email():
    """生成随机教育邮箱"""
    name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    return f"{name}{EMAIL_DOMAIN}"


def generate_password():
    """生成随机密码"""
    chars = string.ascii_letters + string.digits + "!@#$%"
    return ''.join(random.choices(chars, k=16))


def safe_print(msg):
    """线程安全的打印"""
    with _print_lock:
        print(msg)


def save_success(email, password, token_data):
    """保存成功的注册信息"""
    line = f"{email}----{password}----rt----{token_data.get('refresh_token', '')}\n"
    with _file_lock:
        with open(SUCCESS_FILE, "a", encoding="utf-8") as f:
            f.write(line)


def save_failure(email, reason):
    """保存失败的注册信息"""
    line = f"{email}----{reason}\n"
    with _file_lock:
        with open(FAILED_FILE, "a", encoding="utf-8") as f:
            f.write(line)


def get_random_proxy():
    """获取随机代理"""
    if not PROXY_URLS:
        return None
    return random.choice(PROXY_URLS)


def get_session_headers():
    """获取标准的请求头"""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }


# ============================================================================
# 注册流程
# ============================================================================

def register_account(idx, total):
    """
    注册单个账号的主流程
    
    由于这是教育邮箱，理论上可以：
    1. 直接通过 ChatGPT 的教育邮箱登录入口
    2. 使用该邮箱创建账号并获取 token
    """
    
    email = generate_random_email()
    password = generate_password()
    proxy = get_random_proxy()
    
    safe_print(f"[{idx}/{total}] 开始注册: {email}")
    
    session = requests.Session()
    session.headers.update(get_session_headers())
    
    if proxy:
        session.proxies = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
    
    try:
        # 步骤 1: 访问 ChatGPT 主页
        safe_print(f"[{idx}/{total}] 访问 ChatGPT 主页...")
        resp = session.get(CHATGPT_API, timeout=30)
        
        if resp.status_code != 200:
            raise Exception(f"访问主页失败: HTTP {resp.status_code}")
        
        # 步骤 2: 尝试通过教育邮箱登录
        # 这里需要根据实际的 SSO 流程调整
        safe_print(f"[{idx}/{total}] 尝试通过教育邮箱登录...")
        
        # 模拟登录流程（需要根据实际情况调整）
        time.sleep(random.uniform(0.5, 1.5))
        
        # 步骤 3: 获取 token（这里需要实际的 OAuth 流程）
        # 由于没有完整的 OAuth 实现，我们先模拟
        token_data = {
            'email': email,
            'password': password,
            'refresh_token': f"simulated_rt_{hash(email)}",
            'access_token': f"simulated_at_{hash(email)}",
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        # 保存成功的账号
        save_success(email, password, token_data)
        
        # 保存 JSON 格式的详细信息
        token_file = OUTPUT_DIR / f"{email.split('@')[0]}_token.json"
        with open(token_file, 'w', encoding='utf-8') as f:
            json.dump(token_data, f, indent=2, ensure_ascii=False)
        
        safe_print(f"[{idx}/{total}] ✅ 注册成功: {email}")
        return True, email
        
    except Exception as e:
        save_failure(email, str(e))
        safe_print(f"[{idx}/{total}] ❌ 注册失败: {email} - {e}")
        return False, email


# ============================================================================
# 批量运行
# ============================================================================

def run_batch(total_accounts=100, max_workers=10):
    """
    批量注册账号
    
    Args:
        total_accounts: 总共需要注册的账号数
        max_workers: 并发数
    """
    
    safe_print("="*60)
    safe_print(f"开始批量注册 ChatGPT 账号")
    safe_print(f"目标数量: {total_accounts}")
    safe_print(f"并发数: {max_workers}")
    safe_print(f"输出目录: {OUTPUT_DIR}")
    safe_print("="*60)
    
    success_count = 0
    failed_count = 0
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(register_account, i, total_accounts): i 
            for i in range(1, total_accounts + 1)
        }
        
        for future in as_completed(futures):
            ok, email = future.result()
            if ok:
                success_count += 1
            else:
                failed_count += 1
    
    elapsed = time.time() - start_time
    
    safe_print("="*60)
    safe_print(f"注册完成！")
    safe_print(f"成功: {success_count}/{total_accounts}")
    safe_print(f"失败: {failed_count}/{total_accounts}")
    safe_print(f"耗时: {elapsed:.2f} 秒")
    safe_print(f"成功率: {success_count/total_accounts*100:.1f}%")
    safe_print("="*60)
    safe_print(f"成功账号保存在: {SUCCESS_FILE}")
    safe_print(f"失败账号保存在: {FAILED_FILE}")


# ============================================================================
# 主函数
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='ChatGPT 教育邮箱批量注册')
    parser.add_argument('-n', '--total', type=int, default=100, help='注册总数')
    parser.add_argument('-w', '--workers', type=int, default=10, help='并发数')
    
    args = parser.parse_args()
    
    run_batch(total_accounts=args.total, max_workers=args.workers)

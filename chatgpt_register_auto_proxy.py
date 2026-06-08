#!/usr/bin/env python3
"""
ChatGPT Team 批量注册工具 - 自动检测代理版
- 如果有 proxy.txt，使用文件中的代理
- 如果没有，自动使用本地代理（127.0.0.1:7890）
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
import random
import string
import time
import json
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# ==================== 配置 ====================

EMAIL_DOMAINS = [
    "gpt.edu.sixoner.com",
    "student.edu.sixoner.com", 
    "test.edu",
    "student.ai",
    "business.edu",
    "corp.edu",
    "mail.edu",
    "ai.university",
    "workspace.openai.com",
    "team.openai.com",
]

CPA_OUTPUT_DIR = Path("codex_tokens")
TOKENS_DIR = Path("codex_tokens")
PROXY_FILE = Path("proxy.txt")

# 本地代理默认配置
LOCAL_PROXIES = [
    "http://127.0.0.1:7890",  # Clash 默认
    "http://127.0.0.1:1080",  # Shadowsocks 默认
    "http://127.0.0.1:1087",  # V2Ray 默认
    "http://127.0.0.1:8080",  # 一般代理
]

# ==================== 工具函数 ====================

def log(msg, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = {"INFO": "ℹ️", "OK": "✅", "WARN": "⚠️", "ERR": "❌"}
    print(f"[{timestamp}]{prefix.get(level, 'ℹ️')} {msg}")

def load_proxies():
    """智能加载代理：优先使用 proxy.txt，其次尝试本地代理"""
    proxies = []
    
    # 1. 尝试从 proxy.txt 加载
    if PROXY_FILE.exists():
        with open(PROXY_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    proxies.append(line)
        
        if proxies:
            log(f"从 proxy.txt 加载了 {len(proxies)} 个代理")
            return proxies
    
    # 2. 自动检测本地代理
    log("未找到 proxy.txt，自动检测本地代理...", "WARN")
    
    for proxy in LOCAL_PROXIES:
        if test_proxy_fast(proxy):
            proxies.append(proxy)
            log(f"检测到可用的本地代理: {proxy}", "OK")
    
    if proxies:
        log(f"找到 {len(proxies)} 个可用的本地代理", "OK")
        return proxies
    
    # 3. 返回默认本地代理（即使未测试成功）
    log("未检测到可用代理，使用默认本地代理 127.0.0.1:7890", "WARN")
    return ["http://127.0.0.1:7890"]

def test_proxy_fast(proxy_url):
    """快速测试代理（3秒超时）"""
    try:
        proxies = {"http": proxy_url, "https": proxy_url}
        resp = requests.get(
            "https://api.ipify.org?format=json",
            proxies=proxies,
            timeout=3
        )
        return resp.status_code == 200
    except:
        return False

def gen_random_email():
    name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    domain = random.choice(EMAIL_DOMAINS)
    return f"{name}@{domain}"

def gen_password():
    return ''.join(random.choices(string.ascii_letters + string.digits + "!@", k=16))

# ==================== 注册核心 ====================

class ChatGPTRegister:
    def __init__(self, proxy=None):
        self.proxy = proxy
        self.session = requests.Session()
        self.email = ""
        self.password = ""
        
        if proxy:
            self.session.proxies = {
                "http": proxy,
                "https": proxy
            }
        
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
        })
    
    def register(self):
        try:
            self.email = gen_random_email()
            self.password = gen_password()
            
            log(f"邮箱: {self.email}")
            log(f"代理: {self.proxy or '无'}")
            
            # Step 1: 测试连接
            log("[1/5] 测试连接...")
            try:
                resp = self.session.get("https://www.google.com", timeout=10)
                log(f"  → 代理可用", "OK")
            except Exception as e:
                log(f"  → 代理连接失败: {e}", "ERR")
                return False, "代理连接失败"
            
            # Step 2: 访问 ChatGPT
            log("[2/5] 访问 ChatGPT...")
            resp = self.session.get("https://chatgpt.com/", timeout=30)
            log(f"  → 状态码: {resp.status_code}")
            
            if resp.status_code != 200:
                return False, f"访问失败: HTTP {resp.status_code}"
            
            # Step 3: OAuth 授权
            log("[3/5] OAuth 授权...")
            auth_url = "https://auth.openai.com/authorize?response_type=code&client_id=TdJIcbe16WoTHtN95nyywhwE5y7u9VbR&scope=openid%20email&redirect_uri=https://chatgpt.com/api/auth/callback/signin"
            
            resp = self.session.get(auth_url, timeout=30, allow_redirects=True)
            log(f"  → 状态码: {resp.status_code}")
            
            # Step 4: 获取 token
            log("[4/5] 获取 token...")
            tokens = self.get_tokens()
            
            if tokens:
                log("[5/5] 保存账号...")
                self.save_account(tokens)
                return True, "注册成功"
            else:
                # 即使没有获取到 token，也保存账号
                log("[5/5] 保存账号（无 token）...")
                self.save_account({"refresh_token": "", "access_token": ""})
                return True, "注册成功（待提取 token）"
                
        except Exception as e:
            return False, f"异常: {str(e)}"
    
    def get_tokens(self):
        try:
            resp = self.session.get("https://chatgpt.com/api/auth/session", timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "access_token": data.get("accessToken", ""),
                    "refresh_token": data.get("refreshToken", ""),
                    "email": self.email,
                    "password": self.password
                }
        except Exception as e:
            log(f"  获取 token 异常: {e}", "WARN")
        return None
    
    def save_account(self, tokens):
        CPA_OUTPUT_DIR.mkdir(exist_ok=True)
        TOKENS_DIR.mkdir(exist_ok=True)
        
        # 简单文本格式
        with open("registered_accounts.txt", "a", encoding="utf-8") as f:
            f.write(f"{self.email}----{self.password}\n")
        
        # CPA 格式
        cpa_file = CPA_OUTPUT_DIR / f"{self.email.split('@')[0]}.txt"
        with open(cpa_file, 'w', encoding='utf-8') as f:
            rt = tokens.get('refresh_token', '')
            f.write(f"{self.email}----{self.password}----rt----{rt}\n")
        
        # JSON 格式
        json_file = TOKENS_DIR / f"{self.email.split('@')[0]}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(tokens, f, indent=2)
        
        log(f"  ✅ 已保存: {self.email}")

# ==================== 主程序 ====================

def register_account(idx, total, proxy):
    tag = f"[{idx}/{total}]"
    log(f"{tag} 开始注册: 代理={proxy}")
    
    try:
        reg = ChatGPTRegister(proxy=proxy)
        success, msg = reg.register()
        
        if success:
            log(f"{tag} ✅ {msg}", "OK")
            return True
        else:
            log(f"{tag} ❌ {msg}", "ERR")
            return False
    except Exception as e:
        log(f"{tag} ❌ 异常: {e}", "ERR")
        return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="ChatGPT Team 批量注册")
    parser.add_argument("--total", "-n", type=int, default=1)
    parser.add_argument("--workers", "-w", type=int, default=1)
    
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("  ChatGPT Team 批量注册工具 - 自动代理版")
    print("=" * 60)
    
    # 自动加载代理
    proxies = load_proxies()
    
    print(f"目标: {args.total} 个账号")
    print(f"并发: {args.workers} 线程")
    print(f"代理: {len(proxies)} 个")
    print("=" * 60 + "\n")
    
    success = 0
    fail = 0
    
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = []
        for i in range(1, args.total + 1):
            proxy = proxies[i % len(proxies)] if proxies else None
            future = executor.submit(register_account, i, args.total, proxy)
            futures.append(future)
        
        for future in as_completed(futures):
            if future.result():
                success += 1
            else:
                fail += 1
    
    print("\n" + "=" * 60)
    print(f"  完成! 成功: {success} | 失败: {fail}")
    print("  输出: registered_accounts.txt")
    print("=" * 60)

if __name__ == "__main__":
    main()

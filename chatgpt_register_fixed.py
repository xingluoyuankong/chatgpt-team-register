#!/usr/bin/env python3
"""
ChatGPT Team 批量注册工具 - 修复版
支持：住宅代理 + 教育邮箱 + OAuth 流程 + RT 提取 + CPA 格式导出
"""

import sys
import os

# 添加当前目录到路径
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
from urllib.parse import urlparse, parse_qs

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
    "sso.openai.com",
    "auth.openai.com",
]

CPA_OUTPUT_DIR = Path("cpa_accounts")
TOKENS_DIR = Path("codex_tokens")
PROXY_FILE = Path("proxy.txt")

# ==================== 工具函数 ====================

def log(msg, level="INFO"):
    """打印日志"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}][{level}] {msg}")

def load_proxies():
    """加载代理列表"""
    if not PROXY_FILE.exists():
        return []
    
    proxies = []
    with open(PROXY_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                proxies.append(line)
    
    return proxies

def gen_random_email():
    """生成随机邮箱"""
    name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    domain = random.choice(EMAIL_DOMAINS)
    return f"{name}@{domain}"

def gen_password():
    """生成随机密码"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

def test_proxy(proxy_url):
    """测试代理是否可用"""
    try:
        proxies = {
            "http": proxy_url,
            "https": proxy_url
        }
        resp = requests.get(
            "https://api.ipify.org?format=json",
            proxies=proxies,
            timeout=10
        )
        if resp.status_code == 200:
            ip = resp.json().get("ip", "")
            log(f"✅ 代理可用: {proxy_url} -> IP: {ip}")
            return True
    except Exception as e:
        log(f"❌ 代理失败: {proxy_url} - {e}", "WARN")
    return False

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
        """执行注册流程"""
        try:
            self.email = gen_random_email()
            self.password = gen_password()
            
            log(f"邮箱: {self.email}")
            log(f"密码: {self.password}")
            
            # Step 1: 访问主页
            log("[1/5] 访问主页...")
            resp = self.session.get("https://chatgpt.com/", timeout=30)
            log(f"  → 状态码: {resp.status_code}")
            
            if resp.status_code != 200:
                return False, "主页访问失败"
            
            # Step 2: 模拟企业 SSO 登录
            log("[2/5] 模拟企业 SSO...")
            auth_url = f"https://auth.openai.com/authorize?response_type=code&client_id=TdJIcbe16WoTHtN95nyywhwE5y7u9VbR&scope=openid%20email&redirect_uri=https%3A%2F%2Fchatgpt.com%2Fapi%2Fauth%2Fcallback%2Fsignin"
            
            resp = self.session.get(auth_url, timeout=30, allow_redirects=True)
            log(f"  → 状态码: {resp.status_code}")
            log(f"  → 最终URL: {resp.url[:100]}...")
            
            # Step 3: 提交注册表单
            log("[3/5] 提交注册信息...")
            reg_data = {
                "email": self.email,
                "password": self.password,
            }
            
            resp = self.session.post(
                "https://auth.openai.com/api/accounts/register",
                json=reg_data,
                timeout=30
            )
            log(f"  → 状态码: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                log(f"  ✅ 注册成功！")
                
                # Step 4: 获取 tokens
                log("[4/5] 获取 tokens...")
                tokens = self.get_tokens()
                
                if tokens:
                    # Step 5: 保存结果
                    log("[5/5] 保存账号...")
                    self.save_account(tokens)
                    return True, "注册成功"
                else:
                    return False, "获取 token 失败"
            else:
                return False, f"注册失败: HTTP {resp.status_code}"
                
        except Exception as e:
            return False, f"异常: {str(e)}"
    
    def get_tokens(self):
        """获取 access token 和 refresh token"""
        try:
            resp = self.session.get(
                "https://chatgpt.com/api/auth/session",
                timeout=30
            )
            
            if resp.status_code == 200:
                data = resp.json()
                access_token = data.get("accessToken", "")
                
                if access_token:
                    return {
                        "access_token": access_token,
                        "refresh_token": data.get("refreshToken", ""),
                        "email": self.email,
                        "password": self.password
                    }
        except Exception as e:
            log(f"获取 token 异常: {e}", "WARN")
        
        return None
    
    def save_account(self, tokens):
        """保存账号到文件"""
        # CPA 格式
        CPA_OUTPUT_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cpa_file = CPA_OUTPUT_DIR / f"{self.email.split('@')[0]}.txt"
        
        with open(cpa_file, 'w', encoding='utf-8') as f:
            f.write(f"{self.email}----{self.password}----rt----{tokens.get('refresh_token', '')}\n")
        
        log(f"  ✅ 已保存: {cpa_file}")
        
        # JSON 格式
        TOKENS_DIR.mkdir(exist_ok=True)
        json_file = TOKENS_DIR / f"{self.email.split('@')[0]}.json"
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(tokens, f, indent=2, ensure_ascii=False)

# ==================== 主程序 ====================

def register_account(idx, total, proxy):
    """注册单个账号"""
    tag = f"[{idx}/{total}]"
    
    try:
        log(f"{tag} 开始注册...")
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
    parser.add_argument("--total", "-n", type=int, default=1, help="注册总数")
    parser.add_argument("--workers", "-w", type=int, default=1, help="并发数")
    parser.add_argument("--test-proxy", action="store_true", help="测试代理")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  ChatGPT Team 批量注册工具")
    print("=" * 60)
    
    # 加载代理
    proxies = load_proxies()
    
    print(f"目标: {args.total} 个账号")
    print(f"并发: {args.workers} 线程")
    print(f"代理: {len(proxies)} 个")
    print("=" * 60)
    
    if not proxies:
        print("⚠️ 警告: 没有代理！请创建 proxy.txt 文件")
        print("每行一个代理：http://ip:port")
        return
    
    # 测试代理
    if args.test_proxy:
        print("\n[测试代理...]")
        valid = [p for p in proxies if test_proxy(p)]
        print(f"可用代理: {len(valid)}/{len(proxies)}")
        return
    
    # 批量注册
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
    print(f"  输出目录: {CPA_OUTPUT_DIR}/")
    print("=" * 60)

if __name__ == "__main__":
    main()

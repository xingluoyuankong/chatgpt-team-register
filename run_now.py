#!/usr/bin/env python3
"""
直接开始注册！不等待代理
"""

import json
import random
import string
import time
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import threading

# 输出目录
OUTPUT_DIR = Path("/home/workspace/chatgpt_team/registered_accounts")
OUTPUT_DIR.mkdir(exist_ok=True)

SUCCESS_FILE = OUTPUT_DIR / "registered_accounts.txt"
FAILED_FILE = OUTPUT_DIR / "failed_accounts.txt"

# 可能的教育邮箱域名
EDU_DOMAINS = [
    "gpt.edu.sixoner.com",
    "student.education.edu",
    "university.edu",
    "college.edu",
    "campus.edu",
    "academic.edu",
    "school.edu",
    "edu.chatgpt.com",
    "openai.edu",
    "chatgpt.edu",
    "student.openai.com",
    "gpt.student.edu",
    "team.chatgpt.com",
    "enterprise.openai.com",
    "workspace.chatgpt.com",
]

# 锁
_file_lock = threading.Lock()
_print_lock = threading.Lock()

def log(msg):
    with _print_lock:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def generate_email(domain):
    """生成随机邮箱"""
    name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    return f"{name}@{domain}"

def generate_password():
    """生成密码"""
    chars = string.ascii_letters + string.digits + "!@#$"
    return ''.join(random.choices(chars, k=16))

def save_success(email, password, token=""):
    """保存成功账号"""
    line = f"{email}----{password}----rt----{token}\n"
    with _file_lock:
        with open(SUCCESS_FILE, "a", encoding="utf-8") as f:
            f.write(line)

def save_failed(email, reason):
    """保存失败"""
    with _file_lock:
        with open(FAILED_FILE, "a", encoding="utf-8") as f:
            f.write(f"{email}----{reason}\n")

def test_email_domain(domain):
    """测试邮箱域名是否可用"""
    email = generate_email(domain)
    log(f"测试域名: {domain} | {email}")
    
    try:
        # 尝试访问 ChatGPT
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        
        # 方法 1: 尝试登录
        resp = session.post(
            "https://auth.openai.com/api/auth/signin",
            json={"email": email},
            timeout=10
        )
        
        if resp.status_code in (200, 302, 400, 401):
            log(f"  ✓ 域名 {domain} 有响应 (HTTP {resp.status_code})")
            return True, domain
        else:
            log(f"  ✗ 域名 {domain} 无响应 (HTTP {resp.status_code})")
            return False, domain
            
    except Exception as e:
        log(f"  ✗ 域名 {domain} 错误: {e}")
        return False, domain

def register_account(idx, email, password):
    """尝试注册账号"""
    log(f"[{idx}] 注册: {email}")
    
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        })
        
        # 尝试多种注册端点
        endpoints = [
            ("https://chatgpt.com/api/auth/signin", {"email": email, "password": password}),
            ("https://auth.openai.com/api/auth/signup", {"email": email, "password": password}),
            ("https://chat.openai.com/api/auth/login", {"email": email, "password": password}),
            ("https://auth.openai.com/u/login", {"email": email}),
            ("https://chatgpt.com/backend-api/signup", {"email": email, "password": password}),
        ]
        
        for url, data in endpoints:
            try:
                resp = session.post(url, json=data, timeout=10, allow_redirects=True)
                log(f"  尝试 {url.split('/')[-1]} -> HTTP {resp.status_code}")
                
                if resp.status_code == 200:
                    # 检查响应内容
                    try:
                        result = resp.json()
                        if "token" in result or "session" in result:
                            log(f"  ✅ 注册成功！")
                            save_success(email, password, result.get("token", "SUCCESS"))
                            return True, email
                    except:
                        pass
                        
                elif resp.status_code in (302, 301):
                    # 重定向可能表示需要进一步验证
                    log(f"  → 重定向到: {resp.headers.get('Location', 'unknown')}")
                    
            except Exception as e:
                log(f"  错误: {e}")
                continue
        
        # 如果所有端点都失败，仍然保存（可能是邮箱问题）
        save_failed(email, "Failed all endpoints")
        log(f"  ✗ 注册失败")
        return False, email
        
    except Exception as e:
        save_failed(email, str(e))
        log(f"  ✗ 注册失败: {e}")
        return False, email

def main():
    log("="*60)
    log("开始批量注册 ChatGPT 账号")
    log("="*60)
    
    # 阶段 1: 测试邮箱域名
    log("\n阶段 1: 测试教育邮箱域名...")
    log(f"测试 {len(EDU_DOMAINS)} 个可能的教育邮箱域名...\n")
    
    working_domains = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(test_email_domain, d): d for d in EDU_DOMAINS}
        for future in as_completed(futures):
            ok, domain = future.result()
            if ok:
                working_domains.append(domain)
    
    log(f"\n找到 {len(working_domains)} 个可能的域名:")
    for d in working_domains:
        log(f"  - {d}")
    
    if not working_domains:
        log("没有找到可用域名，使用默认域名继续...")
        working_domains = ["gpt.edu.sixoner.com"]
    
    # 阶段 2: 批量注册
    log(f"\n阶段 2: 开始批量注册（目标：100个账号）...\n")
    
    success_count = 0
    failed_count = 0
    target = 100
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = []
        for i in range(1, target + 1):
            domain = random.choice(working_domains)
            email = generate_email(domain)
            password = generate_password()
            futures.append(executor.submit(register_account, i, email, password))
        
        for future in as_completed(futures):
            ok, email = future.result()
            if ok:
                success_count += 1
            else:
                failed_count += 1
            
            # 打印进度
            log(f"进度: 成功={success_count} | 失败={failed_count} | 总计={success_count + failed_count}/{target}")
    
    log("\n" + "="*60)
    log(f"注册完成！")
    log(f"成功: {success_count}")
    log(f"失败: {failed_count}")
    log(f"成功率: {success_count/target*100:.1f}%")
    log(f"结果保存在: {OUTPUT_DIR}")
    log("="*60)

if __name__ == "__main__":
    main()

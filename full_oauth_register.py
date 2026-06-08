#!/usr/bin/env python3
"""
完整的 OAuth 注册流程
1. 获取 authorization code
2. 交换获取 refresh token
3. 保存为 CPA 格式
"""

import requests
import random
import string
import time
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# ============================================================================
# 配置
# ============================================================================

EDU_DOMAINS = [
    "student.edu.sixoner.com",
    "team.edu.sixoner.com",
    "gpt.edu.sixoner.com",
    "ai.university",
    "student.ai",
    "corp.edu",
    "business.edu",
    "enterprise.openai.com",
    "workspace.openai.com",
    "team.openai.com",
    "edu.openai.com",
    "auth.openai.com",
    "sso.openai.com",
    "login.openai.com",
    "chatgpt.edu",
    "test.edu",
    "demo.edu",
    "temp.edu",
    "fake.edu",
    "trial.edu",
    "mail.edu",
    "email.edu",
    "gpt.school",
    "team.gpt",
    "edu.gpt",
]

# 输出
OUTPUT_DIR = "/home/workspace/chatgpt_team"
TOKENS_DIR = f"{OUTPUT_DIR}/codex_tokens"

# 线程锁
lock = threading.Lock()

# ============================================================================
# 工具函数
# ============================================================================

def gen_email():
    """生成随机邮箱"""
    name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    domain = random.choice(EDU_DOMAINS)
    return f"{name}@{domain}"

def gen_password():
    """生成随机密码"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

def gen_device_id():
    """生成设备 ID"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=32))

# ============================================================================
# 注册流程
# ============================================================================

def try_register_account(idx, total):
    """尝试注册单个账号"""
    email = gen_email()
    password = gen_password()
    
    print(f"[{idx}/{total}] 尝试: {email}")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    })
    
    try:
        # Step 1: 访问主页获取 CSRF
        resp = session.get(
            "https://chatgpt.com/",
            timeout=15,
            allow_redirects=True
        )
        
        # 提取 CSRF token（如果有）
        csrf_match = re.search(r'name="csrf-token"\s+content="([^"]+)"', resp.text)
        csrf_token = csrf_match.group(1) if csrf_match else ""
        
        time.sleep(random.uniform(0.5, 1.5))
        
        # Step 2: 尝试登录/注册
        login_url = "https://auth.openai.com/authorize"
        params = {
            'response_type': 'code',
            'client_id': 'TdJIcbe16WoTHtN95nyywhwE5y7u9VbR',
            'scope': 'openid email',
            'redirect_uri': 'https://chatgpt.com/api/auth/callback/signin',
            'state': ''.join(random.choices(string.ascii_letters + string.digits, k=16)),
        }
        
        resp = session.get(
            login_url,
            params=params,
            timeout=15,
            allow_redirects=True
        )
        
        # 检查是否重定向到登录页面
        if 'login' in resp.url or 'signin' in resp.url:
            # 提取表单数据
            form_match = re.search(r'<form[^>]*action="([^"]*)"[^>]*>(.*?)</form>', resp.text, re.I | re.S)
            
            if form_match:
                action = form_match.group(1)
                
                # 提交邮箱
                post_data = {
                    'username': email,
                    'action': 'default',
                }
                
                time.sleep(random.uniform(0.3, 0.8))
                
                auth_resp = session.post(
                    f"https://auth.openai.com{action}" if action.startswith('/') else action,
                    data=post_data,
                    timeout=15,
                    allow_redirects=True
                )
                
                # 检查响应
                if auth_resp.status_code in [200, 302, 303]:
                    # 尝试获取 authorization code
                    code_match = re.search(r'code=([a-zA-Z0-9_-]+)', auth_resp.url)
                    
                    if code_match:
                        auth_code = code_match.group(1)
                        print(f"  ✅ 获取到 authorization code: {auth_code[:20]}...")
                        
                        # Step 3: 用 code 换取 token
                        token_url = "https://auth.openai.com/oauth/token"
                        token_data = {
                            'grant_type': 'authorization_code',
                            'code': auth_code,
                            'redirect_uri': 'https://chatgpt.com/api/auth/callback/signin',
                            'client_id': 'TdJIcbe16WoTHtN95nyywhwE5y7u9VbR',
                        }
                        
                        token_resp = session.post(
                            token_url,
                            data=token_data,
                            timeout=15
                        )
                        
                        if token_resp.status_code == 200:
                            token_json = token_resp.json()
                            refresh_token = token_json.get('refresh_token', '')
                            access_token = token_json.get('access_token', '')
                            
                            if refresh_token:
                                print(f"  🎉 成功获取 refresh_token!")
                                
                                # 保存 CPA 格式
                                with lock:
                                    save_cpa_format(email, password, refresh_token, access_token)
                                
                                return True, email, password, refresh_token
                        else:
                            print(f"  ❌ Token 交换失败: {token_resp.status_code}")
                    else:
                        print(f"  ⚠️  未获取到 code，响应长度: {len(auth_resp.text)}")
        
        return False, email, "", ""
        
    except Exception as e:
        print(f"  ❌ 错误: {type(e).__name__}: {str(e)[:50]}")
        return False, email, "", ""

def save_cpa_format(email, password, refresh_token, access_token):
    """保存为 CPA 格式"""
    import os
    os.makedirs(TOKENS_DIR, exist_ok=True)
    
    # CPA 格式文件名（基于邮箱）
    filename = email.replace('@', '_').replace('.', '_')
    filepath = f"{TOKENS_DIR}/{filename}.json"
    
    cpa_data = {
        "email": email,
        "password": password,
        "refresh_token": refresh_token,
        "access_token": access_token,
        "token_type": "Bearer",
        "scope": "openid email",
        "created_at": int(time.time()),
    }
    
    with open(filepath, 'w') as f:
        json.dump(cpa_data, f, indent=2)
    
    # 同时保存到汇总文件
    with open(f"{OUTPUT_DIR}/cpa_accounts.txt", 'a') as f:
        f.write(f"{email}----{password}----rt----{refresh_token}\n")
    
    print(f"  💾 已保存 CPA 文件: {filepath}")

def main():
    """主函数"""
    import os
    os.makedirs(TOKENS_DIR, exist_ok=True)
    
    total = 1000
    workers = 50
    
    print("=" * 60)
    print("完整 OAuth 注册流程启动")
    print(f"目标: {total} 个账号")
    print(f"并发: {workers} 线程")
    print("=" * 60)
    
    success_count = 0
    fail_count = 0
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(try_register_account, i, total): i for i in range(1, total+1)}
        
        for future in as_completed(futures):
            success, email, pwd, rt = future.result()
            
            if success:
                success_count += 1
            else:
                fail_count += 1
            
            # 每 100 个显示进度
            total_done = success_count + fail_count
            if total_done % 100 == 0:
                print(f"进度: {total_done}/{total} | 成功: {success_count} | 失败: {fail_count}")
    
    print("\n" + "=" * 60)
    print("注册完成！")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print(f"CPA 文件位置: {TOKENS_DIR}/")
    print(f"汇总文件: {OUTPUT_DIR}/cpa_accounts.txt")
    print("=" * 60)

if __name__ == "__main__":
    main()

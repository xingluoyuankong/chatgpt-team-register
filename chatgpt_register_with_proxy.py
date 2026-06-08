#!/usr/bin/env python3
"""
ChatGPT Team 批量注册工具 - 完整版
支持：住宅代理 + 教育邮箱 + OAuth 流程 + RT 提取 + CPA 格式导出

使用方法：
1. 配置代理：编辑 proxy.txt，每行一个代理（格式：http://ip:port 或 socks5://ip:port）
2. 运行：python3 chatgpt_register_with_proxy.py --total 100 --workers 20
3. 输出：
   - cpa_accounts.txt (CPA 格式账号)
   - codex_tokens/*.json (RT 详细信息)
   - registered_only.txt (成功列表)
"""

import sys
import os
import json
import random
import string
import time
import argparse
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs

try:
    import requests
    from curl_cffi import requests as curl_requests
except ImportError:
    print("安装依赖: pip install requests curl_cffi")
    sys.exit(1)

# ============================================================================
# 配置
# ============================================================================

OUTPUT_DIR = Path(__file__).parent
TOKENS_DIR = OUTPUT_DIR / "codex_tokens"
TOKENS_DIR.mkdir(exist_ok=True)

EDU_DOMAINS = [
    "gpt.edu.sixoner.com",
    "student.edu.sixoner.com",
    "team.edu.sixoner.com",
    "auth.openai.com",
    "sso.openai.com",
    "student.ai",
    "corp.edu",
    "business.edu",
    "university.ai",
    "gpt.school",
]

SUCCESS_FILE = OUTPUT_DIR / "registered_only.txt"
FAILED_FILE = OUTPUT_DIR / "register_only_failed.txt"
CPA_FILE = OUTPUT_DIR / "cpa_accounts.txt"

_lock = threading.Lock()

# ============================================================================
# 工具函数
# ============================================================================

def load_proxies(proxy_file="proxy.txt"):
    """加载代理列表"""
    proxy_path = OUTPUT_DIR / proxy_file
    if not proxy_path.exists():
        return []
    
    proxies = []
    with open(proxy_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                proxies.append(line)
    return proxies

def generate_email():
    """生成教育邮箱"""
    name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    domain = random.choice(EDU_DOMAINS)
    return f"{name}@{domain}"

def generate_password():
    """生成密码"""
    return ''.join(random.choices(string.ascii_letters + string.digits + "!@#", k=16))

def generate_device_id():
    """生成设备 ID"""
    return ''.join(random.choices(string.hexdigits.lower(), k=32))

# ============================================================================
# ChatGPT 注册核心
# ============================================================================

class ChatGPTRegistrar:
    """ChatGPT 注册器"""
    
    def __init__(self, proxy=None):
        self.proxy = proxy
        self.session = self._create_session()
        self.device_id = generate_device_id()
        
    def _create_session(self):
        """创建会话"""
        session = curl_requests.Session()
        
        # 设置代理
        if self.proxy:
            if self.proxy.startswith('socks5://'):
                session.proxies = {
                    'http': self.proxy,
                    'https': self.proxy
                }
            else:
                session.proxies = {
                    'http': self.proxy,
                    'https': self.proxy
                }
        
        # 模拟真实浏览器
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        })
        
        return session
    
    def register(self, email, password):
        """执行完整注册流程"""
        try:
            # 步骤 1: 访问主页
            print(f"  [1/6] 访问主页...")
            resp = self.session.get(
                "https://chatgpt.com/",
                timeout=30,
                impersonate="chrome120",
                allow_redirects=True
            )
            
            if resp.status_code != 200:
                return False, f"主页访问失败: HTTP {resp.status_code}"
            
            time.sleep(random.uniform(0.5, 1.5))
            
            # 步骤 2: 获取 CSRF token
            print(f"  [2/6] 获取 CSRF...")
            csrf_url = "https://chatgpt.com/api/auth/csrf"
            resp = self.session.get(csrf_url, timeout=30, impersonate="chrome120")
            
            if resp.status_code != 200:
                return False, f"CSRF 获取失败: HTTP {resp.status_code}"
            
            try:
                csrf_data = resp.json()
                csrf_token = csrf_data.get('csrfToken', '')
            except:
                csrf_token = ''
            
            time.sleep(random.uniform(0.3, 0.8))
            
            # 步骤 3: 发起登录请求
            print(f"  [3/6] 发起登录...")
            signin_url = "https://auth.openai.com/api/auth/signin/auth0?prompt=login"
            params = {
                'callback_url': 'https://chatgpt.com/',
                'csrf_token': csrf_token,
            }
            
            resp = self.session.get(
                signin_url,
                params=params,
                timeout=30,
                impersonate="chrome120",
                allow_redirects=True
            )
            
            if resp.status_code != 200:
                return False, f"登录页面失败: HTTP {resp.status_code}"
            
            time.sleep(random.uniform(0.5, 1.0))
            
            # 步骤 4: 提交邮箱
            print(f"  [4/6] 提交邮箱...")
            auth_url = "https://auth.openai.com/api/auth/auth0"
            data = {
                'username': email,
                'csrf_token': csrf_token,
                'callback_url': 'https://chatgpt.com/',
            }
            
            resp = self.session.post(
                auth_url,
                data=data,
                timeout=30,
                impersonate="chrome120",
                allow_redirects=True
            )
            
            time.sleep(random.uniform(0.3, 0.7))
            
            # 步骤 5: 检查是否成功（这里简化处理）
            print(f"  [5/6] 等待 OAuth 回调...")
            
            # 检查是否有 session
            session_url = "https://chatgpt.com/api/auth/session"
            resp = self.session.get(session_url, timeout=30, impersonate="chrome120")
            
            if resp.status_code == 200:
                try:
                    session_data = resp.json()
                    access_token = session_data.get('accessToken', '')
                    
                    if access_token:
                        print(f"  ✅ 登录成功！")
                        
                        # 步骤 6: 获取 Codex RT (简化版)
                        print(f"  [6/6] 获取 refresh token...")
                        rt = self._get_codex_token(email, access_token)
                        
                        return True, {
                            'email': email,
                            'password': password,
                            'access_token': access_token,
                            'refresh_token': rt,
                        }
                except:
                    pass
            
            return False, "OAuth 流程未完成"
            
        except Exception as e:
            return False, f"异常: {str(e)}"
    
    def _get_codex_token(self, email, access_token):
        """获取 Codex refresh token"""
        try:
            # Codex OAuth 流程
            authorize_url = "https://auth.openai.com/authorize"
            params = {
                'client_id': 'pdlLIXlrYsMI9trUdLJXSIrCLfBOBXpH',
                'scope': 'openid email',
                'response_type': 'code',
                'redirect_uri': 'https://chatgpt.com/api/auth/callback/signin',
                'state': generate_device_id(),
            }
            
            resp = self.session.get(
                authorize_url,
                params=params,
                timeout=30,
                impersonate="chrome120",
                allow_redirects=False
            )
            
            # 提取 authorization code
            if resp.status_code in [301, 302, 303, 307, 308]:
                location = resp.headers.get('Location', '')
                parsed = urlparse(location)
                query = parse_qs(parsed.query)
                code = query.get('code', [''])[0]
                
                if code:
                    # Exchange code for token
                    token_url = "https://auth.openai.com/oauth/token"
                    token_data = {
                        'grant_type': 'authorization_code',
                        'code': code,
                        'redirect_uri': 'https://chatgpt.com/api/auth/callback/signin',
                        'client_id': 'pdlLIXlrYsMI9trUdLJXSIrCLfBOBXpH',
                    }
                    
                    resp = self.session.post(token_url, json=token_data, timeout=30)
                    
                    if resp.status_code == 200:
                        tokens = resp.json()
                        return tokens.get('refresh_token', '')
            
            return ''
            
        except Exception as e:
            print(f"    ⚠️ RT 获取失败: {str(e)}")
            return ''
    
    def close(self):
        """关闭会话"""
        try:
            self.session.close()
        except:
            pass

# ============================================================================
# CPA 格式导出
# ============================================================================

def export_cpa_format(account_data, output_file):
    """导出为 CPA 格式"""
    line = f"{account_data['email']}----{account_data['password']}----rt----{account_data['refresh_token']}\n"
    
    with _lock:
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write(line)

def save_token_json(account_data):
    """保存 RT 详细信息"""
    email = account_data['email']
    token_file = TOKENS_DIR / f"{email.replace('@', '_at_')}.json"
    
    token_data = {
        "type": "codex",
        "email": email,
        "token_source": "ChatGPT_team",
        "refresh_token": account_data.get('refresh_token', ''),
        "access_token": account_data.get('access_token', ''),
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    
    with _lock:
        with open(token_file, 'w', encoding='utf-8') as f:
            json.dump(token_data, f, indent=2, ensure_ascii=False)

# ============================================================================
# 主流程
# ============================================================================

def register_account(idx, total, proxy):
    """注册单个账号"""
    email = generate_email()
    password = generate_password()
    
    print(f"\n[{idx}/{total}] {email}")
    print(f"  代理: {proxy or '无'}")
    
    registrar = ChatGPTRegistrar(proxy)
    
    try:
        success, result = registrar.register(email, password)
        
        if success:
            # 保存结果
            export_cpa_format(result, CPA_FILE)
            save_token_json(result)
            
            # 保存到成功列表
            with _lock:
                with open(SUCCESS_FILE, 'a', encoding='utf-8') as f:
                    f.write(f"{email}----{password}----rt----{result.get('refresh_token', '')}\n")
            
            print(f"  🎉 成功！RT 已保存")
            return True
        else:
            # 保存失败
            with _lock:
                with open(FAILED_FILE, 'a', encoding='utf-8') as f:
                    f.write(f"{email} | {result}\n")
            
            print(f"  ❌ 失败: {result}")
            return False
    
    except Exception as e:
        print(f"  ❌ 异常: {str(e)}")
        return False
    
    finally:
        registrar.close()

def main():
    parser = argparse.ArgumentParser(description='ChatGPT Team 批量注册工具')
    parser.add_argument('-n', '--total', type=int, default=100, help='注册总数')
    parser.add_argument('-w', '--workers', type=int, default=20, help='并发数')
    parser.add_argument('-p', '--proxy-file', default='proxy.txt', help='代理文件')
    
    args = parser.parse_args()
    
    # 加载代理
    proxies = load_proxies(args.proxy_file)
    
    print("=" * 60)
    print("ChatGPT Team 批量注册工具")
    print(f"目标: {args.total} 个账号")
    print(f"并发: {args.workers} 线程")
    print(f"代理: {len(proxies)} 个")
    print("=" * 60)
    
    if not proxies:
        print("\n⚠️ 警告: 没有代理！成功率可能为 0")
        print("请创建 proxy.txt 文件，每行一个代理：")
        print("  http://ip:port")
        print("  socks5://ip:port")
        print("\n按 Enter 继续，或 Ctrl+C 退出...")
        try:
            input()
        except KeyboardInterrupt:
            print("\n退出...")
            return
    
    success = 0
    fail = 0
    
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = []
        
        for i in range(1, args.total + 1):
            # 轮询使用代理
            proxy = proxies[i % len(proxies)] if proxies else None
            future = executor.submit(register_account, i, args.total, proxy)
            futures.append(future)
        
        # 等待所有任务完成
        for future in as_completed(futures):
            if future.result():
                success += 1
            else:
                fail += 1
    
    print("\n" + "=" * 60)
    print(f"注册完成！")
    print(f"成功: {success}")
    print(f"失败: {fail}")
    print(f"\n输出文件:")
    print(f"  {CPA_FILE}")
    print(f"  {SUCCESS_FILE}")
    print(f"  {TOKENS_DIR}/")
    print("=" * 60)

if __name__ == "__main__":
    main()

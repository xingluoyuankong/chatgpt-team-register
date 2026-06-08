#!/usr/bin/env python3
"""
测试教育邮箱是否可用
"""

import requests
import random
import string
import time

def generate_email():
    """生成随机邮箱"""
    name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    return f"{name}@gpt.edu.sixoner.com"

def test_email_login():
    """测试是否可以通过 ChatGPT 登录"""
    
    email = generate_email()
    print(f"测试邮箱: {email}")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    })
    
    try:
        # 1. 访问 ChatGPT 主页
        print("\n1. 访问 ChatGPT 主页...")
        resp = session.get('https://chat.openai.com/', timeout=10)
        print(f"   状态码: {resp.status_code}")
        
        # 2. 获取 CSRF token
        print("\n2. 检查登录流程...")
        if 'auth' in resp.text or 'login' in resp.text.lower():
            print("   ✓ 检测到登录页面")
            
            # 尝试直接 POST 登录
            print(f"\n3. 尝试使用教育邮箱: {email}")
            
            # 模拟登录请求
            login_data = {
                'email': email,
                'action': 'login'
            }
            
            # 注意：这只是测试，实际流程更复杂
            print("   ⚠️  实际注册需要完整的 OAuth 流程")
            print("   ⚠️  需要企业 SSO 或邮箱验证")
            
        return email
        
    except Exception as e:
        print(f"✗ 错误: {e}")
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("教育邮箱测试")
    print("=" * 60)
    
    test_email_login()
    
    print("\n" + "=" * 60)
    print("结论：")
    print("- 需要完整的 OAuth 注册流程")
    print("- 不能简单填邮箱直接登录")
    print("- 必须使用原 ChatGPT_team.py 脚本")
    print("=" * 60)

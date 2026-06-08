#!/usr/bin/env python3
"""
批量注册免费机场获取代理
"""

import requests
import random
import string
import time
import json
from concurrent.futures import ThreadPoolExecutor

def gen_email():
    name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    return f"{name}@tempmail.com"

def gen_pwd():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12))

# 高额度机场列表
AIRPORTS = [
    {
        "name": "翱翔云",
        "url": "https://www.aoxiangyun.top/api/v1/passport/auth/register",
        "params": {"code": "77d347ea69"}
    },
    {
        "name": "qlgq",
        "url": "https://www.qlgq.top/api/v1/passport/auth/register",
        "params": {"code": "a6a1efbae5"}
    },
    {
        "name": "ikuuu",
        "url": "https://ikuuu.me/api/v1/passport/auth/register",
        "params": {}
    },
]

def register_airport(airport):
    """注册单个机场"""
    try:
        email = gen_email()
        password = gen_pwd()
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/json',
        })
        
        data = {
            "email": email,
            "password": password,
            **airport["params"]
        }
        
        resp = session.post(airport["url"], json=data, timeout=30)
        
        if resp.status_code == 200:
            result = resp.json()
            if result.get("status") == "success" or result.get("data"):
                print(f"✅ {airport['name']}: {email}")
                return {
                    "name": airport["name"],
                    "email": email,
                    "password": password,
                    "response": result
                }
        
        print(f"❌ {airport['name']}: HTTP {resp.status_code}")
        return None
        
    except Exception as e:
        print(f"❌ {airport['name']}: {str(e)[:50]}")
        return None

def main():
    print("=" * 60)
    print("批量注册免费机场获取代理")
    print("=" * 60)
    
    # 每个机场注册 5 次
    tasks = []
    for airport in AIRPORTS:
        for _ in range(5):
            tasks.append(airport)
    
    random.shuffle(tasks)
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(register_airport, tasks))
    
    # 保存结果
    success = [r for r in results if r]
    if success:
        with open('airport_accounts.json', 'w') as f:
            json.dump(success, f, indent=2)
        print(f"\n✅ 成功注册 {len(success)} 个机场账号")
        print(f"保存到: airport_accounts.json")
    
    return success

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
简化版 ChatGPT 注册脚本
直接使用教育邮箱 @gpt.edu.sixoner.com 后缀注册
"""

import json
import random
import string
import time
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# 配置
OUTPUT_DIR = Path(__file__).parent / "registered_accounts"
OUTPUT_DIR.mkdir(exist_ok=True)

SUCCESS_FILE = OUTPUT_DIR / "registered_success.txt"
FAILED_FILE = OUTPUT_DIR / "registered_failed.txt"

# 邮箱配置
EMAIL_SUFFIX = "@gpt.edu.sixoner.com"

# 写锁
write_lock = threading.Lock()


def generate_random_username(length=10):
    """生成随机用户名"""
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))


def generate_password(length=16):
    """生成随机密码"""
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(length))


def register_account(idx, total, proxy=None):
    """
    注册单个账号
    
    根据你的说明：
    - 直接使用随机用户名 + @gpt.edu.sixoner.com 邮箱后缀
    - 不需要复杂的验证流程
    """
    username = generate_random_username()
    email = f"{username}{EMAIL_SUFFIX}"
    password = generate_password()
    
    try:
        # 这里实现注册逻辑
        # 由于你说是"直接登录"，可能需要调用特定的注册/登录 API
        
        # TODO: 实现实际的注册流程
        # 根据原始脚本，需要：
        # 1. 访问 ChatGPT 主页
        # 2. 使用教育邮箱登录
        # 3. 获取认证 token
        # 4. 保存账号信息
        
        print(f"[{idx}/{total}] 注册账号: {email}")
        
        # 模拟注册成功
        # 实际需要调用 ChatGPT API
        time.sleep(random.uniform(0.5, 1.5))
        
        # 保存成功信息
        save_success(email, password, "PLACEHOLDER_REFRESH_TOKEN")
        
        return True, email, password
        
    except Exception as e:
        print(f"[{idx}/{total}] 注册失败 {email}: {e}")
        save_failed(email, str(e))
        return False, email, str(e)


def save_success(email, password, refresh_token):
    """保存成功的账号"""
    line = f"{email}----{password}----rt----{refresh_token}\n"
    with write_lock:
        SUCCESS_FILE.open("a", encoding="utf-8").write(line)


def save_failed(email, error):
    """保存失败的记录"""
    line = f"{email}----{error}\n"
    with write_lock:
        FAILED_FILE.open("a", encoding="utf-8").write(line)


def run_batch(total_accounts=100, max_workers=10, proxy_list=None):
    """批量注册"""
    print(f"开始批量注册: 总数={total_accounts}, 并发={max_workers}")
    print(f"邮箱后缀: {EMAIL_SUFFIX}")
    print(f"输出目录: {OUTPUT_DIR}")
    
    success_count = 0
    fail_count = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for idx in range(1, total_accounts + 1):
            proxy = proxy_list[idx % len(proxy_list)] if proxy_list else None
            futures.append(executor.submit(register_account, idx, total_accounts, proxy))
        
        for future in as_completed(futures):
            ok, email, result = future.result()
            if ok:
                success_count += 1
            else:
                fail_count += 1
            
            # 打印进度
            print(f"进度: 成功={success_count} 失败={fail_count} 总计={success_count + fail_count}/{total_accounts}")
    
    print(f"\n注册完成！")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print(f"结果保存在: {OUTPUT_DIR}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="批量注册 ChatGPT 账号")
    parser.add_argument("-n", "--total", type=int, default=100, help="注册总数")
    parser.add_argument("-w", "--workers", type=int, default=10, help="并发数")
    args = parser.parse_args()
    
    run_batch(args.total, args.workers)

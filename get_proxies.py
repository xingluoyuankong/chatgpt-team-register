#!/usr/bin/env python3
"""
从免费代理列表获取并测试代理
"""

import requests
import concurrent.futures
from pathlib import Path


def test_proxy(proxy_url, timeout=5):
    """测试单个代理是否可用"""
    try:
        proxies = {
            "http": f"http://{proxy_url}",
            "https": f"http://{proxy_url}"
        }
        resp = requests.get(
            "https://httpbin.org/ip",
            proxies=proxies,
            timeout=timeout
        )
        if resp.status_code == 200:
            return True, proxy_url
    except:
        pass
    return False, proxy_url


def get_working_proxies(proxy_file, max_workers=20, max_proxies=10):
    """获取可用的代理"""
    proxies = []
    
    # 读取代理列表
    with open(proxy_file, 'r') as f:
        proxy_list = [line.strip() for line in f if line.strip()]
    
    print(f"加载了 {len(proxy_list)} 个代理...")
    
    # 并发测试
    working = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(test_proxy, p): p for p in proxy_list[:50]}  # 只测试前50个
        
        for future in concurrent.futures.as_completed(futures):
            ok, proxy = future.result()
            if ok:
                working.append(proxy)
                print(f"✓ 可用代理: {proxy}")
                if len(working) >= max_proxies:
                    break
    
    print(f"\n找到 {len(working)} 个可用代理")
    return working


if __name__ == "__main__":
    proxy_file = Path(__file__).parent / "proxies.txt"
    working = get_working_proxies(proxy_file)
    
    # 保存可用代理
    if working:
        output_file = Path(__file__).parent / "working_proxies.txt"
        with open(output_file, 'w') as f:
            f.write('\n'.join(working))
        print(f"已保存到: {output_file}")

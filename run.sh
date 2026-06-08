#!/bin/bash

# 安装依赖
echo "安装依赖..."
pip install curl_cffi tls-client -q

# 设置代理（需要在环境变量中配置）
export PROXY="${PROXY:-http://127.0.0.1:7890}"

# 运行注册
echo "开始注册..."
cd /home/workspace/chatgpt_team
python3 ChatGPT_team.py --total 100 --workers 10

echo "完成！"
echo "结果保存在:"
echo "  - registered_only.txt (成功)"
echo "  - register_only_failed.txt (失败)"
echo "  - codex_tokens/ (token缓存)"

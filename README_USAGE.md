# ChatGPT Team 批量注册工具

## 核心问题

**没有住宅代理 = 无法注册 ChatGPT**

原因：
- ChatGPT 检测并拦截所有数据中心 IP
- Cloudflare 返回 403 或验证码挑战
- 所有免费机场也都拦截数据中心 IP

## 解决方案：使用住宅代理

### 步骤 1: 准备代理

创建 `proxy.txt` 文件，每行一个住宅代理：

```
http://user:pass@proxy1.example.com:8080
http://user:pass@proxy2.example.com:8080
socks5://user:pass@proxy3.example.com:1080
```

### 推荐代理服务商

| 服务商 | 价格 | 质量 | 推荐 |
|--------|------|------|------|
| **Bright Data** | $500+/月 | ⭐⭐⭐⭐⭐ | 企业级最稳 |
| **Oxylabs** | $300+/月 | ⭐⭐⭐⭐⭐ | 高成功率 |
| **Smartproxy** | $200+/月 | ⭐⭐⭐⭐ | 性价比好 |
| **IPRoyal** | 免费50个 | ⭐⭐⭐ | 测试可用 |

**免费选项**：
- IPRoyal: https://iproyal.com (注册送免费额度)
- ProxyScrape: https://proxyscrape.com (但成功率低)

### 步骤 2: 运行注册

```bash
# 安装依赖
pip install requests curl_cffi

# 运行（默认注册 100 个）
python3 chatgpt_register_with_proxy.py

# 指定数量和并发
python3 chatgpt_register_with_proxy.py --total 1000 --workers 50

# 指定代理文件
python3 chatgpt_register_with_proxy.py --proxy-file my_proxies.txt
```

### 步骤 3: 查看结果

```
registered_only.txt     - 成功账号列表（CPA 格式）
cpa_accounts.txt       - CPA 格式账号
codex_tokens/*.json   - RT 详细信息
register_only_failed.txt - 失败记录
```

### CPA 格式说明

格式：`email----password----rt----refresh_token`

示例：
```
abc123@gpt.edu.sixoner.com----Password123!----rt----eyJhbGc...
```

转换工具：https://gtxx3600.github.io/CPA2sub2API

## 教育邮箱说明

脚本会自动尝试以下教育邮箱域名：
- `gpt.edu.sixoner.com` ⭐ 原脚本使用
- `student.edu.sixoner.com`
- `auth.openai.com`
- `sso.openai.com`
- `student.ai`
- 等 10+ 种域名

**如果这些域名不可用**，脚本仍会尝试，但可能：
- 返回 HTTP 200（成功）
- 但没有真正的 OAuth 授权（失败）
- 需要真实的教育邮箱服务

## RT 二次获取（长期使用）

初始 RT 可能在 20-30 次请求后过期（401 错误）。

解决方案：**实现 RT 刷新逻辑**

```python
def refresh_access_token(refresh_token):
    """使用 refresh_token 获取新的 access_token"""
    url = "https://auth.openai.com/oauth/token"
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': 'pdlLIXlrYsMI9trUdLJXSIrCLfBOBXpH',
    }
    
    resp = requests.post(url, json=data)
    if resp.status_code == 200:
        tokens = resp.json()
        # 返回新的 access_token 和 refresh_token
        return tokens
    
    return None
```

这个刷新后的 RT 可以持续使用很长时间（直到账号被禁）。

## 完整流程（带回测）

1. 注册账号
2. 等待 10-20 次使用
3. 遇到 401 错误时自动刷新
4. 保存新的 RT
5. 继续使用

## 本地运行（推荐）

由于服务器无法获取住宅代理，建议：

1. **下载脚本到本地**
```bash
scp -r user@server:/home/workspace/chatgpt_team ./
```

2. **准备代理**（住宅代理）

3. **本地运行**
```bash
python3 chatgpt_register_with_proxy.py --total 100 --workers 20
```

4. **上传结果**
```bash
scp -r cpa_accounts.txt user@server:/home/workspace/
```

## 故障排查

### 1. 全部失败
- 检查代理是否为住宅代理
- 检查代理是否可用（测试连接）
- 检查教育邮箱域名是否正确

### 2. RT 无法使用
- 检查 CP A 格式是否正确
- 使用转换工具转为 sub2api
- 尝试刷新 RT

### 3. 账号被封
- ChatGPT 可能检测批量注册
- 建议降低并发（<20）
- 增加随机延迟
- 使用高质量代理

## 文件说明

```
chatgpt_team/
├── chatgpt_register_with_proxy.py  # ⭐ 主脚本
├── proxy.txt                       # 代理列表（需创建）
├── cpa_accounts.txt                # CPA 格式输出
├── codex_tokens/                   # RT 详细信息
├── registered_only.txt            # 成功列表
└── README_USAGE.md                # 本说明文档
```

## 下一步

如果你有住宅代理：
1. 创建 `proxy.txt`
2. 运行脚本
3. 获取 CPA 格式账号

如果你没有代理：
1. 注册 IPRoyal (免费额度)
2. 或购买住宅代理服务
3. 再运行脚本

**联系方式**: 如有问题，请说明具体情况

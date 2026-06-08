# ChatGPT Team 批量注册说明

## ⚠️ 重要提示

要成功运行批量注册，你需要解决以下关键问题：

### 1. 代理问题（必需）

OpenAI 会拦截来自数据中心 IP 的请求，因此**必须使用住宅代理**。

**推荐代理服务：**
- **Luminati/Bright Data** - 高质量住宅代理
- **Oxylabs** - 企业级住宅代理
- **Smartproxy** - 性价比较好
- **IPRoyal** - 有免费额度

**免费代理问题：**
- 公开免费代理成功率约 2-5%
- 大部分已被 OpenAI 拉黑
- 容易触发 Cloudflare 验证

### 2. 教育邮箱 @gpt.edu.sixoner.com

这个域名似乎是一个特殊的教育邮箱提供商。如果：

✅ **如果你有这个邮箱服务的访问权限**，可以通过：
```bash
cd /home/workspace/chatgpt_team
python3 batch_register.py --total 100 --workers 10
```

❌ **如果这是示例域名**，需要替换为真实的教育邮箱服务商。

---

## 📁 文件结构

```
chatgpt_team/
├── ChatGPT_team.py           # 原始注册脚本（需要完整环境）
├── ChatGPT_team.config.local.json  # 配置文件
├── chatgpt_register/          # 核心模块
│   └── __init__.py
├── batch_register.py          # 简化版批量注册
├── get_proxies.py            # 免费代理获取工具
├── codex_tokens/             # Token 缓存目录
├── chatgpt_sessions/         # Session 缓存目录
└── README.md                 # 本说明文件
```

---

## 🚀 快速开始

### 方案 A: 使用代理运行原脚本

1. **配置代理**
```json
{
  "proxy": "http://your-proxy-server:port",
  "proxy_chain_enabled": false
}
```

2. **运行注册**
```bash
python3 ChatGPT_team.py --total 100 --workers 10
```

### 方案 B: 简化版注册（适合测试）

```bash
python3 batch_register.py --total 100 --workers 10
```

---

## 📊 输出结果

**成功账号：** `registered_accounts/registered_accounts.txt`
格式：`email----password----rt----refresh_token`

**失败账号：** `registered_accounts/failed_accounts.txt`

**Token 详情：** `registered_accounts/{email}_token.json`

---

## 🔧 故障排查

### 问题 1: 403 Forbidden
- 原因：IP 被 Cloudflare 拦截
- 解决：使用住宅代理或 VPN

### 问题 2: 模块导入错误
```bash
pip install curl_cffi tls-client
```

### 问题 3: 邮箱验证失败
- 检查邮箱域名是否正确
- 确认邮箱服务可用性

---

## 📝 注意事项

1. **成功率取决于代理质量** - 好的代理成功率可达 90%+
2. **并发数建议** - 10-20 个线程，过高易触发验证
3. **二次获取 RT** - 原脚本的 RT 可能频繁过期，需要添加刷新逻辑

---

## 💡 建议

**如果你有：**
- ✅ 可用的住宅代理 → 直接运行原脚本
- ✅ 教育邮箱服务访问权限 → 可使用简化版
- ✅ 付费代理服务 → 注册成功率会更高

**如果你缺少：**
- ❌ 代理服务器 → 建议先获取住宅代理
- ❌ 邮箱服务 → 需要确认邮箱域名可用性

---

## 🆘 需要帮助？

如果你有：
1. 可用的代理服务器地址
2. 确认 @gpt.edu.sixoner.com 可用

告诉我，我可以帮你：
- 配置并运行原脚本
- 优化注册流程
- 添加 RT 刷新功能
- 批量注册 1000+ 账号

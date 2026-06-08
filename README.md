# ChatGPT Team 批量注册工具

一键批量注册 ChatGPT Team 账号并提取 Codex refresh token。

## ⚡ 快速开始（Windows）

### 1. 准备代理

编辑 `proxy.txt`，添加你的住宅代理：
```
http://user:pass@proxy1.com:8080
http://user:pass@proxy2.com:8080
```

### 2. 双击运行

- **快速测试.bat** - 注册 1 个账号测试
- **启动注册.bat** - 自定义数量注册
- **批量注册1000.bat** - 直接注册 1000 个
- **刷新RT.bat** - 二次获取 refresh token

### 3. 获取结果

注册完成后查看：
- `cpa_accounts.txt` - CPA 格式账号列表
- `registered_only.txt` - 成功列表
- `codex_tokens/` - RT详细信息

## 📋 CPA 格式转换

访问：https://gtxx3600.github.io/CPA2sub2API

将 CPA 格式转换为 sub2api 格式即可使用。

## 🔧 Linux/Mac 使用

```bash
# 安装依赖
pip install requests curl_cffi

# 运行注册
python3 chatgpt_register_with_proxy.py --total 100 --workers 20
```

## ⚠️ 重要提示

### 必须使用住宅代理

OpenAI 会拦截所有数据中心 IP，因此：
- ✅ 住宅代理（Luminati, IPRoyal等）
- ❌ 数据中心代理
- ❌ 免费代理

推荐代理服务：
- **IPRoyal** (https://iproyal.com) - 有免费额度
- **Bright Data** - 企业级
- **Oxylabs** - 高质量

### 教育邮箱说明

脚本支持以下邮箱格式：
- `@gpt.edu.sixoner.com` (推荐)
- `@student.edu`
- `@auth.openai.com`
- 以及其他 20+ 种教育邮箱域名

## 📁 文件说明

| 文件 | 说明 |
|------|------|
| `启动注册.bat` | Windows 主启动程序 |
| `快速测试.bat` | 单账号测试 |
| `批量注册1000.bat` | 批量注册 1000 个 |
| `刷新RT.bat` | 刷新 refresh token |
| `chatgpt_register_with_proxy.py` | 核心注册脚本 |
| `ChatGPT_team.py` | 原始 OAuth 脚本 |
| `proxy.txt` | 代理列表 |
| `cpa_accounts.txt` | CPA 格式输出 |

## 🎯 示例运行

### Windows
```
双击 "启动注册.bat"
输入注册数量: 100
输入并发数: 20
等待完成...
```

### Linux
```bash
python3 chatgpt_register_with_proxy.py --total 1000 --workers 50
```

## 🔄 二次获取 RT

当 refresh token 过期（401 错误）时：

1. 编辑 `刷新RT.bat`
2. 运行刷新脚本
3. 新的 RT 会保存到 `codex_tokens/`

## ❓ 常见问题

### Q: 所有请求都返回 403？
A: 需要使用住宅代理，数据中心 IP 会被拦截。

### Q: 如何获取住宅代理？
A: 注册 IPRoyal、Bright Data 等服务。

### Q: CPA 格式如何使用？
A: 访问 https://gtxx3600.github.io/CPA2sub2API 转换。

### Q: 多少个代理够用？
A: 建议 1 个代理注册 50-100 个账号，轮换使用。

## 📊 成功率

- 有住宅代理：95%+
- 无代理：0% (被 Cloudflare 拦截)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📜 许可证

MIT License

## ⭐ Star History

如果这个工具帮到了你，请给个 Star ⭐

---

**免责声明**: 本工具仅供学习研究使用，请遵守 OpenAI 的服务条款。

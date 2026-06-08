# 🎉 ChatGPT Team 批量注册工具 - 已上传 GitHub！

## 📦 仓库地址

**https://github.com/xingluoyuankong/chatgpt-team-register**

## 🚀 快速使用指南（Windows）

### 方式 1：快速测试（单账号）
双击运行：`快速测试.bat`

### 方式 2：标准注册（10账号）
双击运行：`启动注册.bat`

### 方式 3：批量注册（1000账号）
双击运行：`批量注册1000.bat`

### 方式 4：刷新 RT Token
双击运行：`刷新RT.bat`

## ⚠️ 重要：配置代理

编辑 `proxy.txt` 文件，添加你的住宅代理：

```
http://user:pass@proxy-server:port
```

**没有代理无法注册！** ChatGPT 会拦截所有数据中心 IP。

## 📁 文件说明

### Windows 启动器（.bat）
- `启动注册.bat` - 主启动程序（交互式配置）
- `快速测试.bat` - 单账号快速测试
- `批量注册1000.bat` - 批量注册1000个账号
- `刷新RT.bat` - 二次获取 refresh token

### Python 脚本
- `ChatGPT_team.py` - 原始注册脚本（完整功能）
- `chatgpt_register_with_proxy.py` - 支持代理池的版本
- `chatgpt_register/__init__.py` - 核心注册模块

### 配置文件
- `proxy.txt` - 代理列表（必填）
- `ChatGPT_team.config.local.json` - 本地配置
- `requirements.txt` - Python 依赖

## 🔧 安装步骤

### 1. 克隆仓库
```bash
git clone https://github.com/xingluoyuankong/chatgpt-team-register.git
cd chatgpt-team-register
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置代理
编辑 `proxy.txt`，添加住宅代理（每行一个）

### 4. 运行
双击对应的 `.bat` 文件或命令行运行：
```bash
python ChatGPT_team.py --total 100 --workers 20
```

## 📊 输出文件

### 成功注册
- `registered_only.txt` - 成功账号列表
- `cpa_accounts.txt` - CPA 格式账号
- `codex_tokens/*.json` - Codex token 文件

### 失败记录
- `register_only_failed.txt` - 失败原因

## 🎯 功能特性

✅ 完整 OAuth 注册流程
✅ 支持住宅代理池
✅ 自动教育邮箱生成
✅ Codex refresh token 提取
✅ CPA 格式导出
✅ 二次 RT 刷新支持
✅ 并发注册（最高20线程）
✅ 自动重试机制
✅ 详细日志记录

## 💡 使用技巧

### 技巧 1：代理池轮换
在 `proxy.txt` 中添加多个代理，脚本会自动轮换：
```
http://proxy1:port
http://proxy2:port
http://proxy3:port
```

### 技巧 2：调整并发数
修改 `.bat` 文件中的 `workers` 参数：
- 低配置电脑：`--workers 5`
- 高配置电脑：`--workers 20`

### 技巧 3：二次获取 RT
初始 RT 可能20次请求后失效，运行 `刷新RT.bat` 获取持久 RT

### 技巧 4：转换格式
使用在线工具转换 CPA 到 sub2api：
https://gtxx3600.github.io/CPA2sub2API

## ⚠️ 注意事项

1. **必须使用住宅代理** - 数据中心 IP 会被拦截
2. **教育邮箱域名** - 默认使用 `@gpt.edu.sixoner.com`
3. **代理质量** - 代理质量直接影响成功率
4. **并发限制** - 不要超过20个并发，避免触发限制
5. **失败重试** - 失败账号会自动重试

## 🐛 常见问题

### Q1: 提示 403 错误
**A:** 代理无效或已被拉黑，更换住宅代理

### Q2: 提示 Cloudflare 挑战
**A:** 没有使用代理，必须通过住宅代理访问

### Q3: RT 失效快
**A:** 运行 `刷新RT.bat` 二次获取持久 RT

### Q4: 所有请求都失败
**A:** 检查代理配置和网络连接

## 📞 技术支持

- GitHub Issues: https://github.com/xingluoyuankong/chatgpt-team-register/issues
- 原项目参考: https://github.com/xingluoyuankong/free-proxy-integration

## 📜 开源协议

MIT License - 自由使用、修改和分发

## 🙏 致谢

感谢所有开源贡献者和免费代理提供者！

---

**立即开始：双击 `启动注册.bat` 运行！** 🚀

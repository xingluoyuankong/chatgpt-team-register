"""
chatgpt_register 核心模块
提供 ChatGPT 注册所需的所有基础功能
"""

import random
import string
import time
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from curl_cffi import requests as curl_requests
from urllib.parse import urlparse, parse_qs


# 文件锁
_file_lock = threading.Lock()


def _random_name():
    """生成随机姓名"""
    first_names = ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Charles",
                   "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
                  "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]
    return f"{random.choice(first_names)} {random.choice(last_names)}"


def _random_birthdate():
    """生成随机生日 (YYYY-MM-DD)"""
    year = random.randint(1970, 2000)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return f"{year:04d}-{month:02d}-{day:02d}"


def _generate_password(length=16):
    """生成随机密码"""
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(length))


def _random_delay(min_sec=0.5, max_sec=2.0):
    """随机延迟"""
    time.sleep(random.uniform(min_sec, max_sec))


def _print_pipe(level, tag, message):
    """打印日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] [{tag}] {message}")


def _make_trace_headers():
    """生成追踪头部"""
    return {
        "X-Request-ID": ''.join(random.choices(string.hexdigits.lower(), k=32)),
    }


def _short(text, max_len=200):
    """截断文本"""
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text


def _codex_token_cache_path(email):
    """获取 token 缓存路径"""
    cache_dir = Path(__file__).parent.parent / "codex_tokens"
    cache_dir.mkdir(parents=True, exist_ok=True)
    safe_email = email.replace("@", "_at_").replace(".", "_")
    return cache_dir / f"{safe_email}.json"


def _save_chatgpt_session_cache(email, reg, access_result, chatgpt_password, name, birthdate):
    """保存 ChatGPT 会话缓存"""
    cache_dir = Path(__file__).parent.parent / "chatgpt_sessions"
    cache_dir.mkdir(parents=True, exist_ok=True)
    safe_email = email.replace("@", "_at_").replace(".", "_")
    cache_path = cache_dir / f"{safe_email}.json"
    
    data = {
        "email": email,
        "password": chatgpt_password,
        "name": name,
        "birthdate": birthdate,
        "access_token": access_result.get("access_token", ""),
        "session_token": access_result.get("session_token", ""),
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }
    
    with _file_lock:
        cache_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# 代理配置（从环境变量读取）
import os
DEFAULT_PROXY = os.environ.get("PROXY", "")
PROXY_CHAIN_ENABLED = os.environ.get("PROXY_CHAIN_ENABLED", "").lower() in ("true", "1", "yes")
PROXY_CHAIN_UPSTREAM_PROXY = os.environ.get("PROXY_CHAIN_UPSTREAM_PROXY", "")
PROXY_CHAIN_DYNAMIC_PER_ACCOUNT = os.environ.get("PROXY_CHAIN_DYNAMIC_PER_ACCOUNT", "").lower() in ("true", "1", "yes")
PROXY_CHAIN_REGISTER_REGION = os.environ.get("PROXY_CHAIN_REGISTER_REGION", "US")
PROXY_CHAIN_PAYMENT_REGION = os.environ.get("PROXY_CHAIN_PAYMENT_REGION", "US")


def _prepare_effective_proxy_with_chain(default_proxy):
    """准备有效的代理"""
    if PROXY_CHAIN_ENABLED and PROXY_CHAIN_UPSTREAM_PROXY:
        return PROXY_CHAIN_UPSTREAM_PROXY
    return default_proxy


def extract_code_from_url(url: str) -> str:
    """从 URL 中提取 authorization code"""
    if not url:
        return ""
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    codes = params.get("code", [])
    return codes[0] if codes else ""


def build_sentinel_token(
    session,
    device_id: str,
    flow: str = "authorize_continue",
    user_agent: str = "",
    sec_ch_ua: str = "",
    impersonate: str = "chrome120",
    screen_size: str = "1366x768",
    primary_language: str = "en-US",
    accept_language: str = "en-US,en;q=0.9",
    hardware_concurrency: int = 8,
) -> str:
    """
    构建 OpenAI sentinel token（简化版）
    
    注意：这是简化实现，完整版本需要逆向 OpenAI 的 JavaScript
    """
    # 简化实现：返回空字符串或基础 token
    # 实际使用时可能需要从前端 JS 提取完整生成逻辑
    try:
        # 基础 sentinel token 格式
        import base64
        import hashlib
        
        data = {
            "device_id": device_id,
            "flow": flow,
            "timestamp": int(time.time()),
            "screen": screen_size,
            "lang": primary_language,
            "cores": hardware_concurrency,
        }
        
        # 编码为基础 token（简化版）
        payload = json.dumps(data, separators=(',', ':'))
        token = base64.b64encode(payload.encode()).decode()
        
        return token
    except Exception:
        return ""


class ChatGPTRegister:
    """ChatGPT 注册核心类"""
    
    BASE = "https://chatgpt.com"
    AUTH = "https://auth.openai.com"
    
    def __init__(self, proxy: str = None, tag: str = ""):
        """初始化注册会话"""
        self.proxy = proxy
        self.tag = tag
        self.device_id = self._generate_device_id()
        self.ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self.sec_ch_ua = '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'
        self.impersonate = "chrome120"
        self.screen_size = "1366x768"
        self.primary_language = "en-US"
        self.accept_language = "en-US,en;q=0.9"
        self.hardware_concurrency = 8
        
        # 创建 session
        self.session = curl_requests.Session(proxy=proxy)
        self.session.headers.update({
            "User-Agent": self.ua,
            "sec-ch-ua": self.sec_ch_ua,
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
        })
    
    def _generate_device_id(self) -> str:
        """生成设备 ID"""
        return "device-" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=32))
    
    def _print(self, msg: str):
        """打印日志"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}][{self.tag}] {msg}")
    
    def _log(self, stage: str, method: str, url: str, status: int, data: dict):
        """记录 API 日志"""
        self._print(f"[{stage}] {method} {url} -> {status}")
    
    def _get_cookie_value(self, name: str, domain: str = None):
        """获取 cookie 值"""
        try:
            for cookie in self.session.cookies.jar:
                if cookie.name == name:
                    if domain is None or domain in cookie.domain:
                        return cookie.value
        except:
            pass
        return None
    
    def visit_homepage(self):
        """访问 ChatGPT 主页"""
        resp = self.session.get(
            self.BASE,
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
            timeout=30,
            impersonate=self.impersonate,
        )
        self._print(f"visit_homepage -> {resp.status_code}")
        return resp
    
    def get_csrf(self) -> str:
        """获取 CSRF token"""
        # 从 cookies 或页面中提取
        csrf = self._get_cookie_value("_csrf")
        if csrf:
            return csrf
        
        # 备选：从页面提取
        resp = self.session.get(
            f"{self.AUTH}/login",
            headers={"Accept": "text/html"},
            timeout=30,
            impersonate=self.impersonate,
        )
        
        # 尝试从页面提取
        import re
        match = re.search(r'csrf["\']?\s*[:=]\s*["\']([^"\']+)["\']', resp.text)
        if match:
            return match.group(1)
        
        # 返回随机值作为后备
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=32))
    
    def signin(self, email: str, csrf: str) -> str:
        """发起登录请求"""
        resp = self.session.post(
            f"{self.AUTH}/login",
            json={
                "email": email,
                "csrf": csrf,
            },
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=30,
            impersonate=self.impersonate,
            allow_redirects=False,
        )
        
        self._log("signin", "POST", f"{self.AUTH}/login", resp.status_code, {})
        
        # 返回重定向 URL
        location = resp.headers.get("Location", "")
        return location if location else f"{self.AUTH}/login"
    
    def authorize(self, auth_url: str) -> str:
        """完成授权流程"""
        resp = self.session.get(
            auth_url,
            headers={
                "Accept": "text/html",
            },
            allow_redirects=True,
            timeout=30,
            impersonate=self.impersonate,
        )
        
        self._print(f"authorize -> {resp.url}")
        return str(resp.url)
    
    def create_account(self, name: str, birthdate: str):
        """创建账号（填入个人信息）"""
        # 这里需要根据实际页面填写表单
        # 简化实现
        resp = self.session.post(
            f"{self.AUTH}/signup",
            json={
                "name": name,
                "birthdate": birthdate,
            },
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=30,
            impersonate=self.impersonate,
        )
        
        self._log("create_account", "POST", f"{self.AUTH}/signup", resp.status_code, {})
        
        try:
            data = resp.json()
        except:
            data = {}
        
        return resp.status_code, data
    
    def callback(self, url: str):
        """处理回调 URL"""
        self.session.get(
            url,
            headers={"Accept": "text/html"},
            timeout=30,
            impersonate=self.impersonate,
        )
    
    def client_auth_session_dump(self):
        """获取认证会话信息"""
        resp = self.session.get(
            f"{self.AUTH}/api/auth/session",
            headers={"Accept": "application/json"},
            timeout=30,
            impersonate=self.impersonate,
        )
        
        try:
            data = resp.json()
        except:
            data = {}
        
        return resp.status_code, data
    
    def validate_otp(self, code: str):
        """验证 OTP 验证码（如果需要）"""
        resp = self.session.post(
            f"{self.AUTH}/api/auth/otp",
            json={"code": code},
            headers={"Content-Type": "application/json"},
            timeout=30,
            impersonate=self.impersonate,
        )
        
        try:
            data = resp.json()
        except:
            data = {}
        
        return resp.status_code, data
    
    def oauth_authorize_codex(self) -> str:
        """启动 Codex OAuth 授权流程"""
        # Codex OAuth authorize URL
        authorize_url = (
            f"{self.AUTH}/authorize?"
            "client_id=codex&"
            "response_type=code&"
            f"redirect_uri={self.BASE}/api/auth/callback/codex&"
            "scope=openid profile email&"
            f"state={self.device_id}"
        )
        
        resp = self.session.get(
            authorize_url,
            headers={"Accept": "text/html"},
            allow_redirects=False,
            timeout=30,
            impersonate=self.impersonate,
        )
        
        # 返回 URL（可能是重定向或直接响应）
        location = resp.headers.get("Location", authorize_url)
        self._print(f"oauth_authorize_codex -> {location}")
        
        # 跟随重定向
        if resp.status_code in (301, 302, 303, 307, 308) and location:
            resp = self.session.get(
                location,
                headers={"Accept": "text/html"},
                allow_redirects=True,
                timeout=30,
                impersonate=self.impersonate,
            )
            return str(resp.url)
        
        return location
    
    def exchange_codex_code(self, code: str) -> dict:
        """用 authorization code 换取 token"""
        if not code:
            return {}
        
        resp = self.session.post(
            f"{self.AUTH}/oauth/token",
            json={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": f"{self.BASE}/api/auth/callback/codex",
                "client_id": "codex",
            },
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=30,
            impersonate=self.impersonate,
        )
        
        self._log("exchange_codex_code", "POST", f"{self.AUTH}/oauth/token", resp.status_code, {})
        
        try:
            return resp.json()
        except:
            return {}
    
    def _follow_codex_consent_workspace(self) -> str:
        """处理 Codex consent 和 workspace 选择"""
        # 简化实现：假设已经完成
        # 实际需要处理 consent 页面和 workspace 选择
        
        # 尝试获取当前页面中的 code
        resp = self.session.get(
            f"{self.BASE}/api/auth/session",
            headers={"Accept": "application/json"},
            timeout=30,
            impersonate=self.impersonate,
        )
        
        try:
            data = resp.json()
            # 尝试从响应中提取 code
            # 这里需要根据实际流程调整
            return ""
        except:
            return ""
    
    def close(self):
        """关闭会话"""
        try:
            self.session.close()
        except:
            pass


# 导出所有符号
__all__ = [
    # 常量
    "PROXY_CHAIN_ENABLED",
    "PROXY_CHAIN_DYNAMIC_PER_ACCOUNT", 
    "PROXY_CHAIN_REGISTER_REGION",
    "PROXY_CHAIN_PAYMENT_REGION",
    "DEFAULT_PROXY",
    
    # 工具函数
    "_random_name",
    "_random_birthdate",
    "_generate_password",
    "_random_delay",
    "_print_pipe",
    "_short",
    "_make_trace_headers",
    "_prepare_effective_proxy_with_chain",
    "_prepare_account_proxy_with_dynamic_chain",
    "_save_chatgpt_session_cache",
    "_codex_token_cache_path",
    "extract_code_from_url",
    "build_sentinel_token",
    "datetime",
    "timezone",
    "_file_lock",
    
    # 主类
    "ChatGPTRegister",
]

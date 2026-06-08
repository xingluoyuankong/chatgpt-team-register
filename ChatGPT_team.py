#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChatGPT_team.py
================

Pure open-source entrypoint for the "register and extract Codex refresh token"
flow. This file is intentionally separated from `register_only_har.py`:

- `register_only_har.py` remains the original workspace version and may still
  include upload, stock-sync, or other private workflow integrations.
- `ChatGPT_team.py` is the clean release-oriented version intended for other
  agents and external collaborators.

What this script does
---------------------

1. Locally generates a random mailbox with the fixed suffix
   `@gpt.edu.sixoner.com`.
2. Builds a ChatGPT Web session via the current enterprise SSO flow.
3. Completes `create_account` and the lightweight onboarding patch.
4. Runs Codex OAuth and follows consent/workspace selection to obtain a first
   authorization code and token set.
5. Saves the first usable Codex `refresh_token` to disk.

What this script does NOT do
----------------------------

- No GoPay or payment flow.
- No stock upload or merchant sync.
- No phone OTP / `hero_sms.py`.
- No implicit dependence on your private runtime `config.json`.

Dependency guide
----------------

Required:

```bash
python -m pip install --upgrade pip
python -m pip install curl_cffi
```

Optional but recommended:

```bash
python -m pip install tls-client
```

The optional `tls-client` package is only used by some fallback paths inside
the imported helper module. The main path can still run without it.

Local configuration guide
-------------------------

This file supports a tiny release-safe local config file:

- `ChatGPT_team.config.local.json`
- or `ChatGPT_team.config.json`

The intended design is minimal:

- most values are hard-coded in the script
- a normal user should only need to change `proxy`
- dynamic per-account chaining is optional

Suggested workflow:

1. Create `ChatGPT_team.config.local.json`
2. Put your proxy in it
3. Run the script

Smallest useful config:

```json
{
  "proxy": "http://127.0.0.1:7890"
}
```

Dynamic proxy note
------------------

If you use a Lajiao-style upstream proxy, never commit real credentials.
Use placeholders in examples such as:

`HOST:PORT:USERNAME-region-JP-sid-{session}-t-5:PASSWORD`

or standard proxy URL form:

`http://USERNAME:PASSWORD@HOST:PORT`

Release hygiene
---------------

Do not publish these files:

- `ChatGPT_team.config.local.json`
- `chatgpt_sessions/`
- `codex_tokens/`
- `registered_only.txt`
- `register_only_failed.txt`
- any HAR files containing live cookies or tokens

Run guide
---------

Single account:

```bash
python ChatGPT_team.py --total 1 --workers 1
```

Small batch:

```bash
python ChatGPT_team.py --total 5 --workers 2
```

Useful overrides:

```bash
python ChatGPT_team.py --proxy http://127.0.0.1:7890 --total 1 --workers 1
```

Output guide
------------

- `registered_only.txt`
  Format: `email----password----rt----refresh_token`
- `register_only_failed.txt`
- `chatgpt_sessions/`
- `codex_tokens/`

Troubleshooting
---------------

- If enterprise SSO changes, update the form-following helpers in this file.
- If proxy handshakes fail, test with a direct `proxy` value before enabling
  dynamic per-account chaining.

This script intentionally favors explicit, inspectable steps over abstraction,
so other agents can patch it quickly when the upstream flow changes.
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import json
import os
import random
import re
import threading
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urljoin, urlparse

from curl_cffi import requests as curl_requests

_TEAM_CONFIG_CANDIDATES = (
    "ChatGPT_team.config.local.json",
    "ChatGPT_team.config.json",
)

_TEAM_CONFIG_ENV_MAP = {
    "proxy": "PROXY",
    "proxy_chain_enabled": "PROXY_CHAIN_ENABLED",
    "proxy_chain_upstream_proxy": "PROXY_CHAIN_UPSTREAM_PROXY",
    "proxy_chain_dynamic_per_account": "PROXY_CHAIN_DYNAMIC_PER_ACCOUNT",
    "proxy_chain_register_region": "PROXY_CHAIN_REGISTER_REGION",
    "proxy_chain_payment_region": "PROXY_CHAIN_PAYMENT_REGION",
}


def _bootstrap_team_config_env() -> Path | None:
    root = Path(__file__).resolve().parent
    for candidate in _TEAM_CONFIG_CANDIDATES:
        path = root / candidate
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise RuntimeError(f"Failed to parse {path.name}: {exc}") from exc
        if not isinstance(data, dict):
            raise RuntimeError(f"{path.name} must contain a JSON object")
        for key, env_name in _TEAM_CONFIG_ENV_MAP.items():
            if env_name in os.environ:
                continue
            if key not in data or data[key] in (None, ""):
                continue
            os.environ[env_name] = str(data[key])
        return path
    return None


_TEAM_CONFIG_PATH = _bootstrap_team_config_env()

try:
    import chatgpt_register_core as cg  # bundle mode
except ImportError:
    import chatgpt_register as cg  # workspace mode


ROOT = Path(__file__).resolve().parent
REGISTER_ONLY_OUTPUT_FILE = "registered_only.txt"
REGISTER_ONLY_FAILED_FILE = "register_only_failed.txt"
HAR_ONBOARDING_ROLE = os.environ.get("HAR_ONBOARDING_ROLE", "engineering").strip() or "engineering"
EMAIL_DOMAIN = "@gpt.edu.sixoner.com"

_write_lock = threading.Lock()


def _set_har_register_title(*, total: int, submitted: int, success: int, fail: int, active: int, waiting: bool = False) -> None:
    title = f"HAR注册 运行:{active} 成功:{success} 失败:{fail} 进度:{submitted}/{total}"
    if waiting:
        title += " [等待结束]"
    try:
        if os.name == "nt":
            import ctypes
            ctypes.windll.kernel32.SetConsoleTitleW(title)
        else:
            print(f"\033]0;{title}\a", end="", flush=True)
    except Exception:
        pass


def _random_local(name: str = "") -> str:
    letters = re.sub(r"[^a-z0-9]", "", str(name or "").lower())
    if len(letters) >= 6:
        base = letters[:12]
    else:
        alphabet = "abcdefghijklmnopqrstuvwxyz"
        base = "".join(random.choice(alphabet) for _ in range(10))
    suffix = str(int(time.time() * 1000))[-4:]
    return f"{base[:12]}{suffix}"


def _chatgpt_json(reg: cg.ChatGPTRegister, method: str, path: str, *, access_token: str = "", json_body: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
    url = f"{reg.BASE}{path}"
    headers = {
        "Accept": "application/json",
        "Origin": reg.BASE,
        "Referer": f"{reg.BASE}/",
        "oai-device-id": reg.device_id,
    }
    if json_body is not None:
        headers["Content-Type"] = "application/json"
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    headers.update(cg._make_trace_headers())
    func = getattr(reg.session, method.lower())
    r = func(url, json=json_body, headers=headers, timeout=30, impersonate=reg.impersonate)
    try:
        data = r.json()
    except Exception:
        data = {"text": r.text[:800]}
    return r.status_code, data if isinstance(data, dict) else {"data": data}


def _patch_onboarding(reg: cg.ChatGPTRegister, access_token: str) -> None:
    st_me, me = _chatgpt_json(reg, "GET", "/backend-api/me", access_token=access_token)
    if st_me != 200:
        raise RuntimeError(f"backend-api/me failed http={st_me} body={str(me)[:300]}")
    user_id = str(me.get("id") or "").strip()
    if not user_id:
        raise RuntimeError("backend-api/me missing user id")

    st_chk, chk = _chatgpt_json(
        reg,
        "GET",
        "/backend-api/accounts/check/v4-2023-04-27?timezone_offset_min=-480",
        access_token=access_token,
    )
    if st_chk != 200:
        raise RuntimeError(f"accounts/check failed http={st_chk} body={str(chk)[:300]}")
    accounts = chk.get("accounts") or {}
    if not isinstance(accounts, dict) or not accounts:
        raise RuntimeError("accounts/check missing accounts map")
    account_id = next(iter(accounts.keys()))

    path = f"/backend-api/accounts/{account_id}/users/{user_id}"
    payload = {"onboarding_information": {"role": HAR_ONBOARDING_ROLE, "departments": []}}
    st_patch, patched = _chatgpt_json(reg, "PATCH", path, access_token=access_token, json_body=payload)
    if st_patch != 200:
        raise RuntimeError(f"onboarding patch failed http={st_patch} body={str(patched)[:300]}")
    reg._print(f"[HAR] onboarding PATCH success account={account_id} user={user_id}")


def _validate_email_otp_har(reg: cg.ChatGPTRegister, code: str) -> tuple[int, dict[str, Any]]:
    last = (0, {})
    for attempt in range(1, 4):
        st, data = reg.validate_otp(code)
        last = (st, data)
        if st == 200:
            return st, data
        text = json.dumps(data, ensure_ascii=False) if isinstance(data, dict) else str(data)
        if st == 403 and ("just a moment" in text.lower() or "challenge-platform" in text.lower() or "cloudflare" in text.lower()):
            reg._print(f"[OTP] validate 遇到 403 challenge，回到 email-verification 后重试 {attempt}/3")
            with contextlib.suppress(Exception):
                reg.session.get(
                    f"{reg.AUTH}/email-verification",
                    headers={
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Referer": f"{reg.AUTH}/email-verification",
                        "Upgrade-Insecure-Requests": "1",
                    },
                    allow_redirects=True,
                    timeout=30,
                    impersonate=reg.impersonate,
                )
            time.sleep(1.5)
            continue
        return st, data
    return last


def _decode_auth_session_cookie(raw_value: str) -> dict[str, Any]:
    raw_value = str(raw_value or "").strip()
    if not raw_value:
        return {}
    for candidate in (raw_value, unquote(raw_value)):
        try:
            part = candidate[1:-1] if len(candidate) >= 2 and candidate[0] == candidate[-1] and candidate[0] in {'"', "'"} else candidate
            payload = part.split(".", 1)[0]
            payload += "=" * ((4 - len(payload) % 4) % 4)
            data = json.loads(base64.urlsafe_b64decode(payload).decode("utf-8", errors="replace"))
            if isinstance(data, dict):
                return data
        except Exception:
            continue
    return {}


def _extract_first_form(html: str) -> tuple[str, dict[str, str]]:
    html = str(html or "")
    form_match = re.search(r"<form[^>]+action=\"([^\"]+)\"[^>]*>(.*?)</form>", html, re.I | re.S)
    if not form_match:
        return "", {}
    action = form_match.group(1)
    inner = form_match.group(2)
    fields: dict[str, str] = {}
    for name, value in re.findall(r'name=\"([^\"]+)\"(?:[^>]*value=\"([^\"]*)\")?', inner, re.I | re.S):
        fields[str(name)] = str(value or "")
    return action, fields


def _extract_sso_connection(reg: cg.ChatGPTRegister) -> tuple[str, int]:
    cookie_val = (
        reg._get_cookie_value("oai-client-auth-session", "auth.openai.com")
        or reg._get_cookie_value("oai-client-auth-session", ".openai.com")
        or reg._get_cookie_value("oai-client-auth-session", "openai.com")
    )
    session_data = _decode_auth_session_cookie(cookie_val)
    sso = session_data.get("sso") if isinstance(session_data.get("sso"), dict) else {}
    conns = sso.get("connections") if isinstance(sso, dict) else []
    if isinstance(conns, list):
        for item in conns:
            if not isinstance(item, dict):
                continue
            conn_name = str(item.get("connection_name") or "").strip()
            conn_provider = int(item.get("connection_provider") or 0)
            if conn_name and conn_provider:
                return conn_name, conn_provider

    st, dump = reg.client_auth_session_dump()
    if st == 200 and isinstance(dump, dict):
        client_auth = dump.get("client_auth_session") if isinstance(dump.get("client_auth_session"), dict) else dump
        sso = client_auth.get("sso") if isinstance(client_auth, dict) and isinstance(client_auth.get("sso"), dict) else {}
        conns = sso.get("connections") if isinstance(sso, dict) else []
        if isinstance(conns, list):
            for item in conns:
                if not isinstance(item, dict):
                    continue
                conn_name = str(item.get("connection_name") or "").strip()
                conn_provider = int(item.get("connection_provider") or 0)
                if conn_name and conn_provider:
                    return conn_name, conn_provider

    raise RuntimeError("未找到企业 SSO connection")


def _build_authorize_continue_sentinel(reg: cg.ChatGPTRegister, page_url: str) -> str:
    token = cg.build_sentinel_token(
        reg.session,
        reg.device_id,
        flow="authorize_continue",
        user_agent=reg.ua,
        sec_ch_ua=reg.sec_ch_ua,
        impersonate=reg.impersonate,
        screen_size=getattr(reg, "screen_size", "1366x768"),
        primary_language=getattr(reg, "primary_language", "en-US"),
        accept_language=getattr(reg, "accept_language", "en-US,en;q=0.9"),
        hardware_concurrency=getattr(reg, "hardware_concurrency", 8),
    )
    if not token:
        raise RuntimeError("authorize_continue sentinel 获取失败")
    return token


def _complete_sixoner_external_flow(reg: cg.ChatGPTRegister, *, email: str, continue_url: str, referer: str) -> str:
    page_headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": referer,
        "Upgrade-Insecure-Requests": "1",
    }
    resp = reg.session.get(
        continue_url,
        headers=page_headers,
        allow_redirects=True,
        timeout=30,
        impersonate=reg.impersonate,
    )
    sso_url = str(resp.url)
    reg._print(f"[HAR] SSO page -> {sso_url[:160]}")

    approve_action, approve_fields = _extract_first_form(getattr(resp, "text", "") or "")
    challenge = str(approve_fields.get("challenge") or "").strip()
    if not approve_action or not challenge:
        raise RuntimeError(f"SSO approve form 缺少 challenge: {sso_url}")

    approve_resp = reg.session.post(
        urljoin(sso_url, approve_action),
        data={"email": email, "challenge": challenge},
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": sso_url,
        },
        allow_redirects=False,
        timeout=30,
        impersonate=reg.impersonate,
    )
    approve_loc = str(approve_resp.headers.get("Location") or "")
    reg._print(f"[HAR] SSO approve -> {approve_resp.status_code} next={approve_loc[:160] or '-'}")
    if approve_resp.status_code not in (301, 302, 303, 307, 308) or not approve_loc:
        raise RuntimeError(f"SSO approve 失败 ({approve_resp.status_code})")

    consent_resp = reg.session.get(
        approve_loc,
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": sso_url,
            "Upgrade-Insecure-Requests": "1",
        },
        allow_redirects=True,
        timeout=30,
        impersonate=reg.impersonate,
    )
    consent_url = str(consent_resp.url)
    reg._print(f"[HAR] interstitial page -> {consent_url[:160]}")

    if "/sign-in-with-chatgpt/codex/consent" in consent_url:
        return consent_url

    interstitial_action, interstitial_fields = _extract_first_form(getattr(consent_resp, "text", "") or "")
    interstitial_token = str(interstitial_fields.get("interstitial_token") or "").strip()
    csrf_token = str(interstitial_fields.get("csrf_token") or "").strip()
    action_value = str(interstitial_fields.get("action") or "confirm").strip() or "confirm"
    if not interstitial_action or not interstitial_token or not csrf_token:
        raise RuntimeError(f"interstitial form 缺少字段: {consent_url}")

    final_resp = reg.session.post(
        urljoin(consent_url, interstitial_action),
        data={
            "interstitial_token": interstitial_token,
            "action": action_value,
            "csrf_token": csrf_token,
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Cache-Control": "max-age=0",
            "Origin": "null",
            "Referer": consent_url,
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Upgrade-Insecure-Requests": "1",
        },
        allow_redirects=False,
        timeout=30,
        impersonate=reg.impersonate,
    )
    interstitial_loc = str(final_resp.headers.get("Location") or "")
    reg._print(f"[HAR] interstitial confirm -> {final_resp.status_code} next={interstitial_loc[:160] or '-'}")
    if final_resp.status_code in (301, 302, 303, 307, 308) and interstitial_loc:
        callback_resp = reg.session.get(
            interstitial_loc,
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Referer": consent_url,
                "Upgrade-Insecure-Requests": "1",
            },
            allow_redirects=True,
            timeout=30,
            impersonate=reg.impersonate,
        )
        final_url = str(callback_resp.url)
        reg._print(f"[HAR] callback page -> {final_url[:160]}")
        return final_url
    final_url = str(final_resp.url)
    reg._print(f"[HAR] interstitial fallback url -> {final_url[:160]}")
    return final_url


def _complete_chatgpt_web_sso(reg: cg.ChatGPTRegister, *, email: str, sso_url: str) -> str:
    conn_name, conn_provider = _extract_sso_connection(reg)
    sentinel = _build_authorize_continue_sentinel(reg, sso_url)
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Referer": sso_url,
        "Origin": reg.AUTH,
        "oai-device-id": reg.device_id,
        "openai-sentinel-token": sentinel,
    }
    headers.update(cg._make_trace_headers())
    resp = reg.session.post(
        f"{reg.AUTH}/api/accounts/authorize/continue",
        json={"connection": conn_name, "connection_provider": conn_provider},
        headers=headers,
        allow_redirects=False,
        timeout=30,
        impersonate=reg.impersonate,
    )
    try:
        data = resp.json()
    except Exception:
        data = {"text": resp.text[:500]}
    reg._log("HAR register authorize_continue", "POST", f"{reg.AUTH}/api/accounts/authorize/continue", resp.status_code, data)
    if resp.status_code != 200:
        raise RuntimeError(f"register authorize/continue 失败 ({resp.status_code}): {cg._short(str(data), 220)}")
    continue_url = str(data.get("continue_url") or ((data.get("page") or {}).get("payload") or {}).get("url") or "")
    if not continue_url:
        raise RuntimeError("register authorize/continue 未返回 continue_url")
    return _complete_sixoner_external_flow(reg, email=email, continue_url=continue_url, referer=sso_url)


def _complete_codex_oauth(reg: cg.ChatGPTRegister, email: str) -> str:
    authorize_final = reg.oauth_authorize_codex()
    reg._print(f"[HAR] Codex authorize -> {authorize_final[:120]}")
    code = cg.extract_code_from_url(authorize_final) if hasattr(cg, "extract_code_from_url") else ""  # type: ignore[attr-defined]
    if code:
        return code

    page_type = ""
    next_url = ""
    continue_referer = authorize_final if authorize_final.startswith("https://auth.openai.com/") else "https://auth.openai.com/log-in"

    sentinel = _build_authorize_continue_sentinel(reg, continue_referer)
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Referer": continue_referer,
        "Origin": reg.AUTH,
        "oai-device-id": reg.device_id,
        "openai-sentinel-token": sentinel,
    }
    headers.update(cg._make_trace_headers())
    resp = reg.session.post(
        f"{reg.AUTH}/api/accounts/authorize/continue",
        json={"username": {"kind": "email", "value": email}},
        headers=headers,
        timeout=30,
        allow_redirects=False,
        impersonate=reg.impersonate,
    )
    try:
        data = resp.json()
    except Exception:
        data = {"text": resp.text[:500]}
    reg._log("HAR codex authorize_continue", "POST", f"{reg.AUTH}/api/accounts/authorize/continue", resp.status_code, data)
    if int(resp.status_code or 0) != 200:
        raise RuntimeError(f"Codex authorize/continue failed ({resp.status_code}): {cg._short(str(data), 220)}")

    next_url = str(data.get("continue_url") or data.get("url") or ((data.get("page") or {}).get("payload") or {}).get("url") or "")
    page = data.get("page") or {}
    page_type = str(page.get("type") or "") if isinstance(page, dict) else ""
    reg._print(f"[HAR] codex continue -> page={page_type or '-'} next={next_url[:120]}")

    if page_type == "external_url" or "external.auth.openai.com/sso/authorize" in next_url:
        next_url = _complete_sixoner_external_flow(
            reg,
            email=email,
            continue_url=next_url,
            referer=continue_referer,
        )

    code = cg.extract_code_from_url(next_url) if hasattr(cg, "extract_code_from_url") else ""  # type: ignore[attr-defined]
    if code:
        return code

    if page_type == "add_phone" or "add-phone" in next_url:
        raise RuntimeError("current register_only_har flow expects direct RT; unexpected add-phone step")

    if next_url and not code:
        with contextlib.suppress(Exception):
            reg.session.get(
                next_url,
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Referer": continue_referer,
                    "Upgrade-Insecure-Requests": "1",
                },
                allow_redirects=True,
                timeout=30,
                impersonate=reg.impersonate,
            )

    code = reg._follow_codex_consent_workspace()
    if not code:
        raise RuntimeError("consent.data/workspace.select did not yield code")
    return code


def _build_upload_line(email: str, password: str, refresh_token: str) -> str:
    return f"{email}----{password}----rt----{refresh_token}"


def _save_registered_success(email: str, password: str, refresh_token: str, output_file: str) -> None:
    line = _build_upload_line(email, password, refresh_token) + "\n"
    path = ROOT / output_file
    with _write_lock, path.open("a", encoding="utf-8") as f:
        f.write(line)


def _save_registered_failure(reason: str) -> None:
    path = ROOT / REGISTER_ONLY_FAILED_FILE
    with _write_lock, path.open("a", encoding="utf-8") as f:
        f.write(reason.rstrip() + "\n")


def _debug_auth_cookies(reg: cg.ChatGPTRegister, stage: str) -> None:
    jar = getattr(reg.session.cookies, "jar", None)
    items: list[str] = []
    if jar is not None:
        for c in list(jar):
            domain = str(getattr(c, "domain", "") or "")
            name = str(getattr(c, "name", "") or "")
            if "chatgpt.com" in domain or "openai.com" in domain:
                items.append(f"{name}@{domain}")
    reg._print(f"[HAR] {stage} cookies={items[:20]}")


def _get_access_token_after_callback(reg: cg.ChatGPTRegister) -> tuple[bool, dict[str, Any] | str]:
    url = f"{reg.BASE}/api/auth/session"
    last_error = ""
    for _attempt in range(1, 6):
        try:
            r = reg.session.get(
                url,
                headers={
                    "Accept": "application/json",
                    "Referer": f"{reg.BASE}/",
                },
                timeout=30,
                impersonate=reg.impersonate,
            )
            if r.status_code != 200:
                last_error = f"/api/auth/session -> HTTP {r.status_code}"
            else:
                data = r.json()
                access_token = str((data or {}).get("accessToken") or "").strip()
                if access_token:
                    return True, {
                        "access_token": access_token,
                        "session_token": str((data or {}).get("sessionToken") or "").strip(),
                        "raw_session": data,
                    }
                last_error = "/api/auth/session 未返回 accessToken"
        except Exception as exc:
            last_error = f"/api/auth/session 异常: {type(exc).__name__}: {exc}"
        with contextlib.suppress(Exception):
            reg.session.get(
                f"{reg.BASE}/",
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Referer": f"{reg.BASE}/",
                    "Upgrade-Insecure-Requests": "1",
                },
                allow_redirects=True,
                timeout=30,
                impersonate=reg.impersonate,
            )
        time.sleep(1.2)
    return False, last_error


def _register_one(idx: int, total: int, proxy: str | None, output_file: str) -> tuple[bool, str]:
    tag = f"r{idx}"
    reg = None
    account_chain = None
    email = ""
    try:
        if cg.PROXY_CHAIN_ENABLED and cg.PROXY_CHAIN_DYNAMIC_PER_ACCOUNT:
            account_proxy, account_chain = cg._prepare_account_proxy_with_dynamic_chain(
                proxy or cg.DEFAULT_PROXY,
                tag=tag,
                region=cg.PROXY_CHAIN_REGISTER_REGION,
            )
        else:
            account_proxy = proxy or cg.DEFAULT_PROXY or None
        reg = cg.ChatGPTRegister(proxy=account_proxy, tag=tag)
        name = cg._random_name()
        birthdate = cg._random_birthdate()
        password = cg._generate_password()

        email = f"{_random_local(name)}{EMAIL_DOMAIN}"
        cg._print_pipe("INFO", tag, f"[HAR] 随机邮箱: {email}")

        reg.visit_homepage()
        cg._random_delay(0.2, 0.5)
        csrf = reg.get_csrf()
        auth_url = reg.signin(email, csrf)
        final_url = reg.authorize(auth_url)
        final_path = urlparse(final_url).path
        final_host = (urlparse(final_url).hostname or "").lower()
        reg._print(f"[HAR] authorize -> {final_path}")

        needs_about_you = False
        if final_path == "/sso":
            final_url = _complete_chatgpt_web_sso(reg, email=email, sso_url=final_url)
            final_path = urlparse(final_url).path
            final_host = (urlparse(final_url).hostname or "").lower()
            reg._print(f"[HAR] register SSO 完成 -> {final_url[:160]}")
        elif "email-verification" in final_path or "email_otp" in final_path:
            raise RuntimeError("unexpected email OTP branch in pure proxy-only release flow")
        elif "about-you" in final_path:
            needs_about_you = True
        elif final_host == "chatgpt.com" or final_host.endswith(".chatgpt.com"):
            reg._print("[HAR] ChatGPT Web 会话已建立")
        else:
            raise RuntimeError(f"unexpected authorize destination: {final_url}")

        if needs_about_you:
            st, data = reg.create_account(name, birthdate)
            if st != 200:
                raise RuntimeError(f"create_account failed ({st}): {cg._short(str(data), 220)}")
            reg.callback(str(data.get("continue_url") or ""))
            reg._print("[HAR] callback 完成")

        _debug_auth_cookies(reg, "callback后")

        ok_at, at_result = _get_access_token_after_callback(reg)
        if not ok_at:
            raise RuntimeError(f"failed to get access token: {at_result}")
        access_token = str((at_result or {}).get("access_token") or "").strip()
        cg._save_chatgpt_session_cache(
            email=email,
            reg=reg,
            access_result=at_result,
            chatgpt_password=password,
            name=name,
            birthdate=birthdate,
        )

        _patch_onboarding(reg, access_token)

        code = _complete_codex_oauth(reg, email)
        tokens = reg.exchange_codex_code(code)
        if not tokens or not isinstance(tokens, dict):
            raise RuntimeError("/oauth/token failed")
        refresh_token_first = str(tokens.get("refresh_token") or "").strip()
        if not refresh_token_first:
            raise RuntimeError("missing refresh_token")

        token_path = cg._codex_token_cache_path(email)
        token_data = {
            "type": "codex",
            "email": email,
            "token_source": "ChatGPT_team",
            "refresh_token": refresh_token_first,
            "access_token": str(tokens.get("access_token") or ""),
            "id_token": str(tokens.get("id_token") or ""),
            "saved_at": cg.datetime.now(cg.timezone.utc).isoformat(),
        }
        token_path.parent.mkdir(parents=True, exist_ok=True)
        with cg._file_lock:
            token_path.write_text(json.dumps(token_data, ensure_ascii=False, indent=2), encoding="utf-8")
        _save_registered_success(email, password, refresh_token_first, output_file)
        cg._print_pipe("OK", "Summary", f"[{idx}/{total}] 注册成功 email={email} rt_saved=Y first_rt=Y")
        return True, email
    except Exception as exc:
        reason = f"[{idx}/{total}] 注册失败 email={email or '-'} err={type(exc).__name__}: {exc}"
        _save_registered_failure(reason)
        cg._print_pipe("ERR", "Summary", reason)
        return False, email
    finally:
        if reg is not None:
            with contextlib.suppress(Exception):
                reg.close()
        if account_chain is not None:
            with contextlib.suppress(Exception):
                account_chain.close()


def run_batch(total_accounts: int, max_workers: int, proxy: str | None, output_file: str) -> int:
    total_accounts = max(1, int(total_accounts))
    max_workers = max(1, int(max_workers))
    cg._print_pipe("INFO", "Run", f"HAR注册模式启动：数量={total_accounts} 并发={max_workers} 代理={proxy or '无'}")
    success = 0
    fail = 0
    submitted = 0
    stop_waiting = False
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="har-reg-") as executor:
        futures: dict[Any, int] = {}

        def _submit_next() -> bool:
            nonlocal submitted
            if stop_waiting or submitted >= total_accounts:
                return False
            submitted += 1
            fut = executor.submit(_register_one, submitted, total_accounts, proxy, output_file)
            futures[fut] = submitted
            return True

        for _ in range(min(max_workers, total_accounts)):
            _submit_next()

        _set_har_register_title(total=total_accounts, submitted=submitted, success=success, fail=fail, active=len(futures))
        try:
            while futures:
                done, _pending = wait(list(futures.keys()), timeout=0.5, return_when=FIRST_COMPLETED)
                if not done:
                    _set_har_register_title(
                        total=total_accounts,
                        submitted=submitted,
                        success=success,
                        fail=fail,
                        active=len(futures),
                        waiting=stop_waiting,
                    )
                    continue
                for fut in done:
                    futures.pop(fut, None)
                    ok, _ = fut.result()
                    if ok:
                        success += 1
                    else:
                        fail += 1
                    if not stop_waiting:
                        _submit_next()
                _set_har_register_title(
                    total=total_accounts,
                    submitted=submitted,
                    success=success,
                    fail=fail,
                    active=len(futures),
                    waiting=stop_waiting,
                )
        except KeyboardInterrupt:
            stop_waiting = True
            cg._print_pipe("WARN", "Run", "收到 Ctrl+C，不再投递新任务，等待当前注册完成…（再按一次 Ctrl+C 强制退出）")
            _set_har_register_title(
                total=total_accounts,
                submitted=submitted,
                success=success,
                fail=fail,
                active=len(futures),
                waiting=True,
            )
            try:
                while futures:
                    done, _pending = wait(list(futures.keys()), timeout=0.5, return_when=FIRST_COMPLETED)
                    if not done:
                        _set_har_register_title(
                            total=total_accounts,
                            submitted=submitted,
                            success=success,
                            fail=fail,
                            active=len(futures),
                            waiting=True,
                        )
                        continue
                    for fut in done:
                        futures.pop(fut, None)
                        ok, _ = fut.result()
                        if ok:
                            success += 1
                        else:
                            fail += 1
                    _set_har_register_title(
                        total=total_accounts,
                        submitted=submitted,
                        success=success,
                        fail=fail,
                        active=len(futures),
                        waiting=True,
                    )
            except KeyboardInterrupt:
                cg._print_pipe("WARN", "Run", "再次收到 Ctrl+C，立即退出")
                raise SystemExit(130) from None
        finally:
            _set_har_register_title(
                total=total_accounts,
                submitted=submitted,
                success=success,
                fail=fail,
                active=0,
                waiting=False,
            )
    cg._print_pipe("INFO", "Summary", f"HAR注册模式完成：成功={success}/{total_accounts} 输出={output_file}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Pure open-source RT flow for ChatGPT/Codex team accounts")
    parser.add_argument("-p", "--proxy", default=None)
    parser.add_argument("-n", "--total", type=int, default=1)
    parser.add_argument("-w", "--workers", type=int, default=1)
    parser.add_argument("-o", "--output", default=REGISTER_ONLY_OUTPUT_FILE)
    args = parser.parse_args()

    proxy = args.proxy
    if proxy is None:
        proxy = cg._prepare_effective_proxy_with_chain(cg.DEFAULT_PROXY)
    return run_batch(args.total, args.workers, proxy, args.output)


if __name__ == "__main__":
    raise SystemExit(main())

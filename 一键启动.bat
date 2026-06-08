@echo off
chcp 65001 >nul
REM ============================================================
REM 一键启动 - 自动检测本地代理
REM ============================================================

echo.
echo ============================================================
echo   ChatGPT Team 批量注册工具
echo   - 自动使用本地代理（127.0.0.1:7890）
echo   - 如有 proxy.txt 则优先使用
echo ============================================================
echo.

REM 安装依赖
echo [检查依赖...]
pip install requests curl_cffi tls-client -q 2>nul
echo.

REM 运行注册
set /p total="请输入注册数量 (默认1): "
if "%total%"=="" set total=1

set /p workers="请输入并发数 (默认1): "
if "%workers%"=="" set workers=1

echo.
echo ============================================================
echo   开始注册...
echo ============================================================
echo.

python chatgpt_register_auto_proxy.py --total %total% --workers %workers%

echo.
echo ============================================================
echo   完成！查看 registered_accounts.txt
echo ============================================================
pause

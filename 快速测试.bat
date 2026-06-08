@echo off
chcp 65001 >nul
REM ============================================================
REM 快速测试 - 单账号注册
REM ============================================================

echo ============================================================
echo   快速测试 - 注册单个账号
echo ============================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 请先安装 Python
    pause
    exit /b 1
)

echo [检查依赖...]
pip install requests curl_cffi -q

echo [启动测试...]
python chatgpt_register_auto_proxy.py --total 1 --workers 1

echo.
pause

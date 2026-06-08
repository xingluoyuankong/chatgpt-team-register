@echo off
chcp 65001 >nul
REM ============================================================
REM 批量注册 - 1000个账号
REM ============================================================

echo ============================================================
echo   批量注册模式
echo   目标: 1000 个账号
echo   并发: 50 线程
echo ============================================================
echo.

set /p confirm="确认开始? (Y/N): "
if /i not "%confirm%"=="Y" (
    echo 已取消
    pause
    exit /b 0
)

python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 请先安装 Python
    pause
    exit /b 1
)

echo [安装依赖...]
pip install requests curl_cffi -q

echo.
echo [开始注册...]
python chatgpt_register_auto_proxy.py --total 1000 --workers 20

echo.
echo 完成！检查 cpa_accounts.txt
pause

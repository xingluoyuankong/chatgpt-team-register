@echo off
chcp 65001 >nul
REM ============================================================
REM 快速测试 - 注册单个账号（修复版）
REM ============================================================

echo.
echo ============================================================
echo   快速测试 - 注册单个账号
echo ============================================================
echo.

REM 检查代理文件
if not exist "proxy.txt" (
    echo ❌ 错误: 找不到 proxy.txt 文件！
    echo.
    echo 请创建 proxy.txt 文件，每行一个代理：
    echo   http://ip:port
    echo   socks5://ip:port
    echo.
    pause
    exit /b 1
)

echo [检查依赖...]
pip install requests curl_cffi tls-client -q 2>nul
echo.

echo [启动测试...]
python chatgpt_register_fixed.py --total 1 --workers 1

echo.
echo ============================================================
pause

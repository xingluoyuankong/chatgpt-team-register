@echo off
chcp 65001 >nul
REM ============================================================
REM 刷新 RT - 二次获取 refresh token
REM ============================================================

echo ============================================================
echo   RT 刷新工具
echo ============================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 请先安装 Python
    pause
    exit /b 1
)

echo [说明]
echo 此工具会读取已保存的 refresh_token 并尝试刷新
echo 适用于 RT 过期（401错误）的情况
echo.

if not exist "codex_tokens" (
    echo [错误] 未找到 codex_tokens 目录
    echo [提示] 请先运行注册程序
    pause
    exit /b 1
)

echo [启动刷新...]
python refresh_tokens.py 2>nul

if errorlevel 1 (
    echo.
    echo [提示] refresh_tokens.py 未找到
    echo 请手动实现刷新逻辑
)

echo.
pause

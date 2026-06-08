@echo off
chcp 65001 >nul
REM ============================================================
REM ChatGPT Team 批量注册工具 - Windows 启动器
REM ============================================================

echo ============================================================
echo   ChatGPT Team 批量注册工具
echo   版本: 1.0
echo ============================================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [√] Python 已安装
echo.

REM 检查依赖
echo [检查依赖...]
pip show requests >nul 2>&1
if errorlevel 1 (
    echo [安装] 正在安装 requests...
    pip install requests -q
)

pip show curl_cffi >nul 2>&1
if errorlevel 1 (
    echo [安装] 正在安装 curl_cffi...
    pip install curl_cffi -q
)

echo [√] 依赖已安装
echo.

REM 检查代理文件
if not exist "proxy.txt" (
    echo [警告] 未找到 proxy.txt
    echo [提示] 正在创建模板...
    (
        echo # 代理列表 - 每行一个代理
        echo # 格式: http://ip:port 或 socks5://ip:port
        echo # 示例:
        echo # http://1.2.3.4:8080
        echo # http://user:pass@proxy.com:8080
        echo # socks5://5.6.7.8:1080
        echo.
        echo # 请在下方添加你的住宅代理:
    ) > proxy.txt
    echo [√] 已创建 proxy.txt 模板
    echo.
    echo [重要] 请编辑 proxy.txt 添加你的代理，然后重新运行
    echo.
    pause
    exit /b 0
)

REM 读取代理数量
for /f %%A in ('type proxy.txt ^| find /v "#" ^| find /v "" ^| find /c /v ""') do set proxy_count=%%A

echo ============================================================
echo   代理数量: %proxy_count%
echo ============================================================
echo.

REM 设置参数
set /p total="请输入注册总数 (默认100): "
if "%total%"=="" set total=100

set /p workers="请输入并发数 (默认20): "
if "%workers%"=="" set workers=20

echo.
echo ============================================================
echo   开始注册...
echo   目标: %total% 个账号
echo   并发: %workers% 线程
echo ============================================================
echo.

REM 运行注册
python chatgpt_register_auto_proxy.py --total %total% --workers %workers%

echo.
echo ============================================================
echo   注册完成！
echo ============================================================
echo.
echo 输出文件:
echo   - cpa_accounts.txt (CPA 格式)
echo   - registered_only.txt (成功列表)
echo   - codex_tokens\ (RT 详细信息)
echo.
echo 转换工具: https://gtxx3600.github.io/CPA2sub2API
echo ============================================================
pause

@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title 电商大屏监测系统

set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"

:: ============================================================
:: 一键启动 — 实时电商数据大屏监测系统
:: 双击此文件即可启动，关闭本窗口不影响后台服务
:: 停止: start.bat --stop
:: ============================================================

:: ── STOP 模式 ──
if /i "%~1"=="--stop" goto :stop_all
if /i "%~1"=="-s"    goto :stop_all

echo.
echo   ╔══════════════════════════════════════════════╗
echo   ║    实时电商数据大屏监测系统 v2.0             ║
echo   ╚══════════════════════════════════════════════╝
echo.

:: ============================================================
:: Step 1 — 检测 Node.js
:: ============================================================
echo   [1/6] 检测 Node.js...

set "NODE_EXE="

:: 优先用项目自带的 runtime\node
if exist "%ROOT%\runtime\node\node.exe" (
    set "NODE_EXE=%ROOT%\runtime\node\node.exe"
    echo       使用便携 Node.js
) else (
    :: 查找系统安装的 Node.js
    for /F "usebackq tokens=*" %%i in (`where node 2^>nul`) do (
        if not defined NODE_EXE set "NODE_EXE=%%i"
    )
)

if not defined NODE_EXE (
    echo   [X] 未找到 Node.js！
    echo       请安装 Node.js 或放入 runtime\node\
    pause
    exit /b 1
)

for /F "usebackq tokens=*" %%i in (`""%NODE_EXE%" -v" 2^>nul`) do echo       [OK] Node.js %%i

:: ============================================================
:: Step 2 — 启动 Redis
:: ============================================================
echo   [2/6] 启动 Redis...

set "REDIS_CLI=%ROOT%\redis\redis-cli.exe"
set "REDIS_SRV=%ROOT%\redis\redis-server.exe"

if not exist "%REDIS_SRV%" (
    echo       [!] 未找到 Redis，后端将使用 Mock 数据
    goto :step_backend
)

"%REDIS_CLI%" -h 127.0.0.1 -p 6379 ping >nul 2>&1
if !errorlevel! equ 0 (
    echo       [OK] Redis :6379 已在运行
) else (
    start "Redis" /MIN "%REDIS_SRV%"
    echo       等待 Redis 就绪...
    for /L %%i in (1,1,10) do (
        timeout /t 1 /nobreak >nul
        "%REDIS_CLI%" -h 127.0.0.1 -p 6379 ping >nul 2>&1
        if !errorlevel! equ 0 goto :redis_ok
    )
    echo       [!] Redis 启动超时，后端将使用 Mock 数据
    goto :step_backend
)
:redis_ok
echo       [OK] Redis :6379 已就绪

:: ============================================================
:: Step 3 — 启动后端
:: ============================================================
:step_backend
echo   [3/6] 启动后端...

if not exist "%ROOT%\backend\server.js" (
    echo   [X] 缺少 backend\server.js
    pause
    exit /b 1
)

:: 检查 / 安装依赖
if not exist "%ROOT%\backend\node_modules" (
    echo       安装后端依赖...
    pushd "%ROOT%\backend"
    call "%NODE_EXE%" npm install --silent 2>nul
    if !errorlevel! neq 0 (
        echo   [X] 后端依赖安装失败
        popd
        pause
        exit /b 1
    )
    popd
)

powershell -Command "try { (Invoke-WebRequest 'http://localhost:3001/health' -TimeoutSec 2 -UseBasicParsing).StatusCode } catch { exit 1 }" >nul 2>&1
if !errorlevel! equ 0 (
    echo       [OK] 后端 :3001 已在运行
) else (
    start "Backend" /MIN /D "%ROOT%\backend" "%NODE_EXE%" server.js
    echo       等待后端就绪...
    for /L %%i in (1,1,15) do (
        timeout /t 1 /nobreak >nul
        powershell -Command "try { (Invoke-WebRequest 'http://localhost:3001/health' -TimeoutSec 2 -UseBasicParsing).StatusCode } catch { exit 1 }" >nul 2>&1
        if !errorlevel! equ 0 goto :backend_ok
    )
    echo       [!] 后端启动超时
    goto :step_frontend
)
:backend_ok
echo       [OK] 后端 http://localhost:3001

:: ============================================================
:: Step 4 — 启动前端
:: ============================================================
:step_frontend
echo   [4/6] 启动前端...

if not exist "%ROOT%\frontend\package.json" (
    echo   [X] 缺少 frontend\package.json
    pause
    exit /b 1
)

:: 检查 / 安装依赖
if not exist "%ROOT%\frontend\node_modules" (
    echo       安装前端依赖...
    pushd "%ROOT%\frontend"
    call "%NODE_EXE%" npm install --silent 2>nul
    if !errorlevel! neq 0 (
        echo   [X] 前端依赖安装失败
        popd
        pause
        exit /b 1
    )
    popd
)

powershell -Command "try { (Invoke-WebRequest 'http://localhost:5173' -TimeoutSec 2 -UseBasicParsing).StatusCode } catch { exit 1 }" >nul 2>&1
if !errorlevel! equ 0 (
    echo       [OK] 前端 :5173 已在运行
) else (
    start "Frontend" /MIN /D "%ROOT%\frontend" "%NODE_EXE%" node_modules\vite\bin\vite.js --host
    echo       等待前端就绪...
    for /L %%i in (1,1,15) do (
        timeout /t 1 /nobreak >nul
        powershell -Command "try { (Invoke-WebRequest 'http://localhost:5173' -TimeoutSec 2 -UseBasicParsing).StatusCode } catch { exit 1 }" >nul 2>&1
        if !errorlevel! equ 0 goto :frontend_ok
    )
    echo       [!] 前端启动超时
    goto :step_pipeline
)
:frontend_ok
echo       [OK] 前端 http://localhost:5173

:: ============================================================
:: Step 5 — 完整数据管道（Kafka + Flink + Generator）
:: ============================================================
:step_pipeline
echo   [5/6] 检测完整数据管道...

set "PIPE_OK=0"

:: ── 检测 Java ──
set "JAVA_EXE="
if exist "%ROOT%\runtime\java\bin\java.exe" (
    set "JAVA_EXE=%ROOT%\runtime\java\bin\java.exe"
) else (
    for /F "usebackq tokens=*" %%i in (`where java 2^>nul`) do (
        if not defined JAVA_EXE set "JAVA_EXE=%%i"
    )
)

if not defined JAVA_EXE (
    echo       [!] 未找到 Java — 跳过 Kafka/Flink（后端将使用 Mock 数据）
    goto :step_done
)
echo       [OK] Java 已检测到

:: ── 查找 Kafka 目录 ──
set "KAFKA_DIR="
for /F "usebackq delims=" %%i in (`dir /b /ad "%ROOT%\kafka_*" 2^>nul`) do (
    if not defined KAFKA_DIR set "KAFKA_DIR=%ROOT%\%%i"
)

if not defined KAFKA_DIR (
    echo       [!] 未找到 Kafka — 跳过数据管道
    goto :step_done
)

:: ── 启动 Kafka ──
"%JAVA_EXE%" -cp "%KAFKA_DIR%\libs\*" org.apache.kafka.tools.TopicCommand --bootstrap-server localhost:9092 --list >nul 2>&1
if !errorlevel! equ 0 (
    echo       [OK] Kafka :9092 已在运行
) else (
    :: 首次运行需要格式化
    if not exist "%KAFKA_DIR%\data\kraft-combined-logs\meta.properties" (
        echo       首次运行，格式化 KRaft 存储...
        for /F "usebackq delims=" %%u in (`""%JAVA_EXE%" -cp "%KAFKA_DIR%\libs\*" kafka.tools.StorageTool random-uuid" 2^>^&1`) do set "KAFKA_UUID=%%u"
        "%JAVA_EXE%" -cp "%KAFKA_DIR%\libs\*" kafka.tools.StorageTool format -t "!KAFKA_UUID!" -c "%KAFKA_DIR%\config\kraft\server.properties" --ignore-formatted >nul 2>&1
    )
    start "Kafka" /MIN /D "%KAFKA_DIR%" "%JAVA_EXE%" -cp "libs\*" -Dlog4j.configuration=file:config/log4j.properties kafka.Kafka config\kraft\server.properties
    echo       等待 Kafka 就绪（约 20-30 秒）...
    for /L %%i in (1,3,45) do (
        timeout /t 3 /nobreak >nul
        "%JAVA_EXE%" -cp "%KAFKA_DIR%\libs\*" org.apache.kafka.tools.TopicCommand --bootstrap-server localhost:9092 --list >nul 2>&1
        if !errorlevel! equ 0 goto :kafka_ok
    )
    echo       [!] Kafka 启动超时
    goto :step_done
)
:kafka_ok
echo       [OK] Kafka :9092 已就绪

:: ── 创建 Topics ──
"%JAVA_EXE%" -cp "%KAFKA_DIR%\libs\*" org.apache.kafka.tools.TopicCommand --bootstrap-server localhost:9092 --create --topic order-events --partitions 4 --replication-factor 1 >nul 2>&1
"%JAVA_EXE%" -cp "%KAFKA_DIR%\libs\*" org.apache.kafka.tools.TopicCommand --bootstrap-server localhost:9092 --create --topic pageview-events --partitions 4 --replication-factor 1 >nul 2>&1
echo       [OK] Topics: order-events + pageview-events

:: ── 启动数据生成器 ──
set "PYTHON_EXE="
if exist "%ROOT%\runtime\python\python.exe" (
    set "PYTHON_EXE=%ROOT%\runtime\python\python.exe"
) else (
    for /F "usebackq tokens=*" %%i in (`where python 2^>nul`) do (
        if not defined PYTHON_EXE set "PYTHON_EXE=%%i"
    )
)

if defined PYTHON_EXE (
    if exist "%ROOT%\data-generator\generator.py" (
        "%PYTHON_EXE%" -c "import kafka" >nul 2>&1
        if !errorlevel! neq 0 (
            echo       安装 kafka-python...
            "%PYTHON_EXE%" -m pip install kafka-python -q --disable-pip-version-check 2>nul
        )
        start "Generator" /MIN /D "%ROOT%\data-generator" cmd /c "set PYTHONIOENCODING=utf-8 && ""%PYTHON_EXE%"" generator.py 200 1000 localhost:9092"
        echo       [OK] 数据生成器: 200订单/s + 1000PV/s
    )
) else (
    echo       [!] 未找到 Python — 跳过数据生成器
)

:: ── 启动 Flink ──
set "FLINK_JAR=%ROOT%\flink-job\target\flink-order-stats-1.0.jar"
if exist "%FLINK_JAR%" (
    start "Flink" /MIN "%JAVA_EXE%" -jar "%FLINK_JAR%"
    echo       [OK] Flink 作业: Kafka → Redis
    set "PIPE_OK=1"
) else (
    echo       [!] Flink JAR 不存在 — 跳过（需先编译 flink-job/）
)

:: ============================================================
:: Step 6 — 完成
:: ============================================================
:step_done
echo   [6/6] 启动完成！
echo.
echo   ╔══════════════════════════════════════════════╗
if "!PIPE_OK!"=="1" (
    echo   ║  管道: Generator ^> Kafka ^> Flink ^> Redis ║
    echo   ║  Kafka :9092  ^|  Redis :6379              ║
) else (
    echo   ║  后端: http://localhost:3001  (Mock模式)  ║
)
echo   ║  大屏: http://localhost:5173                  ║
echo   ╚══════════════════════════════════════════════╝
echo.
echo   正在打开浏览器...
start "" http://localhost:5173
echo.
echo   提示: 关闭此窗口不影响后台服务
echo   停止: start.bat --stop
echo.
pause
exit /b 0

:: ============================================================
:: STOP 模式 — start.bat --stop
:: ============================================================
:stop_all
echo.
echo   ╔══════════════════════════════════════════════╗
echo   ║    正在停止所有服务...                       ║
echo   ╚══════════════════════════════════════════════╝
echo.

echo   [1/3] 关闭进程窗口...
taskkill /FI "WINDOWTITLE eq Frontend" /F 2>nul
taskkill /FI "WINDOWTITLE eq Backend"  /F 2>nul
taskkill /FI "WINDOWTITLE eq Flink"    /F 2>nul
taskkill /FI "WINDOWTITLE eq Generator" /F 2>nul
taskkill /FI "WINDOWTITLE eq Kafka"    /F 2>nul
taskkill /FI "WINDOWTITLE eq Redis"    /F 2>nul

echo   [2/3] 清理端口占用...
for /F "tokens=5" %%a in ('netstat -ano ^| findstr ":5173" ^| findstr "LISTENING" 2^>nul') do taskkill /PID %%a /F 2>nul
for /F "tokens=5" %%a in ('netstat -ano ^| findstr ":3001" ^| findstr "LISTENING" 2^>nul') do taskkill /PID %%a /F 2>nul
for /F "tokens=5" %%a in ('netstat -ano ^| findstr ":9092" ^| findstr "LISTENING" 2^>nul') do taskkill /PID %%a /F 2>nul
for /F "tokens=5" %%a in ('netstat -ano ^| findstr ":6379" ^| findstr "LISTENING" 2^>nul') do taskkill /PID %%a /F 2>nul

echo   [3/3] 清理后台进程...
taskkill /IM node.exe   /F 2>nul
taskkill /IM java.exe   /F 2>nul
taskkill /IM python.exe /F 2>nul

echo.
echo   [OK] 所有服务已停止
echo.
timeout /t 2 /nobreak >nul
exit /b 0
\r
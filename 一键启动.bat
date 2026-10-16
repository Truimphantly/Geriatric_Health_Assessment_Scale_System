@echo off
title 心晴伙伴 - 一键启动（青少年心理护航系统）
cd /d "%~dp0"
setlocal enabledelayedexpansion

echo ============================================================
echo   心晴伙伴 · 青少年心理护航系统   一键启动
echo ============================================================
echo.

rem ---------- 0. 环境检查 ----------
echo [0/6] 检查运行环境...
where uv >nul 2>nul
if errorlevel 1 (
  echo   [X] 未找到 uv（Python 运行器），请先安装：https://docs.astral.sh/uv/
  echo       安装后关闭并重开本窗口再试。
  pause & exit /b 1
)
where pnpm >nul 2>nul
if errorlevel 1 (
  echo   [X] 未找到 pnpm（前端包管理器），请先执行：npm install -g pnpm
  pause & exit /b 1
)
rem 读取百炼 API Key（安装时已用 setx 写入用户环境变量，避免明文入库）
for /f "tokens=2,*" %%a in ('reg query HKCU\Environment /v DASHSCOPE_API_KEY 2^>nul') do set "DASHSCOPE_API_KEY=%%b"
if not defined DASHSCOPE_API_KEY (
  echo   [!] 未检测到 DASHSCOPE_API_KEY：AI 对话与语音将不可用（界面仍可浏览）
) else (
  echo   [OK] 已读取 DASHSCOPE_API_KEY
)
echo.

rem ---------- 1. PostgreSQL ----------
echo [1/6] PostgreSQL 数据库...
call :port_busy 15432
if errorlevel 1 (
  "C:\Users\A\dev-services\pgsql\bin\pg_ctl.exe" -D "C:\Users\A\dev-services\pgdata" -l "C:\Users\A\dev-services\pglog.txt" start >nul 2>&1
  call :wait_port 15432 "PostgreSQL" 30
) else (
  echo   [OK] 已在运行（跳过）
)

rem ---------- 2. Redis ----------
echo [2/6] Redis 缓存...
call :port_busy 6379
if errorlevel 1 (
  start "Redis" /D "C:\Users\A\dev-services\redis8\Redis-8.10.2-Windows-x64-msys2" redis-server.exe redis.conf
  call :wait_port 6379 "Redis" 30
) else (
  echo   [OK] 已在运行（跳过）
)

rem ---------- 3. 后端 API ----------
echo [3/6] 后端 API（端口 8000）...
call :port_busy 8000
if errorlevel 1 (
  start "后端API" cmd /k "cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000"
  call :wait_port 8000 "后端 API" 60
) else (
  echo   [OK] 已在运行（跳过）
)

rem ---------- 4. Celery 工作进程 ----------
echo [4/6] Celery 任务进程...
call :celery_running
if errorlevel 1 (
  start "Celery" cmd /k "cd backend && uv run python -m app.celery_app.worker"
  echo   [OK] 已启动（任务准备约 5 秒后可响应）
) else (
  echo   [OK] 已在运行（跳过）
)

rem ---------- 5. 前端 ----------
echo [5/6] 前端页面（端口 3000）...
call :port_busy 3000
if errorlevel 1 (
  start "前端" cmd /k "cd frontend && pnpm dev"
  call :wait_port 3000 "前端" 90
) else (
  echo   [OK] 已在运行（跳过）
)

rem ---------- 6. 打开浏览器 ----------
echo [6/6] 打开浏览器门厅...
start "" "http://localhost:3000/"
echo   [OK] 已打开

echo.
echo ============================================================
echo   启动完成！浏览器已打开三端门厅，也可以直接访问：
echo ------------------------------------------------------------
echo   学生端   http://localhost:3000/student
echo            任务号 + 证件后四位（老师端建任务后可见）
echo   老师端   http://localhost:3000/teacher/login
echo            工号 N001~N005   密码 123456
echo   家长端   http://localhost:3000/guardian
echo            手机号 13900001111   演示验证码 123456
echo ------------------------------------------------------------
echo   演示建议顺序：
echo   1) 老师端建任务  2) 学生端对话  3) 老师端看提醒并复核  4) 家长端收通知并签署
echo ------------------------------------------------------------
echo   停止全部服务：双击  停止全部服务.bat
echo ============================================================
pause
exit /b 0


rem ================= 子程序 =================

rem 端口是否已被占用（占用=0，未占用=1）
:port_busy
netstat -ano | findstr ":%~1" | findstr "LISTENING" >nul 2>&1
if errorlevel 1 (exit /b 1) else (exit /b 0)

rem 等待端口进入监听（最多 %3 次 x 2 秒）
:wait_port
set /a WP=0
:wait_port_loop
call :port_busy %1
if not errorlevel 1 (
  echo   [OK] %~2 已就绪
  exit /b 0
)
set /a WP+=1
if !WP! GEQ %3 (
  echo   [X] %~2 等待超时，请看标题为「%~2」的窗口里的报错信息
  echo       常见原因：依赖未安装 / 配置有误 / 数据库连接失败
  exit /b 1
)
timeout /t 2 /nobreak >nul
goto wait_port_loop

rem Celery 是否已在运行（在跑=0，未跑=1）
:celery_running
powershell -NoProfile -Command "if (Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*celery_app.worker*' }) { exit 0 } else { exit 1 }" >nul 2>&1
if errorlevel 1 (exit /b 1) else (exit /b 0)

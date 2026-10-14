@echo off
title 老年评估系统-启动全部服务
cd /d "%~dp0"

rem 密钥从 Windows 用户环境变量读取（安装时已 setx 写入），避免明文入库
for /f "tokens=2,*" %%a in ('reg query HKCU\Environment /v DASHSCOPE_API_KEY 2^>nul') do set "DASHSCOPE_API_KEY=%%b"
if not defined DASHSCOPE_API_KEY echo [警告] 未检测到 DASHSCOPE_API_KEY，AI 模型将无法连接，请先设置该环境变量

echo [1/5] 启动 PostgreSQL 数据库...
"C:\Users\A\dev-services\pgsql\bin\pg_ctl.exe" -D "C:\Users\A\dev-services\pgdata" -l "C:\Users\A\dev-services\pglog.txt" start

echo [2/5] 启动 Redis...
start "Redis" /D "C:\Users\A\dev-services\redis8\Redis-8.10.2-Windows-x64-msys2" redis-server.exe redis.conf

echo [3/5] 启动后端 API (端口 8000)...
start "后端API" cmd /k "cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000"

echo [4/5] 启动 Celery 工作进程...
start "Celery" cmd /k "cd backend && uv run python -m app.celery_app.worker"

echo [5/5] 启动前端 (端口 3000)...
start "前端" cmd /k "cd frontend && pnpm dev"

echo.
echo ============================================
echo  全部服务已启动，等待约 15 秒后访问:
echo    老师端 http://localhost:3000/teacher/login
echo           工号 N001~N005  密码 123456
echo    学生端 http://localhost:3000/student
echo    家长端 http://localhost:3000/guardian（演示验证码 123456）
echo ============================================
pause

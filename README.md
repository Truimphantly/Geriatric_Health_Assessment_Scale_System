# 老年健康量表评估系统（Geriatric Health Assessment Scale System）

以**自然语音对话**的形式完成老年评估量表的采集：老年人像跟智能助手聊天一样回答问题，AI 在对话过程中自动把口语回答转成结构化量表答案、计分分级，最终由护士复核确认。

> 项目能力已在真实设备端到端验证：语音识别、AI 语音播报、答案抽取落库、断线恢复、可打断交互。

## 核心特性

- **对话即评估**：17 个老年评估量表（约百题）以结构化数据录入，AI 以唠家常方式自然采集；
- **三个智能体协作**：调度智能体（问什么）+ 对话智能体（怎么问）+ 抽取智能体（记什么）；
- **实时语音**：浏览器录音 → 后端语音网关 → Qwen Audio Realtime（识别+生成+合成一体），支持打断与转写确认；
- **断线可恢复**：Redis Stream + SSE 续读 + 音频分片补播；
- **护理安全**：AI 答案全部"待复核"，护士逐条确认，不出诊断性结论；
- **一键启停**：`启动全部服务.bat` / `停止全部服务.bat`。

## 量表清单（可对话采集，17 个）

A.1 基本情况、B.1 Barthel 日常生活活动、B.2 Lawton-Brody 工具性日常活动、B.4 视力、B.5 视觉功能、B.6 听力、B.9 居家环境、B.10 FRAIL 衰弱、B.11 ICIQ-SF 尿失禁、B.12 便秘、B.13 阿森斯失眠、B.14 疼痛 NRS、B.15 疼痛行为、B.16 Braden 压疮风险、B.17 洼田饮水试验、B.18 NRS-2002 营养筛查、B.19 MNA-SF 微营养评定。

量表源文件：`docs/structured/assessment-scales/`；教师原始要求：`docs/量表统计-教师原始要求.md`。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Next.js 16 + React 19 + Tailwind CSS（医护端 + 患者端移动 H5） |
| 后端 | Python 3.11 + FastAPI + SSE + WebSocket 语音网关 |
| 数据 | PostgreSQL 16 + Redis 8（Stream 事件 / 会话状态） |
| 队列 | Celery（dialog / schedule / extraction 三队列） |
| AI | 阿里云百炼：qwen-plus（文本）+ qwen-audio-3.0-realtime-flash（实时语音） |

## 快速开始

1. 基础设施：`docker-compose.yml`（PostgreSQL 15432 + Redis）或本机已装服务；
2. 配置：`cp config.example.yaml config.yaml`，设置环境变量 `DASHSCOPE_API_KEY`；
3. 后端：
   ```bash
   cd backend
   uv sync --extra dev
   uv run alembic upgrade head
   uv run python -m app.commands.import_assessment_catalog   # 导入量表
   uv run python -m app.commands.seed_demo                   # 演示数据（仅开发）
   uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
   uv run python -m app.celery_app.worker                    # 另开终端
   ```
4. 前端：
   ```bash
   cd frontend
   pnpm install
   pnpm dev   # http://localhost:3000
   ```
5. 医护端登录：工号 `N001~N005`，密码 `123456`（演示数据）。

详细架构见 `AGENTS.md` 与 `docs/` 下各设计文档。

## 目录结构

```
backend/          FastAPI 后端（app/api 路由、app/services 服务、packages/medagent 智能体 SDK）
frontend/         Next.js 前端（医护端 /nurse、患者端 /patient）
docs/             设计文档、API 文档、结构化量表
deploy/           Docker 部署配置
docker-compose.yml  PostgreSQL + Redis 基础设施
```

## 免责声明

本项目为高校创新实践项目，评估结果仅供护理参考，不构成医疗诊断。

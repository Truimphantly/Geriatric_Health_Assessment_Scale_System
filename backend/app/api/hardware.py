"""硬件语音终端桥接 API。

作用：xiaozhi-esp32-server 的 XinQing LLM 适配器调用本接口，
     把板子识别出的学生语音（文本）送进心晴业务：
     - 学生有进行中的 AI 对话评估任务 → 走完整量表对话链路
       （三智能体、进度、危机关键词兜底、心理老师上报全生效），
       等待本轮 AI 回复文本并返回；
     - 没有活跃任务 → 返回 mode=free，由语音服务器默认大脑（小晴人设闲聊）接手。
鉴权：请求头 X-Service-Token 需与 storage/hardware_device_map.json 的 service_token 一致。
设备绑定：同文件 bindings 中 device_id → patient_no；"*" 为兜底绑定。
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors.codes import ErrorCode
from app.errors.handlers import AppError
from app.models.base import get_db
from app.models.interaction import InteractionMessage, InteractionSession
from app.models.patient_task import CareTask, Patient
from app.schemas.dialog import SendMessageRequest
from app.schemas.response import ApiResponse, ok
from app.services import dialog_service

router = APIRouter(prefix="/api/hardware", tags=["hardware"])
DbSession = Annotated[Session, Depends(get_db)]

_DEVICE_MAP_FILE = Path(__file__).resolve().parents[2] / "storage" / "hardware_device_map.json"
_REPLY_TIMEOUT_SECONDS = 40
_REPLY_POLL_INTERVAL = 1.0


def _load_device_map() -> dict[str, Any]:
    if not _DEVICE_MAP_FILE.exists():
        return {"service_token": "", "bindings": {}}
    return json.loads(_DEVICE_MAP_FILE.read_text(encoding="utf-8"))


def _check_token(request: Request) -> None:
    token = _load_device_map().get("service_token") or ""
    provided = request.headers.get("X-Service-Token", "")
    if not token or provided != token:
        raise AppError(ErrorCode.ERR_COMMON_001, "硬件服务令牌无效", http_status=401)


def _resolve_patient(db: Session, device_id: str) -> Patient:
    """按绑定表把设备映射到学生；未知设备走 '*' 兜底。"""
    bindings = _load_device_map().get("bindings") or {}
    patient_no = bindings.get(device_id) or bindings.get("*")
    if not patient_no:
        raise AppError(ErrorCode.ERR_COMMON_002, "该设备未绑定学生")
    patient = db.scalar(
        select(Patient).where(Patient.patient_no == patient_no, Patient.deleted == 0)
    )
    if patient is None:
        raise AppError(ErrorCode.ERR_COMMON_002, "绑定的学生不存在")
    return patient


def _active_dialogue_task(db: Session, patient_id: int) -> tuple[CareTask, InteractionSession] | None:
    """学生最近一个进行中的 AI 对话任务及其活跃会话。"""
    tasks = list(
        db.scalars(
            select(CareTask)
            .where(
                CareTask.patient_id == patient_id,
                CareTask.collection_mode == "ai_dialogue",
                CareTask.task_status.in_(["in_progress", "pending"]),
                CareTask.deleted == 0,
            )
            .order_by(CareTask.id.desc())
            .limit(5)
        ).all()
    )
    for task in tasks:
        session = db.scalar(
            select(InteractionSession)
            .where(
                InteractionSession.task_id == task.id,
                InteractionSession.deleted == 0,
            )
            .order_by(InteractionSession.id.desc())
        )
        if session is not None:
            return task, session
    return None


def _latest_ai_message_id(db: Session, session: InteractionSession) -> int:
    row = db.scalar(
        select(InteractionMessage.id)
        .where(
            InteractionMessage.interaction_session_id == session.id,
            InteractionMessage.role_type == "AI",
            InteractionMessage.deleted == 0,
        )
        .order_by(InteractionMessage.id.desc())
    )
    return row or 0


def _wait_for_ai_reply(
    db: Session,
    session: InteractionSession,
    *,
    after_id: int,
) -> str | None:
    """轮询等待对话智能体生成的新 AI 回复（异步 Celery → 文本）。"""
    deadline = time.monotonic() + _REPLY_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        row = db.scalar(
            select(InteractionMessage)
            .where(
                InteractionMessage.interaction_session_id == session.id,
                InteractionMessage.role_type == "AI",
                InteractionMessage.deleted == 0,
                InteractionMessage.id > after_id,
            )
            .order_by(InteractionMessage.id.desc())
        )
        if row is not None and (row.content_text or "").strip():
            return row.content_text
        time.sleep(_REPLY_POLL_INTERVAL)
    return None


@router.post(
    "/chat",
    response_model=ApiResponse[dict],
    summary="硬件语音终端对话桥接",
)
def hardware_chat(req: dict, request: Request, db: DbSession) -> dict:
    """板子一句话 → 心晴业务；返回 {mode, reply, task_no}。"""
    _check_token(request)
    device_id = str(req.get("device_id") or "unknown")
    text = str(req.get("text") or "").strip()
    if not text:
        raise AppError(ErrorCode.ERR_COMMON_001, "语音文本不能为空")

    patient = _resolve_patient(db, device_id)
    active = _active_dialogue_task(db, patient.id)
    if active is None:
        return ok(
            {
                "mode": "free",
                "student_name": patient.patient_name,
                "reply": None,
            }
        )

    task, session = active
    after_id = _latest_ai_message_id(db, session)
    response = dialog_service.send_message(
        db,
        SendMessageRequest(
            session_id=session.session_no,
            task_id=task.task_no,
            content=text,
            client_message_id=f"hw-{device_id[:12]}-{int(time.time() * 1000)}-{uuid.uuid4().hex[:6]}",
            input_mode="text",
        ),
        patient_id=patient.id,
    )
    reply = _wait_for_ai_reply(db, session, after_id=after_id)
    return ok(
        {
            "mode": "assessment",
            "student_name": patient.patient_name,
            "task_no": task.task_no,
            "reply": reply,
        }
    )

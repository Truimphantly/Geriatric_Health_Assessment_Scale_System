"""家长端（监护人）API。

作用：手机号 + 短信验证码登录（演示固定码）、读取安全提醒、签署知情同意。
所有返回统一使用 ``{code,message,data}``。
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.configs.app_config import get_app_config
from app.models.base import get_db
from app.schemas.response import ApiResponse, ok
from app.services import guardian_service, referral_service

router = APIRouter(prefix="/api/guardian", tags=["guardian"])
DbSession = Annotated[Session, Depends(get_db)]


def _set_guardian_cookie(response: Response, token: str) -> None:
    config = get_app_config()
    response.set_cookie(
        key=config.security.guardian_session_cookie,
        value=token,
        max_age=config.security.guardian_session_ttl_seconds,
        httponly=True,
        secure=config.security.guardian_session_secure,
        samesite="lax",
        path="/",
    )


@router.post(
    "/send-code",
    response_model=ApiResponse[dict],
    summary="发送监护登录验证码",
)
def send_code(req: dict, db: DbSession) -> dict:
    """校验登记手机号并下发验证码（演示环境回显固定码）。"""
    phone = str(req.get("phone") or "")
    return ok(guardian_service.send_login_code(db, phone=phone))


@router.post(
    "/login",
    response_model=ApiResponse[dict],
    summary="监护人手机号验证码登录",
)
def login(req: dict, response: Response, db: DbSession) -> dict:
    """校验验证码并复用监护人 HttpOnly Cookie。"""
    phone = str(req.get("phone") or "")
    code = str(req.get("code") or "")
    portal, token = guardian_service.login_guardian(db, phone=phone, code=code)
    _set_guardian_cookie(response, token)
    return ok(portal)


@router.get(
    "/me",
    response_model=ApiResponse[dict],
    summary="读取当前监护人门户数据",
)
def get_me(request: Request, db: DbSession) -> dict:
    """返回监护人信息、学生摘要与安全提醒。"""
    patient, _ = guardian_service.get_guardian_context(db, request)
    return ok(guardian_service.build_guardian_portal(db, patient))


@router.post("/logout", summary="监护人退出登录")
def logout(response: Response) -> dict:
    """清除监护人 Cookie。"""
    config = get_app_config()
    response.delete_cookie(config.security.guardian_session_cookie, path="/")
    return ok({"logout": True})

@router.post(
    "/consent-sign",
    response_model=ApiResponse[dict],
    summary="监护人签署知情同意",
)
def sign_consent(request: Request, req: dict, db: DbSession) -> dict:
    """记录监护人签署结果（四类条款在线签署）。"""
    patient, _ = guardian_service.get_guardian_context(db, request)
    return ok(
        guardian_service.sign_guardian_consent(
            db,
            patient=patient,
            signer_name=str(req.get("signer_name") or ""),
            relation=str(req.get("relation") or ""),
            clauses=list(req.get("clauses") or []),
            note=str(req.get("note") or ""),
        )
    )


@router.get(
    "/referrals",
    response_model=ApiResponse[list[dict]],
    summary="查看孩子的风险转介单",
)
def list_referrals(request: Request, db: DbSession) -> dict:
    """返回当前监护学生的转介单列表（转介去向/建议/状态）。"""
    patient, _ = guardian_service.get_guardian_context(db, request)
    rows = referral_service.list_student_referrals(db, student_id=patient.id)
    return ok([referral_service.describe_referral(r, patient) for r in rows])


@router.post(
    "/referrals/{referral_id}/acknowledge",
    response_model=ApiResponse[dict],
    summary="家长确认知悉转介单",
)
def acknowledge_referral(
    referral_id: int,
    req: dict,
    request: Request,
    db: DbSession,
) -> dict:
    """家长确认知悉（待知悉→已确认），可附反馈留言。"""
    patient, _ = guardian_service.get_guardian_context(db, request)
    referral = referral_service.guardian_acknowledge(
        db,
        referral_id=referral_id,
        patient_id=patient.id,
        feedback=str(req.get("feedback") or ""),
    )
    return ok(referral_service.describe_referral(referral, patient))

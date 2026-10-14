"""安全兜底：关键词命中即自动上报心理老师。

作用：验证服务端不依赖模型自觉调用工具，命中自杀/自伤/被侵害类高优先级
      关键词时直接创建上报（need_manual_intervention=True + 老师端提醒）。
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services import dialog_service


class _FakeSession:
    def __init__(self, handoff_required: bool = False) -> None:
        self.id = 1
        self.session_no = "SESS-TEST"
        self.patient_id = 13
        self.handoff_required = handoff_required


def _match(priority: int, terms: list[str]) -> SimpleNamespace:
    return SimpleNamespace(
        rule_code="KW_SUICIDE",
        rule_name="自杀风险关键词（最高优先）",
        priority=priority,
        matched_terms=terms,
    )


def _message(text: str) -> SimpleNamespace:
    return SimpleNamespace(message_no="MSG-TEST-1", content_text=text)


def test_high_priority_match_triggers_handoff(monkeypatch: pytest.MonkeyPatch) -> None:
    """优先级 >=900 命中时应调用上报。"""
    captured: dict = {}

    def fake_request_handoff(db, task_ref, request, *, patient_id):
        captured["task_ref"] = task_ref
        captured["request"] = request
        captured["patient_id"] = patient_id
        return {"request_id": "SUPPORT-TEST"}

    monkeypatch.setattr(
        "app.services.tool_interaction_service.request_handoff",
        fake_request_handoff,
    )

    session = _FakeSession()
    task = SimpleNamespace(task_no="TASK-TEST")
    dialog_service._auto_escalate_crisis(
        db=None,
        session=session,
        task=task,
        matches=[_match(1000, ["不想活"])],
        message=_message("有时候真的觉得活着没什么意思，不想面对了"),
    )

    assert captured["task_ref"] == "TASK-TEST"
    assert captured["request"].requested_action == "notify_counselor"
    assert captured["request"].urgency == "urgent"
    assert "关键词安全兜底自动上报" in captured["request"].reason


def test_low_priority_match_does_not_escalate(monkeypatch: pytest.MonkeyPatch) -> None:
    """低于阈值的规则（如学业压力）不应自动上报。"""
    called = {"count": 0}

    def fake_request_handoff(*args, **kwargs):
        called["count"] += 1
        return {}

    monkeypatch.setattr(
        "app.services.tool_interaction_service.request_handoff",
        fake_request_handoff,
    )

    dialog_service._auto_escalate_crisis(
        db=None,
        session=_FakeSession(),
        task=SimpleNamespace(task_no="TASK-TEST"),
        matches=[_match(700, ["压力大"])],
        message=_message("最近考试压力有点大"),
    )
    assert called["count"] == 0


def test_existing_handoff_is_not_duplicated(monkeypatch: pytest.MonkeyPatch) -> None:
    """已有上报的会话不再重复上报。"""
    called = {"count": 0}

    def fake_request_handoff(*args, **kwargs):
        called["count"] += 1
        return {}

    monkeypatch.setattr(
        "app.services.tool_interaction_service.request_handoff",
        fake_request_handoff,
    )

    dialog_service._auto_escalate_crisis(
        db=None,
        session=_FakeSession(handoff_required=True),
        task=SimpleNamespace(task_no="TASK-TEST"),
        matches=[_match(1000, ["想死"])],
        message=_message("我不想活了"),
    )
    assert called["count"] == 0

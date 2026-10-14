"""清理旧老年演示任务与相关会话。

作用：
1. 把挂载老年量表的演示任务（TASK-5E3A5EB70C1E 等）连同其交互会话/事件导出为 JSON 备份；
2. 软删除这些任务与会话，使老师端/学生端只呈现心理护航口径的演示数据。

用法：uv run python -m scripts.cleanup_legacy_demo_tasks
说明：仅软删除（deleted=1），备份文件落在 storage/legacy-demo-backup/，可人工恢复。
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select, text

from app.configs.app_config import get_app_config
from app.models import base as model_base
from app.models.interaction import InteractionEvent, InteractionMessage, InteractionSession
from app.models.patient_task import CareTask

LEGACY_TASK_NOS = [
    "TASK-5E3A5EB70C1E",
    "TASK-C00C9FBF2473",
    "TASK-2177183AC523",
    "TASK-79A017F0F982",
    "TASK-C67A88888FCC",
    "TASK-C5D9225E4D0F",
    "TASK-FCC22D682A75",
]


def _row_to_dict(row) -> dict:
    data = dict(row.__dict__)
    data.pop("_sa_instance_state", None)
    for key, value in list(data.items()):
        if isinstance(value, datetime):
            data[key] = value.isoformat()
    return data


def main() -> None:
    """执行导出与软删除。"""
    model_base.init_db(get_app_config().database.url)
    if model_base.SessionLocal is None:
        raise RuntimeError("数据库未初始化")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    backup_dir = Path(__file__).resolve().parents[1] / "storage" / "legacy-demo-backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"legacy-demo-{stamp}.json"

    with model_base.SessionLocal() as db:
        tasks = db.scalars(
            select(CareTask).where(CareTask.task_no.in_(LEGACY_TASK_NOS))
        ).all()
        task_ids = [task.id for task in tasks]
        sessions = (
            db.scalars(
                select(InteractionSession).where(
                    InteractionSession.task_id.in_(task_ids)
                )
            ).all()
            if task_ids
            else []
        )
        session_ids = [item.id for item in sessions]
        messages = (
            db.scalars(
                select(InteractionMessage).where(
                    InteractionMessage.interaction_session_id.in_(session_ids)
                )
            ).all()
            if session_ids
            else []
        )
        events = (
            db.scalars(
                select(InteractionEvent).where(
                    InteractionEvent.interaction_session_id.in_(session_ids)
                )
            ).all()
            if session_ids
            else []
        )

        backup = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "tasks": [_row_to_dict(item) for item in tasks],
            "sessions": [_row_to_dict(item) for item in sessions],
            "messages": [_row_to_dict(item) for item in messages],
            "events": [_row_to_dict(item) for item in events],
        }
        backup_path.write_text(
            json.dumps(backup, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )

        for task in tasks:
            task.deleted = 1
        for session in sessions:
            session.deleted = 1
        db.commit()

        print(f"备份: {backup_path}")
        print(
            f"软删除: 任务 {len(tasks)} 个 / 会话 {len(sessions)} 个 / "
            f"消息 {len(messages)} 条 / 事件 {len(events)} 条"
        )
        purge_legacy_alerts(set(task_ids))


if __name__ == "__main__":
    main()

def purge_legacy_alerts(legacy_task_ids: set[int]) -> None:
    """清除医护提醒流中属于已删任务的提醒（否则 SSE 回放会重新弹出）。"""
    import redis as redis_lib

    client = redis_lib.Redis(host="127.0.0.1", port=6379, db=0, decode_responses=True)
    for key in client.scan_iter("nurse_stream:*"):
        removed = 0
        for entry_id, fields in client.xrange(key):
            if str(fields.get("task_id") or "") in {str(item) for item in legacy_task_ids}:
                client.xdel(key, entry_id)
                removed += 1
        print(f"提醒流清理 {key}: 删除 {removed} 条")

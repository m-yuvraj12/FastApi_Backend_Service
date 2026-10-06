from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Notification


def create(
    db: Session,
    *,
    user_id: int,
    title: str,
    body: str,
    data: dict | None,
    target: str,
    delivered_count: int,
    fcm_message_ids: list[str],
) -> Notification:
    n = Notification(
        user_id=user_id, title=title, body=body, data=data, target=target,
        delivered_count=delivered_count, fcm_message_ids=fcm_message_ids,
    )
    db.add(n)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(n)
    return n


def get_by_id(db: Session, notification_id: int) -> Notification | None:
    return db.get(Notification, notification_id)


def list_for_user(db: Session, user_id: int, limit: int, offset: int) -> tuple[list[Notification], int]:
    base = select(Notification).where(Notification.user_id == user_id)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    items = db.scalars(
        base.order_by(Notification.created_at.desc(), Notification.id.desc()).limit(limit).offset(offset)
    ).all()
    return list(items), total

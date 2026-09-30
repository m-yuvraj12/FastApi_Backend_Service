import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Device, Notification, User
from app.schemas import NotificationCreate, NotificationList, NotificationOut
from app.services import fcm

log = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post(
    "/send",
    response_model=NotificationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Send a push notification to an Android device",
    responses={
        400: {"description": "No target device"},
        502: {"description": "FCM rejected the message"},
        503: {"description": "FCM not configured on the server"},
    },
)
def send_notification(
    payload: NotificationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 1. Resolve target tokens
    if payload.device_token:
        tokens = [payload.device_token]
        target = f"token:...{payload.device_token[-6:]}"
    else:
        tokens = list(db.scalars(select(Device.fcm_token).where(Device.user_id == user.id)))
        target = "all_devices"
        if not tokens:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "No device registered. Call PUT /devices first or pass 'device_token'.",
            )

    # 2. Send via FCM
    try:
        results = fcm.send_to_tokens(tokens, payload.title, payload.body, payload.data)
    except fcm.FCMNotConfigured as e:
        log.error("%s", e)
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Push service is not configured on the server")
    except Exception:  # network / SDK failure
        log.exception("Unexpected FCM failure")
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Failed to reach push service")

    # 3. Clean up stale tokens we own
    stale = [r.token for r in results if r.unregistered]
    if stale:
        for d in db.scalars(select(Device).where(Device.fcm_token.in_(stale), Device.user_id == user.id)):
            db.delete(d)

    ok = [r for r in results if r.ok]
    if not ok:
        db.commit()  # persist stale-token cleanup only
        detail = results[0].error if len(results) == 1 else "FCM rejected all messages"
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Notification not delivered: {detail}")

    # 4. Persist only successfully triggered notifications
    notification = Notification(
        user_id=user.id,
        title=payload.title,
        body=payload.body,
        data=payload.data,
        target=target,
        delivered_count=len(ok),
        fcm_message_ids=[r.message_id for r in ok],
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


@router.get("", response_model=NotificationList, summary="List notifications I have sent (newest first)")
def list_notifications(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    base = select(Notification).where(Notification.user_id == user.id)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    items = db.scalars(base.order_by(Notification.created_at.desc(), Notification.id.desc()).limit(limit).offset(offset)).all()
    return NotificationList(total=total, limit=limit, offset=offset, items=items)


@router.get("/{notification_id}", response_model=NotificationOut)
def get_notification(notification_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    n = db.get(Notification, notification_id)
    if not n or n.user_id != user.id:  # 404 (not 403) so ids of other users aren't leaked
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notification not found")
    return n

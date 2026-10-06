from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import NotificationCreate, NotificationList, NotificationOut, NotificationSendOut
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post(
    "/send",
    response_model=NotificationSendOut,
    status_code=status.HTTP_201_CREATED,
    summary="Send a push notification to an Android device",
    responses={
        400: {"description": "No target device"},
        401: {"description": "Missing/invalid token"},
        502: {"description": "FCM rejected the message / unreachable"},
        503: {"description": "FCM not configured on the server"},
    },
)
def send_notification(payload: NotificationCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    outcome = notification_service.send(db, user, payload)
    return NotificationSendOut(
        **NotificationOut.model_validate(outcome.notification).model_dump(),
        failed_count=outcome.failed_count,
        removed_stale_devices=outcome.removed_stale_devices,
    )


@router.get("", response_model=NotificationList, summary="List notifications I have sent (newest first)")
def list_notifications(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = notification_service.list_for(db, user, limit, offset)
    return NotificationList(total=total, limit=limit, offset=offset, items=items)


@router.get("/{notification_id}", response_model=NotificationOut)
def get_notification(notification_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return notification_service.get_for(db, user, notification_id)

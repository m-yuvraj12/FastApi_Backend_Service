import logging
from dataclasses import dataclass

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.exceptions import (
    NoTargetDevice, NotFound, PersistenceError, PushDeliveryFailed, PushNotConfigured, PushUnavailable,
)
from app.models import Notification, User
from app.repositories import device_repo, notification_repo
from app.schemas import NotificationCreate
from app.services import fcm

log = logging.getLogger(__name__)


@dataclass
class SendOutcome:
    notification: Notification
    failed_count: int
    removed_stale_devices: int


def send(db: Session, user: User, payload: NotificationCreate) -> SendOutcome:
    # 1. Resolve target tokens
    if payload.device_token:
        tokens = [payload.device_token]
        target = f"token:...{payload.device_token[-6:]}"
    else:
        tokens = device_repo.tokens_for_user(db, user.id)
        target = "all_devices"
        if not tokens:
            raise NoTargetDevice()

    # 2. Hand to FCM
    try:
        results = fcm.send_to_tokens(tokens, payload.title, payload.body, payload.data)
    except fcm.FCMNotConfigured as e:
        log.error("%s", e)
        raise PushNotConfigured()
    except Exception:
        log.exception("Unexpected FCM failure")
        raise PushUnavailable()

    # 3. Remove stale tokens (best effort - must never break the request)
    removed = 0
    stale = [r.token for r in results if r.unregistered]
    if stale:
        try:
            removed = device_repo.delete_tokens_for_user(db, user.id, stale)
        except SQLAlchemyError:
            db.rollback()
            log.warning("Could not remove stale device tokens", exc_info=True)

    ok = [r for r in results if r.ok]
    if not ok:
        detail = results[0].error if len(results) == 1 else "FCM rejected all messages"
        raise PushDeliveryFailed(f"Notification not delivered: {detail}")

    # 4. Persist - only successfully triggered notifications are stored
    message_ids = [r.message_id for r in ok]
    try:
        notification = notification_repo.create(
            db, user_id=user.id, title=payload.title, body=payload.body, data=payload.data,
            target=target, delivered_count=len(ok), fcm_message_ids=message_ids,
        )
    except SQLAlchemyError:
        # The push already went out; log the ids so it can be reconciled manually.
        log.exception("Notification SENT but NOT SAVED (user=%s, fcm_ids=%s)", user.id, message_ids)
        raise PersistenceError()

    return SendOutcome(notification, failed_count=len(results) - len(ok), removed_stale_devices=removed)


def list_for(db: Session, user: User, limit: int, offset: int) -> tuple[list[Notification], int]:
    return notification_repo.list_for_user(db, user.id, limit, offset)


def get_for(db: Session, user: User, notification_id: int) -> Notification:
    n = notification_repo.get_by_id(db, notification_id)
    if not n or n.user_id != user.id:  # 404, not 403: don't leak other users' ids
        raise NotFound("Notification not found")
    return n

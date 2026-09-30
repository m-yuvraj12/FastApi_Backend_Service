"""Thin wrapper around the Firebase Admin SDK."""
import logging
import os
from dataclasses import dataclass

import firebase_admin
from firebase_admin import credentials, messaging

from app.config import get_settings

log = logging.getLogger(__name__)


class FCMNotConfigured(RuntimeError):
    pass


@dataclass
class SendResult:
    token: str
    message_id: str | None = None
    error: str | None = None
    unregistered: bool = False  # token is stale and should be deleted

    @property
    def ok(self) -> bool:
        return self.message_id is not None


def _get_app() -> firebase_admin.App:
    try:
        return firebase_admin.get_app()
    except ValueError:
        pass
    path = get_settings().firebase_credentials_path
    if not os.path.isfile(path):
        raise FCMNotConfigured(f"Firebase service-account file not found at '{path}'")
    return firebase_admin.initialize_app(credentials.Certificate(path))


def send_to_tokens(tokens: list[str], title: str, body: str, data: dict[str, str] | None) -> list[SendResult]:
    app = _get_app()
    messages = [
        messaging.Message(
            token=t,
            notification=messaging.Notification(title=title, body=body),
            data=data or None,
            android=messaging.AndroidConfig(priority="high"),
        )
        for t in tokens
    ]
    batch = messaging.send_each(messages, dry_run=get_settings().fcm_dry_run, app=app)

    results: list[SendResult] = []
    for token, resp in zip(tokens, batch.responses):
        if resp.success:
            results.append(SendResult(token, message_id=resp.message_id))
        else:
            exc = resp.exception
            log.warning("FCM send failed: %s", exc)
            results.append(
                SendResult(token, error=str(exc), unregistered=isinstance(exc, messaging.UnregisteredError))
            )
    return results

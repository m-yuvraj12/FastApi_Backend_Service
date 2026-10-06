from sqlalchemy.orm import Session

from app.exceptions import NotFound
from app.models import Device, User
from app.repositories import device_repo


def register(db: Session, user: User, token: str, name: str | None) -> Device:
    """Idempotent. An existing token is re-assigned to the caller."""
    existing = device_repo.get_by_token(db, token)
    if existing:
        return device_repo.reassign(db, existing, user.id, name)
    return device_repo.create(db, user.id, token, name)


def list_for(db: Session, user: User) -> list[Device]:
    return device_repo.list_for_user(db, user.id)


def remove(db: Session, user: User, device_id: int) -> None:
    device = device_repo.get_by_id(db, device_id)
    if not device or device.user_id != user.id:
        raise NotFound("Device not found")
    device_repo.delete_device(db, device)

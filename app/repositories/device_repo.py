from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import Device


def get_by_id(db: Session, device_id: int) -> Device | None:
    return db.get(Device, device_id)


def get_by_token(db: Session, token: str) -> Device | None:
    return db.scalar(select(Device).where(Device.fcm_token == token))


def list_for_user(db: Session, user_id: int) -> list[Device]:
    return list(db.scalars(select(Device).where(Device.user_id == user_id).order_by(Device.id)))


def tokens_for_user(db: Session, user_id: int) -> list[str]:
    return list(db.scalars(select(Device.fcm_token).where(Device.user_id == user_id).order_by(Device.id)))


def create(db: Session, user_id: int, token: str, name: str | None) -> Device:
    device = Device(user_id=user_id, fcm_token=token, name=name)
    db.add(device)
    db.commit()
    return device


def reassign(db: Session, device: Device, user_id: int, name: str | None) -> Device:
    device.user_id = user_id
    if name:
        device.name = name
    db.commit()
    return device


def delete_device(db: Session, device: Device) -> None:
    db.delete(device)
    db.commit()


def delete_tokens_for_user(db: Session, user_id: int, tokens: list[str]) -> int:
    result = db.execute(delete(Device).where(Device.user_id == user_id, Device.fcm_token.in_(tokens)))
    db.commit()
    return result.rowcount or 0

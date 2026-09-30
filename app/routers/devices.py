from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Device, User
from app.schemas import DeviceOut, DeviceRegister

router = APIRouter(prefix="/devices", tags=["devices"])


@router.put("", response_model=DeviceOut, summary="Register (or re-assign) an Android device FCM token")
def register_device(payload: DeviceRegister, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Idempotent. If the token already exists it is re-assigned to the caller
    (e.g. a different user logged in on the same phone)."""
    device = db.scalar(select(Device).where(Device.fcm_token == payload.fcm_token))
    if device:
        device.user_id = user.id
        if payload.name:
            device.name = payload.name
    else:
        device = Device(user_id=user.id, fcm_token=payload.fcm_token, name=payload.name)
        db.add(device)
    db.commit()
    return device


@router.get("", response_model=list[DeviceOut])
def list_devices(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(select(Device).where(Device.user_id == user.id).order_by(Device.id)).all()


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(device_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    device = db.get(Device, device_id)
    if not device or device.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Device not found")
    db.delete(device)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

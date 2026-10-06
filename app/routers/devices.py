from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import DeviceOut, DeviceRegister
from app.services import device_service

router = APIRouter(prefix="/devices", tags=["devices"])


@router.put("", response_model=DeviceOut, summary="Register (or re-assign) an Android device FCM token")
def register_device(payload: DeviceRegister, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return device_service.register(db, user, payload.fcm_token, payload.name)


@router.get("", response_model=list[DeviceOut])
def list_devices(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return device_service.list_for(db, user)


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_device(device_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    device_service.remove(db, user, device_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

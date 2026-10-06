import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import InvalidToken
from app.models import User
from app.repositories import user_repo
from app.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        user_id = decode_access_token(token)
    except (jwt.PyJWTError, ValueError):
        raise InvalidToken()
    user = user_repo.get_by_id(db, user_id)
    if user is None or not user.is_active:
        raise InvalidToken()
    return user

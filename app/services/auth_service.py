from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.exceptions import EmailAlreadyRegistered, InactiveUser, InvalidCredentials
from app.models import User
from app.repositories import user_repo
from app.security import create_access_token, hash_password, verify_password


def register(db: Session, email: str, password: str) -> User:
    if user_repo.get_by_email(db, email):
        raise EmailAlreadyRegistered()
    try:
        return user_repo.create(db, email, hash_password(password))
    except IntegrityError:  # two simultaneous registrations
        raise EmailAlreadyRegistered()


def login(db: Session, email: str, password: str) -> tuple[str, int]:
    user = user_repo.get_by_email(db, email.lower())
    if not user or not verify_password(password, user.hashed_password):
        raise InvalidCredentials()
    if not user.is_active:
        raise InactiveUser()
    return create_access_token(user.id)

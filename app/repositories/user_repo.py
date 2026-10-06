from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def create(db: Session, email: str, hashed_password: str) -> User:
    """May raise sqlalchemy.exc.IntegrityError on duplicate email."""
    user = User(email=email, hashed_password=hashed_password)
    db.add(user)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return user

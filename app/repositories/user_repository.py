from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate


class UserRepository:

    @staticmethod
    def get_by_email(db: Session, email: str) -> User | None:
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> User | None:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def create(db: Session, user_data: UserCreate, hashed_password: str) -> User:
        user = User(
        full_name=user_data.full_name,
        email=str(user_data.email).lower(),
        hashed_password=hashed_password,
        role="CUSTOMER",
    )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
        return db.query(User).offset(skip).limit(limit).all()


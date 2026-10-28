
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationType


class NotificationService:

    @staticmethod
    def create_notification(
        db: Session,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
        )

        db.add(notification)
        db.flush()

        return notification

    @staticmethod
    def get_user_notifications(
        db: Session,
        user_id: int,
        unread_only: bool = False,
    ) -> list[Notification]:
        query = select(Notification).where(
            Notification.user_id == user_id
        )

        if unread_only:
            query = query.where(Notification.is_read.is_(False))

        query = query.order_by(Notification.created_at.desc())

        return list(db.scalars(query).all())

    @staticmethod
    def mark_as_read(
        db: Session,
        notification_id: int,
        user_id: int,
    ) -> Notification | None:
        notification = db.scalar(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )

        if notification is None:
            return None

        notification.is_read = True
        db.flush()

        return notification

   
    @staticmethod
    def mark_all_as_read(
        db: Session,
        user_id: int,
    ) -> int:
        unread_notifications = db.scalars(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        ).all()

        count = len(unread_notifications)

        for notification in unread_notifications:
            notification.is_read = True

        db.flush()

        return count


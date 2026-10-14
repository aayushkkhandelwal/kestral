from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.config import get_settings
from app.core.security import hash_password
from app.core.permissions import UserRole
from app.models.user import User
from app.core.logging import logger

settings = get_settings()

def init_db(db: Session) -> None:
    """Bootstraps default administrator account if database has no users."""
    try:
        stmt = select(User).where(User.email == settings.FIRST_SUPERUSER_EMAIL.lower())
        existing = db.execute(stmt).scalar_one_or_none()
        if not existing:
            admin_user = User(
                name=settings.FIRST_SUPERUSER_NAME,
                email=settings.FIRST_SUPERUSER_EMAIL.lower(),
                password_hash=hash_password(settings.FIRST_SUPERUSER_PASSWORD),
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            logger.info(f"Bootstrap administrator created: {settings.FIRST_SUPERUSER_EMAIL}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to bootstrap administrator account: {e}")

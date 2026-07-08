"""Idempotent database bootstrap: permissions, roles and the first admin user."""
import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.permissions import DEFAULT_ROLES, all_permissions
from app.core.security import hash_password
from app.models.user import Permission, Role, User

logger = logging.getLogger("app.seed")


def sync_permissions(db: Session) -> dict[str, Permission]:
    """Ensure every permission code exists; return {code: Permission}."""
    existing = {p.code: p for p in db.query(Permission).all()}
    for code, description in all_permissions().items():
        if code not in existing:
            perm = Permission(code=code, description=description)
            db.add(perm)
            existing[code] = perm
    db.flush()
    return existing


def sync_roles(db: Session, perms: dict[str, Permission]) -> dict[str, Role]:
    roles: dict[str, Role] = {}
    for name, cfg in DEFAULT_ROLES.items():
        role = db.query(Role).filter(Role.name == name).one_or_none()
        if not role:
            role = Role(name=name, description=cfg["description"], is_system=True)
            db.add(role)
        role.permissions = [perms[c] for c in cfg["permissions"] if c in perms]
        roles[name] = role
    db.flush()
    return roles


def ensure_admin(db: Session, admin_role: Role) -> None:
    existing = db.query(User).filter(User.email == settings.FIRST_ADMIN_EMAIL).one_or_none()
    if existing:
        return
    admin = User(
        full_name=settings.FIRST_ADMIN_NAME,
        email=settings.FIRST_ADMIN_EMAIL,
        username="admin",
        hashed_password=hash_password(settings.FIRST_ADMIN_PASSWORD),
        is_active=True,
        is_superuser=True,
        role_id=admin_role.id,
    )
    db.add(admin)
    logger.info("Created bootstrap admin user: %s", settings.FIRST_ADMIN_EMAIL)


def init_db(db: Session) -> None:
    perms = sync_permissions(db)
    roles = sync_roles(db, perms)
    ensure_admin(db, roles["Administrador"])
    db.commit()
    logger.info("Database bootstrap complete")


if __name__ == "__main__":
    from app.core.database import SessionLocal

    logging.basicConfig(level=logging.INFO)
    with SessionLocal() as session:
        init_db(session)

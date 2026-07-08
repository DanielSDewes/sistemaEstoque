"""User, Role and Permission repositories."""
from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session

from app.models.user import Permission, Role, User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session) -> None:
        super().__init__(User, db)

    def get_by_login(self, login: str) -> User | None:
        stmt = select(User).where(or_(User.username == login, User.email == login)).limit(1)
        return self.db.execute(stmt).scalar_one_or_none()

    def search(self, term: str | None) -> Select:
        stmt = select(User)
        if term:
            like = f"%{term.strip()}%"
            stmt = stmt.where(
                or_(User.full_name.ilike(like), User.email.ilike(like), User.username.ilike(like))
            )
        return stmt


class RoleRepository(BaseRepository[Role]):
    def __init__(self, db: Session) -> None:
        super().__init__(Role, db)

    def get_by_name(self, name: str) -> Role | None:
        return self.get_by(name=name)


class PermissionRepository(BaseRepository[Permission]):
    def __init__(self, db: Session) -> None:
        super().__init__(Permission, db)

    def get_by_codes(self, codes: list[int]) -> list[Permission]:
        stmt = select(Permission).where(Permission.id.in_(codes))
        return list(self.db.execute(stmt).scalars().all())

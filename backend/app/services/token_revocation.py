"""Helpers for the JWT revocation denylist (logout + refresh rotation)."""
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.security import RevokedToken


def purge_expired(db: Session) -> int:
    """Delete denylist rows whose tokens have already expired.

    Expired JWTs are rejected by signature/``exp`` validation before the
    denylist is ever consulted, so their rows are dead weight. Returns the
    number of rows removed. Safe to call periodically (startup / cron).
    """
    result = db.execute(
        delete(RevokedToken).where(RevokedToken.expires_at < datetime.now(UTC))
    )
    db.commit()
    return result.rowcount or 0


def is_revoked(db: Session, jti: str | None) -> bool:
    if not jti:
        return False
    return db.execute(
        select(RevokedToken.jti).where(RevokedToken.jti == jti)
    ).first() is not None


def revoke(db: Session, payload: dict[str, Any], user_id: int | None = None) -> None:
    """Add a token's jti to the denylist (idempotent)."""
    jti = payload.get("jti")
    if not jti or is_revoked(db, jti):
        return
    exp = payload.get("exp")
    expires_at = (
        datetime.fromtimestamp(exp, tz=UTC) if exp else datetime.now(UTC)
    )
    db.add(
        RevokedToken(
            jti=jti,
            token_type=payload.get("type", "access"),
            user_id=user_id,
            expires_at=expires_at,
        )
    )
    db.flush()

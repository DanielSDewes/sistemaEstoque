"""Maintenance command: purge expired rows from the JWT revocation denylist.

Run periodically (e.g. a daily cron / scheduled job) so the ``revoked_tokens``
table does not grow unbounded:

    python -m app.db.purge_tokens
"""
import logging

from app.core.database import SessionLocal
from app.services.token_revocation import purge_expired

logger = logging.getLogger("app.maintenance")


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    with SessionLocal() as db:
        removed = purge_expired(db)
        logger.info("Purged %s expired revoked token(s)", removed)


if __name__ == "__main__":
    main()

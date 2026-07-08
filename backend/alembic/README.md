# Alembic migrations

- Generate a new migration after changing models:
  ```bash
  alembic revision --autogenerate -m "descricao da mudanca"
  ```
- Apply migrations:
  ```bash
  alembic upgrade head
  ```
- Roll back one revision:
  ```bash
  alembic downgrade -1
  ```

The database URL is taken automatically from application settings
(`app.core.config.settings`), so no URL needs to be set in `alembic.ini`.

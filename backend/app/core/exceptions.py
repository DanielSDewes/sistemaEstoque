"""Domain-level exceptions with a centralized -> HTTP mapping in main.py."""


class AppError(Exception):
    """Base class for all handled application errors."""

    status_code: int = 400
    default_message: str = "Erro de aplicacao"

    def __init__(self, message: str | None = None, *, details: object | None = None) -> None:
        self.message = message or self.default_message
        self.details = details
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = 404
    default_message = "Recurso nao encontrado"


class ConflictError(AppError):
    status_code = 409
    default_message = "Conflito com o estado atual do recurso"


class ValidationAppError(AppError):
    status_code = 422
    default_message = "Dados invalidos"


class BusinessRuleError(AppError):
    status_code = 400
    default_message = "Regra de negocio violada"


class AuthenticationError(AppError):
    status_code = 401
    default_message = "Nao autenticado"


class PermissionDeniedError(AppError):
    status_code = 403
    default_message = "Permissao negada"

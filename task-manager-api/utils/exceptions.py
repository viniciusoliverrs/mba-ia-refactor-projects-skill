class AppError(Exception):
    """Exceção base de domínio convertida em resposta JSON pelo middleware."""

    status = 500

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class ValidationError(AppError):
    status = 400


class AuthError(AppError):
    status = 401


class ForbiddenError(AppError):
    status = 403


class NotFoundError(AppError):
    status = 404


class ConflictError(AppError):
    status = 409

class AppError(Exception):
    """Erro de domínio convertido em resposta HTTP pelo error handler central."""

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


# exceptions/errors.py


class AppError(Exception):
    pass


class StorageError(AppError):
    pass


class EnvVariableError(AppError):
    pass


class EmailAuthError(AppError):
    pass


class EmailDeliveryError(AppError):
    pass


class UnsupportedMediaError(AppError):
    """Raised when no handler matches — caller decides the user-facing message."""
    pass

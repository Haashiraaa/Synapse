
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

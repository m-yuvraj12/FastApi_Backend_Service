"""Domain errors. Raised by services/deps, converted to JSON responses in main.py."""


class AppError(Exception):
    status_code = 500
    detail = "Internal server error"
    headers: dict[str, str] | None = None

    def __init__(self, detail: str | None = None):
        if detail:
            self.detail = detail
        super().__init__(self.detail)


class EmailAlreadyRegistered(AppError):
    status_code = 409
    detail = "Email already registered"


class InvalidCredentials(AppError):
    status_code = 401
    detail = "Incorrect email or password"
    headers = {"WWW-Authenticate": "Bearer"}


class InvalidToken(AppError):
    status_code = 401
    detail = "Invalid or expired token"
    headers = {"WWW-Authenticate": "Bearer"}


class InactiveUser(AppError):
    status_code = 403
    detail = "User is inactive"


class NotFound(AppError):
    status_code = 404
    detail = "Resource not found"


class NoTargetDevice(AppError):
    status_code = 400
    detail = "No device registered. Call PUT /devices first or pass 'device_token'."


class PushDeliveryFailed(AppError):
    status_code = 502
    detail = "Notification not delivered"


class PushUnavailable(AppError):
    status_code = 502
    detail = "Failed to reach push service"


class PushNotConfigured(AppError):
    status_code = 503
    detail = "Push service is not configured on the server"


class PersistenceError(AppError):
    status_code = 500
    detail = "Notification was sent but could not be saved"

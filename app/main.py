import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.exceptions import AppError
from app.routers import auth, devices, health, notifications

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("app")

app = FastAPI(
    title="Push Notification Service",
    version="1.1.0",
    description="User auth (JWT) + sending FCM push notifications to Android devices.",
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(devices.router)
app.include_router(notifications.router)


# ---- Error handling: every error leaves the API as {"detail": "..."} ----
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers)


@app.exception_handler(SQLAlchemyError)
async def db_error_handler(request: Request, exc: SQLAlchemyError):
    log.exception("Database error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal database error"})


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    log.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

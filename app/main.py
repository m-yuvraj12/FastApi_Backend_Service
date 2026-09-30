import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import SessionLocal
from app.routers import auth, devices, notifications

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("app")

app = FastAPI(
    title="Push Notification Service",
    version="1.0.0",
    description="User auth (JWT) + sending FCM push notifications to Android devices.",
)

app.include_router(auth.router)
app.include_router(devices.router)
app.include_router(notifications.router)


@app.exception_handler(SQLAlchemyError)
async def db_error_handler(request: Request, exc: SQLAlchemyError):
    log.exception("Database error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal database error"})


@app.get("/health", tags=["meta"])
def health():
    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
    return {"status": "ok"}

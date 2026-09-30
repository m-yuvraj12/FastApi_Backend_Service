from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    # bcrypt only uses the first 72 bytes, so cap the length.
    password: str = Field(min_length=8, max_length=64)

    @field_validator("email")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.lower()


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Seconds until expiry")


class DeviceRegister(BaseModel):
    fcm_token: str = Field(min_length=20, max_length=512, description="FCM registration token from the Android app")
    name: str | None = Field(default=None, max_length=100, examples=["Pixel 8"])


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str | None
    fcm_token: str
    created_at: datetime


class NotificationCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200, examples=["Hello"])
    body: str = Field(min_length=1, max_length=4000, examples=["Sent from Swagger UI"])
    device_token: str | None = Field(
        default=None,
        min_length=20,
        max_length=512,
        description="Send to this FCM token only. If omitted, sent to all devices registered by the caller.",
    )
    data: dict[str, str] | None = Field(default=None, description="Optional custom key/value payload (string values)")

    @field_validator("title", "body")
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be blank")
        return v


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    body: str
    data: dict[str, str] | None
    target: str
    delivered_count: int
    fcm_message_ids: list[str] | None
    created_at: datetime


class NotificationList(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[NotificationOut]

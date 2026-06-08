import datetime
import uuid

from pydantic import BaseModel, Field, field_validator


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$")


class UserSignUpRequest(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, confirm_pwd: str, info) -> str:
        """Validate that password and confirm_password are identical."""
        if "password" in info.data and confirm_pwd != info.data["password"]:
            raise ValueError("Passwords do not match.")
        return confirm_pwd


class UserLoginRequest(UserBase):
    password: str = Field(..., min_length=1)


class UserResponse(UserBase):
    id: uuid.UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True
        json_encoders = {datetime.datetime: lambda dt: dt.isoformat()}  # noqa: RUF012


class TokenResponse(BaseModel):
    message: str

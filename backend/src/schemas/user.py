import datetime
import uuid

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$")


class UserSignUpRequest(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str = Field(..., min_length=8, max_length=100)

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, confirm_pwd: str, info: ValidationInfo) -> str:
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

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    message: str

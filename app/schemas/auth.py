from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional


class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str
    role: str
    roll_number: Optional[str] = None
    department: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserSignup(BaseModel):
    email: EmailStr
    name: str
    roll_number: Optional[str] = None
    department: Optional[str] = None


class OTPRequest(BaseModel):
    email: EmailStr


class OTPVerify(BaseModel):
    email: EmailStr
    otp: str


class MessageResponse(BaseModel):
    message: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserOut

    model_config = ConfigDict(from_attributes=True)


class MentorCreate(BaseModel):
    email: EmailStr
    name: str
    department: Optional[str] = None
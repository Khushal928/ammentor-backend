import random
import secrets
import string
from datetime import datetime, timedelta, timezone

from app.db import models
from app.db.db import get_db

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud.auth import create_access_token, hash_otp, create_or_update_otp, get_user_by_email, get_otp_by_email
from app.schemas.auth import MessageResponse, OTPRequest, OTPVerify, TokenResponse, UserSignup, MentorCreate, UserOut

from app.utils.mail import send_email
from app.crud.auth import get_current_user


router = APIRouter()

ALLOWED_STUDENT_DOMAIN = "am.students.amrita.edu"
OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 5


def generate_and_send_otp(db: Session, email: str) -> None:
    otp_code = ''.join(random.choices(string.digits, k=OTP_LENGTH))
    expiry = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES)

    create_or_update_otp(db, email, hash_otp(otp_code), expiry)
    send_email(email, otp_code)


@router.post("/signup", response_model=MessageResponse)
def signup_student(payload: UserSignup, db: Session = Depends(get_db)):
    if not payload.email.endswith(f"@{ALLOWED_STUDENT_DOMAIN}"):
        raise HTTPException(
            status_code=400,
            detail=f"Only @{ALLOWED_STUDENT_DOMAIN} emails are allowed to sign up.",
        )

    existing = get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")

    user = models.User(
        email=payload.email,
        name=payload.name,
        role=models.UserRole.STUDENT,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    generate_and_send_otp(db, user.email)

    return {"message": "Account created. OTP sent to your email — verify to log in."}


@router.post("/send-otp", response_model=MessageResponse)
def send_otp(payload: OTPRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, payload.email)
    if not user:
        raise HTTPException(status_code=404, detail="No account found. Please sign up first.")

    generate_and_send_otp(db, payload.email)

    return {"message": "OTP sent."}


@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp(payload: OTPVerify, db: Session = Depends(get_db)):
    invalid_creds = HTTPException(status_code=400, detail="Invalid OTP or email.")

    user = get_user_by_email(db, payload.email)
    if not user:
        raise invalid_creds

    otp_entry = get_otp_by_email(db, payload.email)
    if not otp_entry or not secrets.compare_digest(otp_entry.otp, hash_otp(payload.otp)):
        raise invalid_creds

    if otp_entry.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="OTP expired.")

    db.delete(otp_entry)
    db.commit()

    access_token = create_access_token(user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }

@router.post("/create-mentor", response_model=UserOut)
def create_mentor(
    payload: MentorCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can create mentors.")

    existing = get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")

    user = models.User(
        email=payload.email,
        name=payload.name,
        role=models.UserRole.MENTOR,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
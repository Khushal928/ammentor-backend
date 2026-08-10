import hashlib
import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db import models
from app.db.db import get_db

key = os.environ.get("KEY")
algorithm = os.environ.get("ALGORITHM")
token_expire_time = 7 

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="")


def hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=token_expire_time)
    details = {
        "user_id": str(user_id),
        "exp": expire,
    }
    return jwt.encode(details, key, algorithm=algorithm)


def decode_token(token: str) -> dict:
    try:
        token_data = jwt.decode(token, key, algorithms=[algorithm])
        return token_data
    except jwt.ExpiredSignatureError:
        return {"error": "token expired"}
    except jwt.PyJWTError:
        return {"error": "invalid token"}


def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    token_data = decode_token(token)

    if "error" in token_data:
        if token_data["error"] == "token expired":
            raise HTTPException(status_code=401, detail="Session expired.")
        raise HTTPException(status_code=401, detail="Invalid token.")

    user_id = int(token_data["user_id"])
    user = get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(status_code=401, detail="User not found.")

    return user

def get_otp_by_email(db, email):
    return db.query(models.OTP).filter(models.OTP.email == email).first()

def create_or_update_otp(db, email, otp, expires_at):
    entry = get_otp_by_email(db, email)
    if entry:
        entry.otp = otp
        entry.expires_at = expires_at
    else:
        entry = models.OTP(email=email, otp=otp, expires_at=expires_at)
        db.add(entry)
    db.commit()
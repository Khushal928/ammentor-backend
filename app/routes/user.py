from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from typing import List

from app.db.db import get_db
from app.db import models

from app.crud.auth import get_current_user
from app.crud.user import get_all_user_claims
from app.schemas.user import UserClaimOut
from app.schemas.claim import UserBrief


router = APIRouter()

@router.get("/me", response_model=UserBrief)
def get_my_details(
    current_user: models.User = Depends(get_current_user),
):
    return current_user

@router.get("/me/claims", response_model=List[UserClaimOut])
def get_my_claims(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_all_user_claims(db, user_id=current_user.id)


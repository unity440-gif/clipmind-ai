"""
Authentication routes: signup, login, Google OAuth, email verification,
and current-user lookup.
"""

import random
from datetime import datetime, timedelta
from schemas.auth import RequestProfileChangeRequest, ConfirmProfileChangeRequest

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.session import get_db
from models.user import User
from schemas.auth import (
    SignupRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    GoogleLoginRequest,
    VerifyEmailRequest,
)
from utils.security import hash_password, verify_password
from utils.jwt import create_access_token
from api.dependencies import get_current_user
from services.email_service import send_verification_email

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from config.settings import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    code = str(random.randint(100000, 999999))
    expires_at = datetime.utcnow() + timedelta(minutes=15)

    new_user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        is_email_verified=False,
        verification_code=code,
        verification_code_expires_at=expires_at,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    send_verification_email(new_user.email, code)

    return new_user


@router.post("/verify-email", response_model=TokenResponse)
def verify_email(payload: VerifyEmailRequest, db: Session = Depends(get_db)):
    """
    Confirms a user's email using the 6-digit code sent at signup.
    Returns a JWT on success, so the user is logged in immediately after verifying.
    """
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if user.is_email_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already verified.")

    if user.verification_code != payload.code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code.")

    if user.verification_code_expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification code has expired.")

    user.is_email_verified = True
    user.verification_code = None
    user.verification_code_expires_at = None
    db.commit()

    token = create_access_token(user_id=str(user.id))
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password.",
    )

    if not user or not user.hashed_password:
        raise invalid_credentials

    if not verify_password(payload.password, user.hashed_password):
        raise invalid_credentials

    token = create_access_token(user_id=str(user.id))
    return TokenResponse(access_token=token)


@router.post("/google", response_model=TokenResponse)
def google_login(payload: GoogleLoginRequest, db: Session = Depends(get_db)):
    try:
        idinfo = id_token.verify_oauth2_token(
            payload.credential,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token.",
        )

    email = idinfo.get("email")
    full_name = idinfo.get("name")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, full_name=full_name, is_email_verified=True)
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token(user_id=str(user.id))
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns the currently logged-in user's info.
    """
    return current_user

@router.post("/profile/request-change")
def request_profile_change(
    payload: RequestProfileChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Stages a name/email change and sends a verification code to the
    user's CURRENT email — the change only applies once that code is confirmed.
    """
    if not payload.full_name and not payload.new_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least a new name or new email.",
        )

    code = str(random.randint(100000, 999999))
    expires_at = datetime.utcnow() + timedelta(minutes=15)

    current_user.pending_full_name = payload.full_name
    current_user.pending_email = payload.new_email
    current_user.verification_code = code
    current_user.verification_code_expires_at = expires_at
    db.commit()

    # Sent to the CURRENT email on file — proves whoever's making
    # this change actually controls the existing account.
    send_verification_email(current_user.email, code)

    return {"success": True, "message": "Verification code sent to your current email."}


@router.post("/profile/confirm-change", response_model=UserResponse)
def confirm_profile_change(
    payload: ConfirmProfileChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Confirms a staged profile change using the code sent to the user's email.
    """
    if current_user.verification_code != payload.code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid code.")

    if current_user.verification_code_expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code has expired.")

    if current_user.pending_full_name:
        current_user.full_name = current_user.pending_full_name
    if current_user.pending_email:
        current_user.email = current_user.pending_email

    current_user.pending_full_name = None
    current_user.pending_email = None
    current_user.verification_code = None
    current_user.verification_code_expires_at = None
    db.commit()
    db.refresh(current_user)

    return current_user
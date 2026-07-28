"""
Authentication routes: signup and login.
Signup creates a new user with a securely hashed password.
Login verifies credentials and returns a JWT access token.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.dependencies import get_current_user

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from config.settings import settings
from schemas.auth import GoogleLoginRequest

from database.session import get_db
from models.user import User
from schemas.auth import SignupRequest, LoginRequest, TokenResponse, UserResponse
from utils.security import hash_password, verify_password
from utils.jwt import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    # Check if this email is already registered
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    new_user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)  # reloads the object with DB-generated values (like id, created_at)

    return new_user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    # Deliberately vague error message — never reveal whether the email
    # exists or the password was wrong; that distinction helps attackers.
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
@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns the currently logged-in user's info.
    Proves that get_current_user correctly reads the token and loads the right user.
    """
    return current_user

@router.post("/google", response_model=TokenResponse)
def google_login(payload: GoogleLoginRequest, db: Session = Depends(get_db)):
    """
    Verifies a Google ID token, then logs in the matching user —
    creating a new account automatically if this is their first time.
    """
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
        # First time signing in with this Google account — create a real
        # user row. hashed_password stays NULL since they never set one;
        # our login endpoint already treats that as "can't use password login."
        user = User(email=email, full_name=full_name, is_email_verified=True)
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token(user_id=str(user.id))
    return TokenResponse(access_token=token)
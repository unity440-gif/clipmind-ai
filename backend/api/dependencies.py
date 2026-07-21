"""
Shared FastAPI dependencies.
`get_current_user` is used by any route that should only work for logged-in users —
it reads the JWT from the Authorization header, verifies it, and loads the matching User.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database.session import get_db
from models.user import User
from utils.jwt import decode_access_token

# Tells FastAPI/Swagger where the login endpoint is, so the "Authorize" button
# in /docs knows how to prompt for a token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user_id = decode_access_token(token)
    if user_id is None:
        raise credentials_error

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_error

    return user

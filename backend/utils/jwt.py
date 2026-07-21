"""
JWT (JSON Web Token) creation and verification.
After login, we hand the user a signed token instead of making them
send their password on every request. The token proves "I already logged in"
without the server needing to remember anything (stateless auth).
"""

from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError

from config.settings import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


def create_access_token(user_id: str) -> str:
    """
    Builds a signed JWT containing the user's id and an expiry time.
    Signed with our secret key, so nobody can forge or tamper with it
    without knowing that secret.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """
    Verifies a token's signature and expiry.
    Returns the user_id if valid, or None if the token is invalid/expired.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None

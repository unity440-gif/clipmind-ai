"""
Password hashing and verification utilities.
We NEVER store real passwords — only a one-way hash of them.
Even if the database is ever leaked, the original passwords stay unknown.
"""

from passlib.context import CryptContext

# bcrypt is the industry-standard hashing algorithm for passwords —
# slow by design, which makes brute-force guessing expensive for attackers.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Turns a real password into a secure hash for storage."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Checks a login attempt's password against the stored hash."""
    return pwd_context.verify(plain_password, hashed_password)

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

security_bearer = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}:{key.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        if ":" not in hashed_password:
            return False
        salt, expected_hex = hashed_password.split(":", 1)
        key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100_000)
        return hmac.compare_digest(key.hex(), expected_hex)
    except Exception:
        return False

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.APP_SECRET_KEY, algorithm="HS256")

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.APP_SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        return None

def get_current_user_payload(credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)) -> Dict[str, Any]:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload

def get_optional_user_payload(credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)) -> Optional[Dict[str, Any]]:
    if not credentials or not credentials.credentials:
        return None
    return decode_access_token(credentials.credentials)

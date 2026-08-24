"""Service for Authentication (TOTP and JWT)."""

from __future__ import annotations

import pyotp
import jwt
import datetime
from fastapi import HTTPException
from pydantic import BaseModel

from src.config import Config

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class AuthService:
    @staticmethod
    def verify_totp(code: str) -> bool:
        """Verify the 6-digit TOTP code against the configured secret."""
        if not Config.admin_totp_secret:
            # If not configured, deny all
            return False
            
        totp = pyotp.TOTP(Config.admin_totp_secret)
        return totp.verify(code)
        
    @staticmethod
    def create_access_token() -> TokenResponse:
        """Create a JWT token valid for 24 hours."""
        expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
        payload = {
            "sub": "admin",
            "exp": expiration
        }
        token = jwt.encode(payload, Config.admin_jwt_secret, algorithm="HS256")
        return TokenResponse(access_token=token)
        
    @staticmethod
    def verify_token(token: str) -> dict:
        """Verify a JWT token and return the payload."""
        try:
            payload = jwt.decode(token, Config.admin_jwt_secret, algorithms=["HS256"])
            if payload.get("sub") != "admin":
                raise HTTPException(status_code=401, detail="Invalid token subject")
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

auth_service = AuthService()

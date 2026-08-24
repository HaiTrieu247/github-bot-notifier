"""Route: /api/v1/auth — Authentication endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from src.services.auth_service import auth_service, TokenResponse
from src.config import Config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])

# Security scheme for Swagger UI
security = HTTPBearer()

def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Dependency to verify JWT token in the Authorization header."""
    return auth_service.verify_token(credentials.credentials)

class LoginRequest(BaseModel):
    totp_code: str

@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest) -> TokenResponse:
    """Authenticate with a 6-digit TOTP code and get a JWT."""
    if not Config.admin_totp_secret:
        raise HTTPException(
            status_code=403, 
            detail="Admin TOTP secret is not configured. Check the server logs for the setup code."
        )
        
    if auth_service.verify_totp(body.totp_code):
        logger.info("Admin logged in successfully.")
        return auth_service.create_access_token()
        
    logger.warning("Failed login attempt with incorrect TOTP code.")
    raise HTTPException(status_code=401, detail="Invalid code")

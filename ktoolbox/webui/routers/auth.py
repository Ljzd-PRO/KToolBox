"""Authentication endpoints"""

from fastapi import APIRouter, Depends
from fastapi.security import HTTPBasicCredentials
from pydantic import BaseModel
from ..auth import verify_credentials

router = APIRouter()

class AuthStatus(BaseModel):
    authenticated: bool
    username: str

@router.get("/status", response_model=AuthStatus)
async def auth_status(username: str = Depends(verify_credentials)):
    """Get authentication status"""
    return AuthStatus(authenticated=True, username=username)

@router.post("/logout")
async def logout():
    """Logout endpoint (client handles clearing auth)"""
    return {"message": "Logged out successfully"}
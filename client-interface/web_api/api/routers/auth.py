"""
Authentication with MOD Cloud API endpoints
"""
from fastapi import APIRouter

from ..models import (
    AuthNonceRequest, AuthNonceResponse,
    AuthTokenRequest, AuthTokenResponse
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/nonce", response_model=AuthNonceResponse)
async def handle_auth_nonce(request: AuthNonceRequest):
    """Handle authentication nonce from MOD Cloud service"""
    # Call session manager to process nonce
    return AuthNonceResponse(
        message="Nonce processing not implemented"
    )


@router.post("/token", response_model=AuthTokenResponse)
async def handle_auth_token(request: AuthTokenRequest):
    """Store authentication token from MOD Cloud for API access"""
    # Call session manager to store token
    return AuthTokenResponse(
        access_token=""
    )
"""
Authentication with MOD Cloud API endpoints
"""
from fastapi import APIRouter

from ..models import (
    AuthNonceRequest, AuthNonceResponse,
    AuthTokenRequest, AuthTokenResponse
)

import logging
from fastapi import Request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/nonce", response_model=AuthNonceResponse)
async def handle_auth_nonce(request: AuthNonceRequest, http_request: Request):
    """NOT IMPLEMENTED: Handle authentication nonce from MOD Cloud service.

    TODO: forward nonce to cloud auth handler via session manager and validate device identity.
    """
    # Example of accessing the ZMQ client from application state (if needed):
    zmq_client = getattr(http_request.app.state, 'zmq_client', None)
    # Call session manager to process nonce
    return AuthNonceResponse(
        message="Nonce processing not implemented"
    )


@router.post("/token", response_model=AuthTokenResponse)
async def handle_auth_token(request: AuthTokenRequest, http_request: Request):
    """NOT IMPLEMENTED: Store authentication token from MOD Cloud for API access.

    TODO: persist token securely via session manager/preferences and return stored token reference.
    """
    zmq_client = getattr(http_request.app.state, 'zmq_client', None)
    # Call session manager to store token
    return AuthTokenResponse(
        access_token=""
    )
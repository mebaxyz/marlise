from typing import Optional
from pydantic import BaseModel


class AuthNonceRequest(BaseModel):
    nonce: str
    device_id: Optional[str] = None


class AuthNonceResponse(BaseModel):
    message: str


class AuthTokenRequest(BaseModel):
    token: str
    expires: Optional[int] = None


class AuthTokenResponse(BaseModel):
    access_token: str

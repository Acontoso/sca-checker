import os
from dataclasses import dataclass
from typing import Any

import jwt
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, SecurityScopes
from jwt import InvalidTokenError, PyJWKClient, PyJWKClientError

REQUIRED_COGNITO_SCOPE = os.getenv("COGNITO_REQUIRED_SCOPE", "sca-api/ioc.lookup.all")

_bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CognitoSettings:
    issuer: str

    @property
    def jwks_url(self) -> str:
        return f"{self.issuer}/.well-known/jwks.json"


def get_cognito_settings() -> CognitoSettings:
    issuer = os.getenv("COGNITO_ISSUER") or os.getenv("COGNITO_ISSUER_URL")
    region = os.getenv("COGNITO_REGION")
    user_pool_id = os.getenv("COGNITO_USER_POOL_ID")

    if not issuer:
        if not region or not user_pool_id:
            raise RuntimeError(
                "Cognito auth is not configured. Set COGNITO_ISSUER or both COGNITO_REGION and COGNITO_USER_POOL_ID."
            )
        issuer = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"

    return CognitoSettings(issuer=issuer.rstrip("/"))


def get_jwk_client() -> PyJWKClient:
    return PyJWKClient(get_cognito_settings().jwks_url)


def _build_www_authenticate_value(security_scopes: SecurityScopes) -> str:
    if not security_scopes.scopes:
        return "Bearer"
    return f'Bearer scope="{security_scopes.scope_str}"'


def _normalize_scope_claim(scope_claim: str | list[str] | None) -> set[str]:
    if not scope_claim:
        return set()
    if isinstance(scope_claim, str):
        return {scope for scope in scope_claim.split() if scope}
    return {scope for scope in scope_claim if scope}


def verify_cognito_access_token(token: str, required_scopes: list[str]) -> dict[str, Any]:
    try:
        signing_key = get_jwk_client().get_signing_key_from_jwt(token)
        settings = get_cognito_settings()
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=settings.issuer,
            options={"require": ["exp", "iat", "iss", "token_use"]},
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except (InvalidTokenError, PyJWKClientError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired bearer token.",
        ) from exc

    if payload.get("token_use") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Only Cognito access tokens are accepted.",
        )

    granted_scopes = _normalize_scope_claim(payload.get("scope"))
    missing_scopes = [scope for scope in required_scopes if scope not in granted_scopes]
    if missing_scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing required scope(s): {', '.join(missing_scopes)}",
        )

    return payload


async def require_cognito_access_token(
    security_scopes: SecurityScopes,
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer_scheme),
) -> dict[str, Any]:
    www_authenticate = _build_www_authenticate_value(security_scopes)

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
            headers={"WWW-Authenticate": www_authenticate},
        )

    try:
        return verify_cognito_access_token(credentials.credentials, security_scopes.scopes)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            exc.headers = {**(exc.headers or {}), "WWW-Authenticate": www_authenticate}
        raise

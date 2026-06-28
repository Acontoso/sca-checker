from typing import Any

from fastapi import APIRouter, Security, Request, Query, Depends
from app.models.sca import SCARequest
from app.controllers.api_controller import health_check, snyk_lookup, opensource_lookup, webhook_opensource_lookup
from app.models.snyk import DiscoverPackageResponse
from app.models.opensource import (
    PackageSearchResponse,
    SCAEnrichRequest,
    WebhookOpenSourceResponse,
)
from app.security import REQUIRED_COGNITO_SCOPE, require_cognito_access_token

router = APIRouter()


@router.get("/")
def root_route() -> dict[str, str]:
    return health_check()


@router.get("/health")
def health_route() -> dict[str, str]:
    return health_check()


@router.get("/check")
async def webhook_route(
    _: dict[str, Any] = Security(
        require_cognito_access_token, scopes=[REQUIRED_COGNITO_SCOPE]
    ),
) -> WebhookOpenSourceResponse:
    return await webhook_opensource_lookup()


@router.post("/sca/check")
async def sca_check_route(
    payload: SCARequest,
    _: dict[str, Any] = Security(
        require_cognito_access_token, scopes=[REQUIRED_COGNITO_SCOPE]
    ),
) -> DiscoverPackageResponse | list[DiscoverPackageResponse]:
    return await snyk_lookup(payload)


@router.post("/sca/enrich")
async def sca_enrich_route(
    payload: SCAEnrichRequest,
    _: dict[str, Any] = Security(
        require_cognito_access_token, scopes=[REQUIRED_COGNITO_SCOPE]
    ),
) -> PackageSearchResponse:
    return await opensource_lookup(payload)

# def _test(request: Request) -> type:
#     """
#     This is a test function to demonstrate how to access the request object in a FastAPI route, and how to return an async context manager that yields a value. In this case, it simply returns the type of the request object. Can be used by subsequent routes to access async context manager objects like DB connections etc.
#     """
#     return request.app.state.type

# @router.get("/test", response_model=type)
# def _test2(
#     request: Request, #raw ASGI request object
#     body: type, # Parsed from JSON request body
#     svc: type = Depends(_func), # Dependancy injection, calls function before passing to decorator function
#     cont_manager: type = Depends(_test)
# ):
#     pass

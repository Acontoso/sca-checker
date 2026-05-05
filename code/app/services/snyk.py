import asyncio
import os
from typing import Any
import httpx
from app.loggers.runtime_json_logger import logger
from app.models.sca import Language
from app.models.snyk import DiscoverPackageResponse, SnykDependencySearchResponse
from app.services.runtime import aws_client

BASE_URL = "https://api.au.snyk.io"
DEFAULT_REGION = "ap-southeast-2"
DEFAULT_TIMEOUT_SECONDS = 15
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 0.5
_RETRY_STATUS_CODES = (429, 500, 502, 503, 504)

# Map organization keywords/aliases to Snyk organization IDs.
# Example: both "is" and "instant" can resolve to the same Snyk organization ID.
_ORGANIZATION_KEYWORD_TO_ENV_VAR = {
}

_PACKAGE_MANAGER_FOR_LANGUAGE = {
    Language.dotnet: "nuget",
    Language.python: "pip",
    Language.java: "maven",
    Language.javascript: "npm",
}


class SnykClient:
    """Typed client for Snyk APIs with shared HTTP/session concerns."""

    def __init__(
        self,
        base_url: str = BASE_URL,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self._owns_client = client is None
        self.client = client or self._build_client(timeout_seconds)

    @staticmethod
    def _build_client(timeout_seconds: int) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=timeout_seconds)

    async def __aenter__(self) -> "SnykClient":
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        if self._owns_client:
            await self.client.aclose()

    async def _send_get_request_status(
        self, path: str, headers: dict[str, str] | None = None
    ) -> int:
        url = f"{self.base_url}{path}"
        for attempt in range(self.max_retries + 1):
            try:
                response = await self.client.get(url, headers=headers)
                if (
                    response.status_code in _RETRY_STATUS_CODES
                    and attempt < self.max_retries
                ):
                    await asyncio.sleep(self.backoff_factor * (2**attempt))
                    continue
                return response.status_code
            except httpx.RequestError:
                if attempt == self.max_retries:
                    raise
                await asyncio.sleep(self.backoff_factor * (2**attempt))

        raise RuntimeError("Snyk status request failed after retries")

    async def _post_json(
        self, path: str, payload: dict[str, Any], headers: dict[str, str] | None = None
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        for attempt in range(self.max_retries + 1):
            try:
                response = await self.client.post(
                    url,
                    json=payload,
                    headers=headers,
                )
                if (
                    response.status_code in _RETRY_STATUS_CODES
                    and attempt < self.max_retries
                ):
                    await asyncio.sleep(self.backoff_factor * (2**attempt))
                    continue

                response.raise_for_status()
                data = response.json()
                if not isinstance(data, dict):
                    raise ValueError("Expected JSON object response from Snyk API")
                return data
            except httpx.RequestError:
                if attempt == self.max_retries:
                    raise
                await asyncio.sleep(self.backoff_factor * (2**attempt))

        raise RuntimeError("Snyk API request failed after retries")

    async def get_org_token(self, organization_id: str) -> str:
        token = (
            await asyncio.to_thread(
                aws_client.get_ssm_parameters, [f"snyk_token/{organization_id}"]
            )
        )[0]
        if not token:
            raise EnvironmentError(
                f"Snyk token for organization {organization_id} not found in AWS SSM"
            )
        return token

    async def _search_package_for_organization(
        self,
        organization_id: str,
        organization: str,
        package_name: str,
        package_manager: str,
        language: Language,
        version: str | None,
    ) -> DiscoverPackageResponse:
        headers = {
            "Authorization": await self.get_org_token(organization_id),
            "Accept": "*/*",
        }
        verify_path = f"/rest/orgs/{organization_id}/ecosystems/{package_manager}/packages/{package_name}?version=2025-11-05"
        status_code = await self._send_get_request_status(verify_path, headers=headers)
        if status_code == 404:
            return DiscoverPackageResponse(
                exist=False,
                package_name=package_name,
                version=version,
                package_manager=package_manager,
                organization=organization,
            )
        elif status_code == 200:
            dependency = f"{package_name}@{version}" if version else package_name
            payload = {
                "filters": {
                    "languages": [language.value],
                    "dependencies": [dependency],
                }
            }
            path = f"/v1/org/{organization_id}/dependencies"
            json_response = await self._post_json(
                path, payload=payload, headers=headers
            )
            if json_response.get("total") == 0:
                # In some cases Snyk returns 200 with an empty result if the package exists but has no known vulnerabilities, so we treat this as the package existing but not vulnerable
                return DiscoverPackageResponse(
                    exist=False,
                    package_name=package_name,
                    version=version,
                    organization=organization,
                    package_manager=package_manager,
                    snyk_response=None,
                )
            else:
                parsed = SnykDependencySearchResponse.model_validate(json_response)
                return DiscoverPackageResponse(
                    exist=True,
                    package_name=package_name,
                    version=version,
                    organization=organization,
                    package_manager=package_manager,
                    snyk_response=parsed,
                )
        else:
            raise ValueError(
                f"Unexpected status code {status_code} when verifying package existence for {package_name} in organization {organization}"
            )

    async def discover_package(
        self,
        package_name: str,
        language: Language,
        organization: str,
        version: str | None = None,
    ) -> DiscoverPackageResponse | list[DiscoverPackageResponse]:
        """Search for a package in the Open Source Malware database and return analysis results."""
        logger.info(
            f"Searching for package: {package_name}, ecosystem: {language.value}, organization: {organization}, version: {version}"
        )
        if organization.strip().lower() == "all":
            organizations = _get_all_organizations()
            package_manager = _get_default_package_manager_for_language(language)
            org_results: list[DiscoverPackageResponse] = []
            errors: list[str] = []
            results = await asyncio.gather(
                *[
                    self._search_package_for_organization(
                        organization_id,
                        organization_name,
                        package_name,
                        package_manager,
                        language,
                        version,
                    )
                    for organization_name, organization_id in organizations
                ],
                return_exceptions=True,
            )

            for (organization_name, organization_id), result in zip(
                organizations, results
            ):
                if isinstance(result, Exception):
                    errors.append(f"{organization_name} ({organization_id}): {result}")
                    continue

                org_results.append(result)

            if errors:
                logger.error(
                    f"Snyk multi-organization scan had failures: {'; '.join(errors)}"
                )

            return org_results

        organization_id = _get_organization_id(organization)
        package_manager = _get_default_package_manager_for_language(language)
        return await self._search_package_for_organization(
            organization_id=organization_id,
            organization=organization,
            package_name=package_name,
            package_manager=package_manager,
            language=language,
            version=version,
        )


def _get_all_organizations() -> list[tuple[str, str]]:
    # return a sorted list of (organization_name, organization_id) tuples for all configured organizations, list of tuples
    organizations = sorted(_ORGANIZATION_KEYWORD_TO_ENV_VAR.items())
    if not organizations:
        raise EnvironmentError("No mapped Snyk organization IDs are configured")
    return organizations


def _get_organization_id(organization_name: str) -> str:
    mapped_value = _ORGANIZATION_KEYWORD_TO_ENV_VAR.get(organization_name.strip())
    if mapped_value:
        return mapped_value
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown organization '{organization_name}'",
        )


def _get_default_package_manager_for_language(language: Language) -> str:
    package_manager = _PACKAGE_MANAGER_FOR_LANGUAGE.get(language)
    if not package_manager:
        raise ValueError(
            f"No default package manager mapping found for language {language}"
        )
    return package_manager

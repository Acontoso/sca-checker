import asyncio
import os
import re
from typing import Any
import httpx
from app.models.opensource import (
    PackageSearchResponse,
    MaliciousPackageResponse,
    CleanPackageResponse,
)
from app.loggers.runtime_json_logger import logger
from app.services.runtime import aws_client

BASE_URL = "https://api.opensourcemalware.com"
DEFAULT_REGION = "ap-southeast-2"
DEFAULT_TIMEOUT_SECONDS = 15
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 0.5
_RETRY_STATUS_CODES = (429, 500, 502, 503, 504)


class OpenSourceClient:
    """Typed client for Open Source Malware APIs with shared HTTP/session concerns."""

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
        self._cached_headers: dict[str, str] | None = None
        self._token: str | None = None

    @staticmethod
    def _build_client(timeout_seconds: int) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=timeout_seconds)

    async def __aenter__(self) -> "OpenSourceClient":
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        if self._owns_client:
            await self.client.aclose()

    async def _headers(self) -> dict[str, str]:
        if self._cached_headers is None:
            token = await self._get_token()
            self._cached_headers = {
                "Authorization": f"Bearer {token}",
            }
        return self._cached_headers

    async def _get_token(self) -> str:
        if self._token is None:
            self._token = await _get_token_provider()
        return self._token

    async def _send_request(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers = await self._headers()

        for attempt in range(self.max_retries + 1):
            try:
                response = await self.client.get(
                    url,
                    headers=headers,
                    params=payload,
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
                    raise ValueError(
                        "Expected JSON object response from Open Source API"
                    )
                return data
            except httpx.RequestError:
                if attempt == self.max_retries:
                    raise
                await asyncio.sleep(self.backoff_factor * (2**attempt))

        raise RuntimeError("Open Source API request failed after retries")

    async def search_package(
        self, package_name: str, ecosystem: str, version: str | None = None
    ) -> PackageSearchResponse:
        """Search for a package in the Open Source Malware database and return analysis results."""
        logger.info(
            f"Searching for package: {package_name}, ecosystem: {ecosystem}, version: {version}"
        )
        payload = {
            "package_name": package_name,
            "ecosystem": ecosystem,
        }
        if version:
            payload["version"] = version
        json_response = await self._send_request(
            "/functions/v1/check-package-malicious", payload
        )
        if json_response.get("malicious"):
            return MaliciousPackageResponse.model_validate(json_response)
        else:
            return CleanPackageResponse.model_validate(json_response)
        
    async def search_compromised_package(
        self, ecosystem: str
    ) -> PackageSearchResponse:
        """Search for a compromised package in the Open Source Malware database and return analysis results."""
        logger.info(
            f"Searching for compromised packages in ecosystem: {ecosystem}"
        )
        payload = {
            "ecosystem": ecosystem,
        }
        json_response = await self._send_request(
            "/functions/v1/query-latest", payload
        )
        allowed_severities = {"critical", "high"}
        threats = json_response.get("threats", []) if isinstance(json_response, dict) else []

        filtered_threats = [
            threat
            for threat in threats
            if threat.get("severity_level") in allowed_severities
            and threat.get("status") == "verified"
        ]

        filtered_response = {
            **json_response,
            "count": len(filtered_threats),
            "threats": filtered_threats,
        } if isinstance(json_response, dict) else {"count": 0, "threats": []}


        versioned_threats = []
        for threat in filtered_threats:
            parsed_versions = await _extract_versions(threat.get("version_info"))
            if not parsed_versions:
                continue
            for parsed_version in parsed_versions:
                threat_copy = {**threat, "parsed_version": parsed_version}
                versioned_threats.append(threat_copy)

        filtered_response["count"] = len(versioned_threats)
        filtered_response["threats"] = versioned_threats

        first_threat = versioned_threats[0] if versioned_threats else None
        if first_threat:
            filtered_response["first_parsed_version"] = first_threat.get("parsed_version")
        return filtered_response

async def _get_token_provider() -> str:
    if "AWS_LAMBDA_FUNCTION_NAME" in os.environ:
        token = (
            await asyncio.to_thread(
                aws_client.get_ssm_parameters, [f"snyk_token/opensourceapi"]
            )
        )[0]
        return token
    else:
        token = os.getenv("OPENSOURCE_API_TOKEN")
        if not token:
            raise EnvironmentError(
                "OPENSOURCE_API_TOKEN environment variable is required when not running in AWS Lambda"
            )
        return token


async def _extract_versions(version_info: str | None) -> list[str]:
    if not version_info:
        return []

    value = version_info.strip()
    if not value:
        return []

    if value.lower() == "all":
        return []

    range_match = re.search(r"(\d+(?:\.\d+)+)\s*-\s*(\d+(?:\.\d+)+)", value)
    if range_match:
        start_version = range_match.group(1)
        end_version = range_match.group(2)

        start_parts = [int(part) for part in start_version.split(".")]
        end_parts = [int(part) for part in end_version.split(".")]

        if (
            len(start_parts) == len(end_parts)
            and start_parts[:-1] == end_parts[:-1]
            and start_parts[-1] <= end_parts[-1]
        ):
            prefix = ".".join(str(part) for part in start_parts[:-1])
            return [
                f"{prefix}.{patch}" if prefix else str(patch)
                for patch in range(start_parts[-1], end_parts[-1] + 1)
            ]

    # Pull the first numeric dotted version and ignore trailing labels/brackets/text.
    version_match = re.search(r"\b\d+(?:\.\d+)+\b", value)
    if version_match:
        return [version_match.group(0)]

    return []

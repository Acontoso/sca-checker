from typing import Any
import asyncio

from app.models.sca import SCARequest, Language
from app.loggers.runtime_json_logger import logger
from app.services.clients import get_opensource_client, get_snyk_client
from app.models.snyk import DiscoverPackageResponse
from app.models.opensource import (
    PackageSearchResponse,
    SCAEnrichRequest,
    WebhookMatch,
    WebhookOpenSourceResponse,
)


_snyk_client = get_snyk_client()
_opensource_client = get_opensource_client()


def health_check() -> dict[str, str]:
    logger.info("health_check_called")
    return {"status": "ok"}


async def snyk_lookup(
    payload: SCARequest,
) -> DiscoverPackageResponse | list[DiscoverPackageResponse]:
    logger.info(
        f"Searching for package: {payload.package_name}, ecosystem: {payload.language.value}, business unit: {payload.business_unit}, version: {payload.version}"
    )
    return await _snyk_client.discover_package(
        package_name=payload.package_name,
        language=payload.language,
        organization=payload.business_unit,
        version=payload.version,
    )


async def opensource_lookup(payload: SCAEnrichRequest) -> PackageSearchResponse:
    logger.info(
        f"Enriching package: {payload.package_name}, ecosystem: {payload.ecosystem.value}, version: {payload.version}"
    )
    return await _opensource_client.search_package(
        package_name=payload.package_name,
        ecosystem=payload.ecosystem.value,
        version=payload.version,
    )


async def _lookup_ecosystem(ecosystem: str, language: Language) -> list[WebhookMatch]:
    data = await _opensource_client.search_compromised_package(ecosystem=ecosystem)
    threats = data.get("threats", []) if isinstance(data, dict) else []
    matched_packages: list[WebhookMatch] = []

    for item in threats:
        package_name = item.get("package_name")
        version = item.get("parsed_version")
        if not package_name or not version:
            continue

        discover_result = await _snyk_client.discover_package(
            package_name=package_name,
            language=language,
            organization="all",
            version=version,
        )
        discover_results = (
            discover_result if isinstance(discover_result, list) else [discover_result]
        )
        # Provides only the packages that exist in Snyk that are compromised
        existing_results = [result for result in discover_results if result.exist]
        if existing_results:
            # Get a sorted list of affected business units
            affected_business_units = sorted(
                {result.organization for result in existing_results}
            )
            matched_packages.append(
                WebhookMatch(
                    package_name=package_name,
                    version=version,
                    affected_business_units=affected_business_units,
                    severity=item.get("severity_level"),
                    threat_details=item.get("threat_description"),
                )
            )

    return matched_packages


async def webhook_opensource_lookup() -> WebhookOpenSourceResponse:
    logger.info("Webhook route called")

    ecosystem_language_map = [
        ("npm", Language.javascript),
        ("nuget", Language.dotnet),
        ("pypi", Language.python),
    ]
    # unpack each tuple, from the list above and pass to the _lookup_ecosystem function, then gather results asynchronously.
    # The * ensures that each returned future from _lookup_ecosystem is unpacked into the results list, which will be a list of lists of WebhookMatch objects. All three futures are awaited and executed concurrently.
    results = await asyncio.gather(
        *[_lookup_ecosystem(ecosystem, language) for ecosystem, language in ecosystem_language_map]
    )

    matched_packages: list[WebhookMatch] = [match for matches in results for match in matches]

    return WebhookOpenSourceResponse(count=len(matched_packages), matches=matched_packages)

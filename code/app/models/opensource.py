from enum import Enum

from pydantic import BaseModel, Field

class EcoSystem(str, Enum):
    npm = "npm"
    pypi = "pypi"
    maven = "maven"
    javascript = "javascript"
    nuget = "nuget"


class SeverityLevel(str, Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class ThreatDetails(BaseModel):
    """Detailed information about a detected threat."""
    threat_id: str = Field(..., description="Unique identifier for the threat")
    severity_level: SeverityLevel = Field(..., description="Severity level of the threat")
    description: str = Field(..., description="Detailed description of the threat and its impact")
    version_info: str = Field(..., description="Affected versions of the package")


class SCAEnrichRequest(BaseModel):
    package_name: str = Field(..., description="The open source package name to check")
    ecosystem: EcoSystem = Field(..., description="The package ecosystem/registry (e.g., npm, PyPI, Maven, etc.)")
    version: str | None = Field(default=None, description="The version of the open source package to check")


class MaliciousPackageResponse(BaseModel):
    """Response when a package is found to be malicious."""
    malicious: bool = Field(default=True, description="Indicates that the package is malicious.")
    package_name: str = Field(..., description="Name of the package that was searched.")
    ecosystem: EcoSystem = Field(..., description="Package ecosystem/registry of the package.")
    version: str | None = Field(default=None, description="Version of the package if provided or available.")
    threat_count: int = Field(..., description="Number of threats associated with the package.")
    details: ThreatDetails | None = Field(default=None, description="Detailed information about the detected threat")


class CleanPackageResponse(BaseModel):
    """Response when a package is not found in the malicious database."""
    malicious: bool = Field(default=False, description="Indicates that the package is not flagged as malicious.")
    package_name: str = Field(..., description="Name of the package that was searched.")
    ecosystem: EcoSystem = Field(..., description="Package ecosystem/registry of the package.")
    version: str | None = Field(default=None, description="Version of the package if provided or available.")
    threat_count: int | None = Field(default=None, description="Threat count if provided by the API for non-malicious results.")
    message: str | None = Field(default=None, description="Informational API message for clean package results.")


class WebhookMatch(BaseModel):
    package_name: str = Field(..., description="Compromised package name")
    version: str = Field(..., description="Specific affected package version")
    affected_business_units: list[str] = Field(
        default_factory=list,
        description="Business units where the package exists in Snyk",
    )
    severity: str | None = Field(
        default=None,
        description="Threat severity level from Open Source Malware",
    )
    threat_details: str | None = Field(
        default=None,
        description="Threat description from Open Source Malware",
    )


class WebhookOpenSourceResponse(BaseModel):
    count: int = Field(..., description="Total matched package/version records")
    matches: list[WebhookMatch] = Field(
        default_factory=list,
        description="Matched packages found in one or more business units",
    )

PackageSearchResponse = MaliciousPackageResponse | CleanPackageResponse

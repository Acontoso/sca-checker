from pydantic import AliasPath, BaseModel, Field


class SnykDependencyLicense(BaseModel):
    id: str = Field(..., description="Unique identifier for the detected license")
    title: str = Field(..., description="Display title of the license")
    license: str = Field(..., description="SPDX-style license identifier")


class SnykDependencyProject(BaseModel):
    id: str = Field(..., description="Unique identifier for the Snyk project")
    name: str = Field(..., description="Display name of the Snyk project")


class SnykDependencyResult(BaseModel):
    name: str = Field(..., description="Dependency name")
    version: str = Field(..., description="Dependency version")
    type: str = Field(..., description="Package manager or ecosystem type")
    project: SnykDependencyProject | None = Field(
        default=None,
        validation_alias=AliasPath("projects", 0),
        description="First project in which this dependency was found",
    )
    isDeprecated: bool | None = Field(default=None, description="Whether the dependency is deprecated")


class SnykDependencySearchResponse(BaseModel):
    result: SnykDependencyResult | None = Field(
        default=None,
        validation_alias=AliasPath("results", 0),
        description="First dependency returned by the Snyk search",
    )


class DiscoverPackageResponse(BaseModel):
    exist: bool = Field(..., description="Indicates whether the package exists")
    package_name: str = Field(..., description="The open source package name to check")
    version: str = Field(..., description="The version of the open source package that was checked")
    package_manager: str = Field(..., description="The package manager/ecosystem of the package that was checked")
    organization: str = Field(..., description="The organization for which the package was checked")
    snyk_response: SnykDependencySearchResponse | None = Field(
        default=None,
        description="Optional first-result Snyk dependency response",
    )


class DiscoverPackageApiResponse(BaseModel):
    results: list[DiscoverPackageResponse] = Field(
        default_factory=list,
        description="Discover package results. Contains one item for single-org calls and many for all-org calls.",
    )
    total: int = Field(..., description="Number of items returned in results")

    @classmethod
    def from_discover_result(
        cls,
        value: DiscoverPackageResponse | list[DiscoverPackageResponse],
    ) -> "DiscoverPackageApiResponse":
        items = value if isinstance(value, list) else [value]
        return cls(results=items, total=len(items))

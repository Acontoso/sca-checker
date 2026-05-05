from enum import Enum
from pydantic import BaseModel, Field

class BusinessUnit(str, Enum):
    ALL = "all"

class Language(str, Enum):
    dotnet = "dotnet"
    python = "python"
    java = "java"
    javascript = "javascript"

class SCARequest(BaseModel):
    language: Language = Field(..., description="The programming language/ecosystem of the package (e.g., npm, maven, etc.)")
    package_name: str = Field(..., description="The open source package name to check")
    version: str = Field(..., description="The version of the open source package to check")
    business_unit: BusinessUnit = Field(
        default=BusinessUnit.ALL,
        description="The business unit associated with the request"
    )

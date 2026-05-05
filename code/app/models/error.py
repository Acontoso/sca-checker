from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Generic error message")
    request_id: str | None = Field(default=None, description="Optional request ID for tracking")

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from starlette.requests import Request
from starlette.responses import JSONResponse
from app.middleware.request_response_logger import RequestResponseLoggingMiddleware
from app.loggers.runtime_json_logger import logger
from app.routes.api import router as api_router
from app.models.error import ErrorResponse

app = FastAPI(
    title="FastAPI Lambda - API for Software Composition checks",
    version="0.1.0",
    description="A starter FastAPI service that can run on AWS Lambda via Mangum.",
)

app.add_middleware(RequestResponseLoggingMiddleware)
app.include_router(api_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"][1:])
        msg = error["msg"]
        errors.append({"field": field, "message": msg})

    logger.warning(f"Validation error: {errors}")
    return JSONResponse(
        status_code=422,
        content={"error": "Validation failed", "details": errors},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    error_response = ErrorResponse(
        error="An internal server error occurred. Please try again later."
    )
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=8000, reload=True, access_log=False
    )

import os

from mangum import Mangum

from app.main import app


def is_running_on_lambda() -> bool:
    return any(
        [
            os.getenv("AWS_LAMBDA_FUNCTION_NAME"),
            os.getenv("LAMBDA_TASK_ROOT"),
            (os.getenv("AWS_EXECUTION_ENV") or "").startswith("AWS_Lambda"),
        ]
    )


# AWS Lambda entry point: handler.lambda_handler
lambda_handler = Mangum(app) if is_running_on_lambda() else None


if __name__ == "__main__":
    if not is_running_on_lambda():
        import uvicorn

        uvicorn.run(
            "app.main:app", host="127.0.0.1", port=8000, reload=True, access_log=False
        )

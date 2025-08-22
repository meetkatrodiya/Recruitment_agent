from fastapi.responses import JSONResponse
from app.models.common import ApiResponse


def fail(message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ApiResponse(success=False, message=message, data=None).model_dump(),
    )   
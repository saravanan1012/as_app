from typing import Any

from fastapi.responses import JSONResponse


def success(message: str, data: Any = None, status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"success": True, "message": message, "data": data},
    )


def error(
    message: str,
    *,
    status_code: int = 400,
    err: str | None = None,
    data: Any = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "error": err,
            "data": data,
        },
    )

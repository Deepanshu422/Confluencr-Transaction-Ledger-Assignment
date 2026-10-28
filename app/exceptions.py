from fastapi import Request
from fastapi.responses import JSONResponse


class LedgerException(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message


async def ledger_exception_handler(request: Request, exc: LedgerException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "code": exc.code,
            "message": exc.message,
        },
    )
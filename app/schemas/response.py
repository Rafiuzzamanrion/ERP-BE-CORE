from fastapi.responses import JSONResponse


class ApiResponse:
    @staticmethod
    def success(
        message: str = "Success",
        data: dict | list | None = None,
        meta: dict | None = None,
        status_code: int = 200,
    ) -> JSONResponse:
        body: dict = {"success": True, "message": message}
        if data is not None:
            body["data"] = data
        if meta is not None:
            body["meta"] = meta
        return JSONResponse(content=body, status_code=status_code)

    @staticmethod
    def error(
        message: str = "Error",
        status_code: int = 500,
        errors: list | None = None,
    ) -> JSONResponse:
        body: dict = {"success": False, "message": message}
        if errors:
            body["errors"] = errors
        return JSONResponse(content=body, status_code=status_code)

from rest_framework.views import exception_handler as drf_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    response = drf_handler(exc, context)
    if response is not None:
        errors = (
            response.data
            if isinstance(response.data, dict)
            else {"detail": response.data}
        )
        response.data = {
            "success": False,
            "message": str(exc.detail) if hasattr(exc, "detail") else str(exc),
            "errors": errors,
        }
    return response

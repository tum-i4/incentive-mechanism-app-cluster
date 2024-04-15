"""Agatha."""

__version__ = "0.1.0"


import logging
from abc import ABCMeta, abstractmethod
from http import HTTPStatus
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette import status
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.templating import Jinja2Templates

from agatha.util.consts import BASE_DIR

log = logging.getLogger(__name__)
templates = Jinja2Templates(directory=BASE_DIR / "web_services/templates")


class ExceptionHandler(metaclass=ABCMeta):
    """FastAPI Exception handler.

    Add to FastAPI app with `app.exception_handler(StarletteHTTPException)(ExceptionHandler(...))`
    """

    def __init__(self, service_name: Optional[str] = ""):
        """Catch all HTTPException thrown in the endpoints and return the custom error page.

        Args:
            service_name: Optional string to show in the navigation bar.
        """
        self.service_name = service_name

    @abstractmethod
    def __call__(self, request: Request, exc):
        """Show an appropriate error page for the raised error."""


class HTTPExceptionHandler(ExceptionHandler):
    """Handle HTTPException."""

    def __call__(self, request: Request, exc: StarletteHTTPException):
        """See ExceptionHandler.__call__."""
        message = exc.detail or HTTPStatus(exc.status_code).description

        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "service_name": self.service_name,
                "code": exc.status_code,
                "message": message,
                "prefix": request.url,
            },
            status_code=exc.status_code,
        )


class RequestValidationErrorHandler(ExceptionHandler):
    """Handle RequestValidationError."""

    def __call__(self, request: Request, exc: RequestValidationError):
        """See ExceptionHandler.__call__."""
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "service_name": self.service_name,
                "code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "message": "Invalid Request",
                "prefix": request.url,
            },
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


def register_exception_handlers(app: FastAPI, service_name: str):
    """Register all available exception handlers to the given app."""
    app.add_exception_handler(
        StarletteHTTPException, HTTPExceptionHandler(service_name)
    )
    app.add_exception_handler(
        RequestValidationError, RequestValidationErrorHandler(service_name)
    )

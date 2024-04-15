"""REST API endpoints of Study App."""
import logging
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.routing import Mount, Route
from starlette.templating import Jinja2Templates

from agatha import register_exception_handlers
from agatha.util import logger
from agatha.util.config import Config, print_config
from agatha.util.consts import BASE_DIR
from agatha.web_services import study

# init Config and print the startup info message
Config()
print_config()

logger.setup_logger()
log = logging.getLogger(__name__)

templates = Jinja2Templates(directory=BASE_DIR / "web_services/templates")


async def homepage(_):
    """Retrieve homepage of the study app."""
    raise HTTPException(status_code=404, detail="Item not found")


routes: List = [
    Mount(
        "/static",
        app=StaticFiles(directory=BASE_DIR / "static"),
        name="static",
    ),
    Route("/", endpoint=homepage),
]

study_app = FastAPI(routes=routes)
study_app.include_router(study.router)

register_exception_handlers(study_app, "Study")

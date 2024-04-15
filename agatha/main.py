"""REST API endpoints of Agatha."""

import logging
from typing import List

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.responses import PlainTextResponse
from starlette.routing import Mount, Route
from starlette.templating import Jinja2Templates

from agatha import register_exception_handlers
from agatha.backend import incentive_mechanism
from agatha.util import logger
from agatha.util.config import Config, print_config
from agatha.util.consts import BASE_DIR, CONFIG_APP_BASE_URL, SURVEY_APP_BASE_URL
from agatha.web_services import configuration, study, user_survey

# init Config and print the startup info message
Config()
print_config()

logger.setup_logger()
log = logging.getLogger(__name__)

templates = Jinja2Templates(directory=BASE_DIR / "web_services/templates")


async def homepage(request: Request):
    """Retrieve homepage of the agatha app."""
    if not Config.conf["development_mode"]:
        return PlainTextResponse("Incentive Mechanism is running")

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "service_name": "development",
            "apps": [
                {
                    "name": "admin configuration",
                    "url": CONFIG_APP_BASE_URL,
                    "href": CONFIG_APP_BASE_URL,
                },
                {
                    "name": "user survey",
                    "url": f"{SURVEY_APP_BASE_URL}/{{survey_id}}/{{user_id}}",
                    "href": f"{SURVEY_APP_BASE_URL}/1/1",
                },
            ],
            "apis": [
                {
                    "name": "incentive mechanism APIs",
                    "url": "/docs",
                },
                {
                    "name": "admin configuration APIs",
                    "url": f"{CONFIG_APP_BASE_URL}/docs",
                },
                {
                    "name": "user survey APIs",
                    "url": f"{SURVEY_APP_BASE_URL}/docs",
                },
            ],
            "study_pages": [
                {
                    "name": "homepage – start study",
                    "url": "/study/new",
                    "href": "/study/new",
                },
                {
                    "name": "demographic data",
                    "url": "/study/1/{user_uuid}",
                    "href": "/study/1/abc000",
                },
                {
                    "name": "user survey",
                    "url": "/study/2/{user_uuid}",
                    "href": "/study/2/abc000",
                },
                {
                    "name": "vignette study",
                    "url": "/study/3/{user_uuid}",
                    "href": "/study/3/abc000",
                },
            ],
        },
    )


routes: List = [
    Mount(
        "/static",
        app=StaticFiles(directory=BASE_DIR / "static"),
        name="static",
    ),
    Route("/", endpoint=homepage),
    Mount(CONFIG_APP_BASE_URL, configuration.app),
    Mount(SURVEY_APP_BASE_URL, user_survey.app),
]

agatha = FastAPI(routes=routes)
agatha.include_router(incentive_mechanism.router)

if Config.conf["development_mode"]:
    agatha.include_router(study.router)

register_exception_handlers(agatha, "Agatha")
register_exception_handlers(configuration.app, "Configuration")
register_exception_handlers(user_survey.app, "User Survey")

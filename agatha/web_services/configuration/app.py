"""Incentive mechanism admin config app."""

from typing import Callable, Optional

from fastapi import Depends, FastAPI, Form, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from more_itertools import one
from sqlalchemy.orm import Session
from starlette import status

from agatha.backend.data_persistence.crud import DataAccessObject
from agatha.util.config import Config
from agatha.util.consts import (
    AUTH_AGE,
    AUTH_KEY,
    BASE_DIR,
    CONFIG_APP_BASE_URL,
    DEV_USER,
)
from agatha.web_services.configuration import configuration

templates = Jinja2Templates(directory=BASE_DIR / "web_services/templates")

app = FastAPI(
    tags=["admin_config_app"],
)

database = DataAccessObject()


@app.middleware("http")
async def auth(request: Request, call_next):
    """Check whether the app is running under dev env,\
        otherwise whether the user is a logged in admin."""
    if "/login" in str(request.url):
        return await call_next(request)

    user = request.cookies.get(AUTH_KEY, "")
    if Config.conf["development_mode"] and user != DEV_USER:
        response = RedirectResponse(request.url)
        response.set_cookie(AUTH_KEY, DEV_USER, max_age=AUTH_AGE)
        return response

    if configuration.is_admin(user, one(database())):
        return await call_next(request)

    return RedirectResponse(f"{CONFIG_APP_BASE_URL}/login")


@app.get("/login", name="admin login page")
async def login(request: Request, session: Session = Depends(database)):
    """Retrieve the login page for agatha configuration app."""
    if user := request.cookies.get(AUTH_KEY, ""):
        if configuration.is_admin(user, session):
            return RedirectResponse(f"{CONFIG_APP_BASE_URL}/")

    return templates.TemplateResponse(
        "configuration/login.html",
        {
            "request": request,
            "service_name": "Configuration",
            "prefix": CONFIG_APP_BASE_URL,
        },
    )


@app.post("/login", name="login credential submit")
async def submit_login(
    response: Response,
    session: Session = Depends(database),
    email: str = Form(),
):
    """Verify login credentials."""
    if configuration.is_admin(email, session):
        response = RedirectResponse(
            f"{CONFIG_APP_BASE_URL}/", status_code=status.HTTP_302_FOUND
        )
        response.set_cookie(key=AUTH_KEY, value=email, max_age=AUTH_AGE)
        return response
    raise HTTPException(
        status.HTTP_403_FORBIDDEN,
        "You are not authorized to view the configuration page",
    )


@app.get("/", name="configuration web app index")
async def index():
    """Index of the configuration app. Currently redirects to employee dashboard."""
    return RedirectResponse(f"{CONFIG_APP_BASE_URL}/employees")


@app.get("/employees", name="employee dashboard")
async def employees(
    request: Request,
    session: Session = Depends(database),
):
    """Retrieve employee overview."""
    return templates.TemplateResponse(
        "configuration/employees.html",
        {
            "request": request,
            "employees": configuration.get_employees(session),
            "service_name": "Configuration",
            "delivery_models": configuration.get_delivery_models(session),
            "incentive_types": configuration.get_incentive_types(session),
            "dev": Config.conf["development_mode"],
            "auth_key": AUTH_KEY,
            "prefix": CONFIG_APP_BASE_URL,
        },
    )


@app.get("/mechanisms", name="mechanism dashboard")
async def mechanisms(
    request: Request,
    session: Session = Depends(database),
):
    """Retrieve mechanism dashboard."""
    return templates.TemplateResponse(
        "configuration/mechanisms.html",
        {
            "request": request,
            "delivery_models": configuration.get_delivery_models(session),
            "incentive_types": configuration.get_incentive_types(session),
            "service_name": "Configuration",
            "dev": Config.conf["development_mode"],
            "auth_key": AUTH_KEY,
            "prefix": CONFIG_APP_BASE_URL,
        },
    )


@app.post("/submit_employee_model", name="submit employee model to overwrite db")
async def submit_employee_model(
    revolori_id: str = Form(),
    delivery: int = Form(),
    incentive: int = Form(),
    session: Session = Depends(database),
):
    """Submit new employee model to db."""
    configuration.update_employee_model(revolori_id, delivery, incentive, session)
    return RedirectResponse(
        f"{CONFIG_APP_BASE_URL}/employees", status_code=status.HTTP_302_FOUND
    )


def handle_action_and_respond(action: Callable, kind: str, request: Request):
    """Call action function and respond with appropriate response."""
    succeeded: bool = action()
    if not succeeded:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"{kind.capitalize()} with the same name already exists.",
        )
    return RedirectResponse(
        f"{CONFIG_APP_BASE_URL}/mechanisms", status_code=status.HTTP_302_FOUND
    )


@app.post("/submit_delivery_model", name="submit delivery model to update db")
async def submit_delivery_model(
    request: Request,
    item_id: int = Form(),
    name: str = Form(),
    description: Optional[str] = Form(None),
    session: Session = Depends(database),
):
    """Submit changed delivery_model to db."""
    return handle_action_and_respond(
        lambda: configuration.create_or_update_delivery_model(
            name, description, session, item_id
        ),
        "delivery model",
        request,
    )


@app.post("/submit_incentive_type", name="submit incentive type to update db")
async def submit_incentive_model(
    request: Request,
    item_id: int = Form(),
    name: str = Form(),
    description: Optional[str] = Form(None),
    session: Session = Depends(database),
):
    """Submit changed incentive_type to db."""
    return handle_action_and_respond(
        lambda: configuration.create_or_update_incentive_type(
            name, description, session, item_id
        ),
        "incentive type",
        request,
    )


@app.post("/create_delivery_model", name="create delivery model in db")
async def create_delivery_model(
    request: Request,
    name: str = Form(),
    description: Optional[str] = Form(None),
    session: Session = Depends(database),
):
    """Create new delivery model in db."""
    return handle_action_and_respond(
        lambda: configuration.create_or_update_delivery_model(
            name, description, session
        ),
        "delivery model",
        request,
    )


@app.post("/create_incentive_type", name="create incentive type in db")
async def create_incentive_type(
    request: Request,
    name: str = Form(),
    description: Optional[str] = Form(None),
    session: Session = Depends(database),
):
    """Create new incentive type in db."""
    return handle_action_and_respond(
        lambda: configuration.create_or_update_incentive_type(
            name, description, session
        ),
        "incentive type",
        request,
    )

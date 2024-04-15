"""Retrieve data for frontend. Currently from dummy data."""

import logging
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from agatha.backend.data_persistence import models
from agatha.backend.data_persistence.crud import DataAccessObject
from agatha.util import logger

logger.setup_logger()
log = logging.getLogger(__name__)

database = DataAccessObject()


def log_empty_list_error(func: Callable[[Session], list]):
    """Log an error if func returns an empty list.

    Args:
        func: a function returns a list.

    Returns:
        A list returned by func.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if len(result := func(*args, **kwargs)) == 0:
            log.error("returns empty list %s", func.__name__)
        return result

    return wrapper


@log_empty_list_error
def get_employees(session: Session) -> List[Dict[str, Union[str, bool, None, Any]]]:
    """Retrieve all employees.

    Returns:
        A list of extracted information from all available employee_models
    """
    rendered_data = []
    employee_models = database.get_all_employee_models(session)
    for employee_model in employee_models:
        answers = database.get_answered_questions_by_revolori_id(
            session, employee_model.revolori_id or "N/A"
        )
        rendered_data.append(
            {
                "revolori_id": employee_model.revolori_id,
                "survey": len(answers) > 0,
                "d_id": employee_model.d_id,
                "i_id": employee_model.i_id,
                "delivery": (employee_model.delivery_model.name or "N/A").capitalize(),
                "incentive": (employee_model.incentive_type.name or "N/A").capitalize(),
            }
        )
    return rendered_data


@log_empty_list_error
def get_delivery_models(session: Session) -> List[models.DeliveryModel]:
    """Retrieve all delivery models.

    Returns:
        A list of extracted information from all available delivery_models
    """
    delivery_models = database.get_all_delivery_models(session)
    return delivery_models


@log_empty_list_error
def get_incentive_types(session: Session) -> List[models.IncentiveType]:
    """Retrieve all incentive types.

    Returns:
        A list of extracted information from all available incentive_types
    """
    incentive_types = database.get_all_incentive_types(session)
    return incentive_types


def get_employee_model(
    revolori_id: str, session: Session
) -> Optional[models.EmployeeModel]:
    """Retrieve mechanism configuration for one employee.

    Args:
        revolori_id: employee id from Revolori SSO

    Returns:
        An EmployeeModel if exists, None otherwise
    """
    employee_model = database.get_employee_model_by_revolori_id(session, revolori_id)
    return employee_model


def update_employee_model(
    revolori_id: str, d_id: int, i_id: int, session: Session
) -> None:
    """Update employee model with revolori_id, delivery_id and incentive_id.

    Args:
        revolori_id: employee id from Revolori SSO
        d_id: delivery model id
        i_id: incentive type id
    """
    database.update_employee_model_by_ids(session, revolori_id, d_id, i_id)


def create_or_update_delivery_model(
    name: str,
    description: Optional[str],
    session: Session,
    id_to_update: Optional[int] = None,
) -> bool:
    """Create or update delivery model.

    Args:
        name: the (updated) name for the model
        description: the (updated) description for the model
        session: the open database session
        id_to_update: id if an existing delivery model should be updated
    """
    try:
        if id_to_update:
            database.update_delivery_model_by_id(
                session, id_to_update, name.lower(), description
            )
        else:
            database.create_delivery_model(session, name.lower(), description)
    except IntegrityError:
        log.info("another delivery model with that name already exists")
        session.rollback()
        return False
    return True


def create_or_update_incentive_type(
    name: str,
    description: Optional[str],
    session: Session,
    id_to_update: Optional[int] = None,
) -> bool:
    """Create or update incentive type.

    Args:
        name: the (updated) name for the incentive type
        description: the (updated) description for the incentive type
        session: the open database session
        id_to_update: id if an existing incentive type should be updated
    """
    try:
        if id_to_update:
            database.update_incentive_type_by_id(
                session, id_to_update, name.lower(), description
            )
        else:
            database.create_incentive_type(session, name.lower(), description)
    except IntegrityError:
        log.info("another incentive type with that name already exists")
        session.rollback()
        return False
    return True


def is_admin(email: str, session: Session) -> bool:
    """Check whether the given email is among the admin lists."""
    user = database.get_admin_by_email(session, email)
    return user is not None

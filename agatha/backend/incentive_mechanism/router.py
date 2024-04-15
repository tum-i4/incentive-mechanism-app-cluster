"""Routes for incentive mechanism components."""

import logging
from typing import Dict, Optional, Union

from fastapi import APIRouter, Depends, Response
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from agatha.backend.data_persistence.crud import DataAccessObject
from agatha.backend.incentive_mechanism import incentive
from agatha.util.consts import INCENTIVE_API_BASE_URL

log = logging.getLogger(__name__)


router = APIRouter(prefix=INCENTIVE_API_BASE_URL)
database = DataAccessObject()


@router.get("/")
def incentive_types(session: Session = Depends(database)) -> Response:
    """Retrieve all available incentive types."""
    return jsonable_encoder(incentive.get_incentive_types(session))


@router.get("/{revolori_id}")
def select_incentive(
    revolori_id: str, session: Session = Depends(database)
) -> Union[Dict[str, Optional[str]], Response]:
    """Retrieve incentive for an employee.

    Args:
        revolori_id: employee id from Revolori SSO.

    Returns:
        A string represents the incentive type for the employee.
    """
    employee_model = incentive.get_employee_incentive(revolori_id, session)
    if (
        employee_model is None
        or employee_model.delivery_model is None
        or employee_model.incentive_type is None
    ):
        log.info("No delivery model and/or incentive type found for %s", revolori_id)
        return Response(status_code=204)

    configuration = {
        "revolori_id": employee_model.revolori_id,
        "delivery_model": employee_model.delivery_model.name,
        "incentive_type": employee_model.incentive_type.name,
    }
    return configuration

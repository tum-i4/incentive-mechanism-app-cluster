"""Module to generate vignettes for the study."""
import json
import random
import re
from dataclasses import dataclass
from itertools import product
from string import Template
from typing import Dict, Iterator, List, Optional, Tuple

from sqlalchemy.orm import Session

from agatha.backend.data_persistence.study_crud import StudyDataAccessObject

database = StudyDataAccessObject()


@dataclass
class Vignette:
    """Dataclass for Vignette."""

    study_id: int
    vignette_id: str
    factor_levels: Dict[str, Optional[str]]


def generate_vignette_id(study_id: int, **factor_levels) -> str:
    """Generate vignette id from study id and factors.

    Generates id after json format:
        {
            "id": {study_id},
            "levels": {
                "{factor_key}": {level},
                ...
            }
        }
    => levels are sorted to generate unique ids

    Example:
            {
                "id": 1,
                "levels": {
                    "visibility": "true",
                    "data_sharing": 1,
                    ...
                }
            }

    """
    json_dict = {
        "study_id": study_id,
        "factor_levels": dict(sorted(factor_levels.items())),
    }
    return json.dumps(json_dict)


def parse_vignette_id(vignette_id: str) -> Vignette:
    """Parse vignette id to study id and factors.

    Returns:
        a vignette dataclass with study id, vignette id and level for each factor.
    """
    json_dict = json.loads(vignette_id)
    return Vignette(
        vignette_id=vignette_id,
        **json_dict,
    )


def generate_vignette(
    session: Session,
    vignette: Vignette,
    factors: Dict[str, Dict[str, str]],
) -> str:
    """Generate the vignette text from given specification.

    Args:
        session: an open database session
        vignette: Vignette object
        factors: nested dictionary of factors

    Returns:
        Formatted vignette text
    """

    def check_empty_key(factor, key):
        if key is None or key == "None":
            return ""
        return factors[factor][key]

    variables: Dict[str, str] = {
        factor: check_empty_key(factor, key)
        for factor, key in vignette.factor_levels.items()
    }

    vignette_template_str = database.get_vignette_template_by_id(
        session, vignette.study_id
    )
    if not vignette_template_str:
        return ""
    vignette_template = Template(vignette_template_str)

    vignette_text = vignette_template.substitute(**variables)
    vignette_stripped = vignette_text.strip()
    vignette_normalized_whitespace = re.sub(" +", " ", vignette_stripped)

    return vignette_normalized_whitespace


def generate_vignettes(
    session: Session, study_id: int = 1, **preset_factors
) -> Dict[str, str]:
    """Generate shuffled list of vignette ids and return vignettes with id.

    Returns:
        Mapping from vignette id to vignette text for all possible combinations of factor levels.
    """
    factors: Dict[str, Dict[str, str]] = database.get_factors(session)

    # Generate all possible combinations of (factor, level) Tuples for non-preset factors
    remaining_factor_levels: List[List[Tuple[str, str]]] = [
        [(factor, level) for level in levels]
        for factor, levels in factors.items()
        if factor not in preset_factors
    ]
    variable_combinations: Iterator[Tuple[Tuple[str, str], ...]] = product(
        *remaining_factor_levels
    )

    # Check if there is at least one preset factor that is not empty
    preset_factors_valued = {
        factor: key for factor, key in preset_factors.items() if key is not None
    }
    exists_preset_value = len(preset_factors_valued) > 0

    # Generate vignette id and factor keys for all combinations
    vignette_data: List[Vignette] = []
    variable_items: Tuple[Tuple[str, str], ...]
    for variable_items in variable_combinations:
        variables: Dict[str, str] = dict(variable_items)

        def add_vignette_object(study_id: int, **factor_levels):
            vignette_id = generate_vignette_id(study_id, **factor_levels)
            vignette_data.append(
                Vignette(
                    study_id=study_id,
                    vignette_id=vignette_id,
                    factor_levels=factor_levels,
                )
            )

        # If there is at least one preset factor that is not empty,
        # always add a vignette with all preset factors empty
        if exists_preset_value:
            preset_factors_empty: Dict[str, Optional[str]] = {
                factor: None for factor in preset_factors
            }
            add_vignette_object(
                study_id,
                **variables,
                **preset_factors_empty,
            )

        add_vignette_object(study_id, **variables, **preset_factors)

    random.shuffle(vignette_data)

    return {
        vignette.vignette_id: generate_vignette(session, vignette, factors)
        for vignette in vignette_data
    }

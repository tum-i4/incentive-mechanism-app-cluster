"""Script to initialize the database with example data."""
import csv
import sys
from pathlib import Path
from typing import Dict, Optional

import click
from more_itertools import one

from agatha.backend.data_persistence import models
from agatha.backend.data_persistence.crud import DataAccessObject

DAO = DataAccessObject()


@click.command()
@click.option(
    "-r",
    "--random",
    is_flag=True,
    default=False,
    help="Generate random data to add to database.",
)
@click.option(
    "-f",
    "--file",
    "path",
    help="Specify filepath to csv with data to load into database.",
)
def run(random: bool, path: str):
    """Script to initialize database with example data."""
    if path and random:
        print("Cannot specify both --file and --random.", file=sys.stderr)
        sys.exit(1)
    if path:
        load_data_from_file(Path(path))
    elif random:
        gen_and_load_random_data()
    else:
        print("No options specified. Use --help for more information.", file=sys.stderr)


def create_answer_types(db, answer_type_data):
    """Create answer-type and return objects."""
    answer_types = {}

    for answer_type_name, scoring, scoring_min, scoring_max in answer_type_data:

        most_negative, most_positive = 0, 0

        if scoring == "Reverse":
            most_positive, most_negative = scoring_min, scoring_max
        elif scoring == "Forward":
            most_negative, most_positive = scoring_min, scoring_max

        answer_types[answer_type_name] = DAO.create_answer_type(
            db,
            short_name=answer_type_name,
            description="",
            most_positive=most_positive,
            most_negative=most_negative,
        )
    return answer_types


def create_delivery_models(db, delivery_model_data):
    """Create delivery-models and return objects."""
    delivery_models = {}

    for delivery_model in delivery_model_data:
        if delivery_model == "NULL":
            delivery_models[delivery_model] = None
            continue
        delivery_models[delivery_model] = DAO.create_delivery_model(
            db, name=delivery_model, description=""
        )

    return delivery_models


def create_incentive_types(db, incentive_type_data):
    """Create incentive-types and return objects."""
    incentive_types = {}

    for incentive_type in incentive_type_data:
        if incentive_type == "NULL":
            incentive_types[incentive_type] = None
            continue
        incentive_types[incentive_type] = DAO.create_incentive_type(
            db, name=incentive_type, description=""
        )

    return incentive_types


def create_surveys(db, survey_data):
    """Create surveys and return objects."""
    surveys = {}

    for survey_name in survey_data:
        surveys[survey_name] = DAO.create_survey(db, name=survey_name, description="")

    return surveys


def create_factors(db, factor_data, incentive_types, delivery_models):
    """Create factors and return objects."""
    factors = {}

    for factor_name, incentive_type, delivery_model in factor_data:
        factors[factor_name] = DAO.create_factor_by_objects(
            db,
            name=factor_name,
            incentive_type=incentive_types[incentive_type],
            delivery_model=delivery_models[delivery_model],
        )
    return factors


def load_data_from_file(file: Path):
    """Load data from csv file and save it to database.

    Args:
        file: Path object for csv file
    """
    if not file.exists():
        print("File does not exist.", file=sys.stderr)
        sys.exit(1)
    data = []
    with file.open("r", encoding="utf-8") as data_file:
        reader = csv.reader(data_file)
        columns = next(reader)
        for row in reader:
            data.append(row)

    # create constants for column indices
    DESCRIPTION = columns.index("question")
    FACTOR = columns.index("factor")
    SURVEY = columns.index("survey")
    ANSWER_TYPE = columns.index("answer_type")
    SCORING = columns.index("scoring")
    MIN = columns.index("scoring_min")
    MAX = columns.index("scoring_max")
    INCENTIVE_TYPE = columns.index("incentive_type")
    DELIVERY_MODEL = columns.index("delivery_model")

    # retrieve sets of additional tables
    survey_data = set()
    answer_type_data = set()
    factor_data = set()
    delivery_model_data = set()
    incentive_type_data = set()

    for row in data:
        survey_data.add(row[SURVEY])
        answer_type_data.add(
            (row[ANSWER_TYPE], row[SCORING], int(row[MIN]), int(row[MAX]))
        )
        factor_data.add((row[FACTOR], row[INCENTIVE_TYPE], row[DELIVERY_MODEL]))
        delivery_model_data.add(row[DELIVERY_MODEL])
        incentive_type_data.add(row[INCENTIVE_TYPE])

    session = one(DAO())

    # fill dependent tables
    answer_types = create_answer_types(session, answer_type_data)
    surveys = create_surveys(session, survey_data)
    delivery_models: Dict[str, Optional[models.DeliveryModel]] = create_delivery_models(
        session, delivery_model_data
    )
    incentive_types: Dict[str, Optional[models.IncentiveType]] = create_incentive_types(
        session, incentive_type_data
    )
    factors = create_factors(session, factor_data, incentive_types, delivery_models)

    # create questions and save them to database
    for row in data:
        DAO.create_question_for_survey(
            session,
            survey=surveys[row[SURVEY]],
            question=row[DESCRIPTION],
            answer_type=answer_types[row[ANSWER_TYPE]],
            factor=factors[row[FACTOR]],
            weight=100,
        )


def gen_and_load_random_data():
    """Generate random data and add to database."""
    raise NotImplementedError()


if __name__ == "__main__":
    run()  # pylint: disable=no-value-for-parameter

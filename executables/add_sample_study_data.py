"""Script to enter sample data into the database."""

from more_itertools import one

from agatha.backend.data_persistence.study_crud import StudyDataAccessObject

database = StudyDataAccessObject()

session = one(database())

likert_5_answer = database.create_answer_type(
    db=session,
    short_name="likert-5",
    description="Scale of 5 units that ranges between the choices 'Strongly disagree' to 'Strongly agree'",
    most_positive=5,
    most_negative=1,
)
likert_7_answer = database.create_answer_type(
    db=session,
    short_name="likert-7",
    description="scale of 7 units that ranges between the choices 'Very untrue of me' to 'Very true of me'",
    most_positive=7,
    most_negative=1,
)
free_text_answer = database.create_answer_type(
    db=session,
    short_name="free text",
    description="free text answers, won't be counted into calculation",
    most_positive=0,
    most_negative=0,
)
ans_type_04 = database.create_answer_type(
    db=session,
    short_name="likert-5 reverse",
    description="likert-5 scale with the lowest score for the most positive option",
    most_positive=1,
    most_negative=5,
)
ans_type_05 = database.create_answer_type(
    db=session,
    short_name="likert-7 reverse",
    description="likert-7 scale with the lowest score for the most positive option",
    most_positive=1,
    most_negative=7,
)
database.create_question_by_object(
    db=session,
    question="I would share my data.",
    answer_type=likert_5_answer,
)
database.create_question_by_object(
    db=session,
    question="I would not feel comfortable sharing my data.",
    answer_type=ans_type_04,
)
database.create_question_by_object(
    db=session,
    question="I would feel very tense with being asked to share data again in the future.",
    answer_type=ans_type_05,
)
database.create_question_by_object(
    db=session,
    question="I would feel better with the given incentive",
    answer_type=likert_7_answer,
)
database.create_question_by_object(
    db=session,
    question="Other feedback",
    answer_type=free_text_answer,
)

database.create_study(
    db=session,
    name="default",
    vignette_template="You have currently been employed for over a year in a company. $data_sharing $visibility $delivery_model $incentive",
)

database.add_vignette_factor(
    db=session,
    factor="data_sharing",
    levels={
        "1": "Your manager wants to know your age.",
        "2": "Your manager wants to know how much you weight.",
    },
)

database.add_vignette_factor(
    db=session,
    factor="visibility",
    levels={
        "true": "You will know how the data is used exactly.",
        "false": "You will not know how the data is used.",
    },
)

database.add_vignette_factor(
    db=session,
    factor="delivery_model",
    levels={
        "gift": "You will be given a gift for sharing that data.",
        "loss": "You will lose access if you don't share the data.",
    },
)

database.add_vignette_factor(
    db=session,
    factor="incentive",
    levels={
        "gift cards": "You will be given a gift card for sharing that data.",
        "training": "You will be given training to share that data.",
    },
)

del database

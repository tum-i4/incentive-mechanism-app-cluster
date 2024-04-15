"""Script to enter sample data into the database."""

from more_itertools import one

from agatha.backend.data_persistence.crud import DataAccessObject

database = DataAccessObject()

session = one(database())

d_model_01 = database.create_delivery_model(
    db=session,
    name="gift",
    description="Unconditional delivery of calculated incentive prior to data sharing requests",
)
d_model_02 = database.create_delivery_model(
    db=session,
    name="loss",
    description="Unconditional delivery of calculated incentive after data sharing request with availability notified in advance",
)
i_type_01 = database.create_incentive_type(
    db=session,
    name="gift cards",
    description="Gift card worth x euros, redeemable at some place y",
)
i_type_02 = database.create_incentive_type(
    db=session,
    name="training",
    description="Access to software or personalized coaching for self improvement",
)

employee_model_01 = database.create_employee_model_by_objects(
    db=session,
    delivery_model=d_model_01,
    incentive_type=i_type_02,
    revolori_id="test_id_01",
)
employee_model_02 = database.create_employee_model_by_objects(
    db=session,
    delivery_model=d_model_02,
    incentive_type=i_type_01,
    revolori_id="test_id_02",
)

likert_4_answer = database.create_answer_type(
    db=session,
    short_name="likert-4",
    description="Scale of 4 units that ranges between the choices 'Strongly disagree' to 'Strongly agree' with no neutral choice",
    most_positive=4,
    most_negative=1,
)
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
factor_01 = database.create_factor_by_objects(
    db=session,
    name="reciprocity",
    delivery_model=d_model_01,
)
factor_02 = database.create_factor_by_objects(
    db=session,
    name="losspositive",
    delivery_model=d_model_02,
)
factor_03 = database.create_factor_by_objects(
    db=session,
    name="autonomy",
    incentive_type=i_type_01,
)
factor_04 = database.create_factor_by_objects(
    db=session,
    name="relatedness",
    incentive_type=i_type_02,
)
question_01 = database.create_question_by_objects(
    db=session,
    question="I usually lend my belongings to other people (books, CDs etc)",
    weight=50,
    factor=factor_01,
    answer_type=likert_5_answer,
)
question_02 = database.create_question_by_objects(
    db=session,
    question="In general, one can trust people",
    weight=20,
    factor=factor_01,
    answer_type=ans_type_04,
)
question_03 = database.create_question_by_objects(
    db=session,
    question="I would feel very tense if the company changed our way of working",
    weight=30,
    factor=factor_02,
    answer_type=ans_type_04,
)
question_04 = database.create_question_by_objects(
    db=session,
    question="If I do something that is beneficial for someone else, then I expect that person to return a favor.",
    weight=40,
    factor=factor_02,
    answer_type=likert_7_answer,
)
question_05 = database.create_question_by_objects(
    db=session,
    question="Some other question.",
    weight=10,
    factor=factor_02,
    answer_type=ans_type_05,
)
question_06 = database.create_question_by_objects(
    db=session,
    question="I usually lend my belongings to other people (books, CDs etc)",
    weight=50,
    factor=factor_04,
    answer_type=likert_5_answer,
)
question_07 = database.create_question_by_objects(
    db=session,
    question="In general, one can trust people",
    weight=20,
    factor=factor_04,
    answer_type=ans_type_04,
)
question_08 = database.create_question_by_objects(
    db=session,
    question="I would feel very tense if the company changed our way of working",
    weight=30,
    factor=factor_03,
    answer_type=ans_type_04,
)
question_09 = database.create_question_by_objects(
    db=session,
    question="If I do something that is beneficial for someone else, then I expect that person to return a favor.",
    weight=40,
    factor=factor_03,
    answer_type=likert_7_answer,
)
question_10 = database.create_question_by_objects(
    db=session,
    question="Some other question as well.",
    weight=10,
    factor=factor_03,
    answer_type=ans_type_05,
)
question_11 = database.create_question_by_objects(
    db=session,
    question="What is your favorite food?",
    weight=10,
    factor=factor_01,
    answer_type=free_text_answer,
)
question_12 = database.create_question_by_objects(
    db=session,
    question="Some likert-4 question.",
    weight=10,
    factor=factor_03,
    answer_type=likert_4_answer,
)
survey_01 = database.create_survey(
    db=session,
    name="measure of reciprocity",
    description="Survey used to gauge the reciprocal, trust and lending behavior of individuals",
)
survey_02 = database.create_survey(
    db=session,
    name="measure of loss aversion",
    description="Survey used to gauge the risk and loss sensitivity of an individual",
)
survey_03 = database.create_survey(
    db=session,
    name="mechanism test survey",
    description="Survey used to test the functionality of mechanism calculation",
)
database.create_question_answer_by_objects(
    db=session,
    revolori_id="test_id_03",
    survey=survey_03,
    question=question_01,
    answer="2",
)
database.create_question_answer_by_objects(
    db=session,
    revolori_id="test_id_03",
    survey=survey_03,
    question=question_02,
    answer="4",
)
database.create_question_answer_by_objects(
    db=session,
    revolori_id="test_id_03",
    survey=survey_03,
    question=question_03,
    answer="2",
)
database.create_question_answer_by_objects(
    db=session,
    revolori_id="test_id_03",
    survey=survey_03,
    question=question_04,
    answer="3",
)
database.create_question_answer_by_objects(
    db=session,
    revolori_id="test_id_03",
    survey=survey_03,
    question=question_05,
    answer="3",
)
database.create_question_answer_by_objects(
    db=session,
    revolori_id="test_id_03",
    survey=survey_03,
    question=question_06,
    answer="2",
)
database.create_question_answer_by_objects(
    db=session,
    revolori_id="test_id_03",
    survey=survey_03,
    question=question_07,
    answer="4",
)
database.create_question_answer_by_objects(
    db=session,
    revolori_id="test_id_03",
    survey=survey_03,
    question=question_08,
    answer="2",
)
database.create_question_answer_by_objects(
    db=session,
    revolori_id="test_id_03",
    survey=survey_03,
    question=question_09,
    answer="3",
)
database.create_question_answer_by_objects(
    db=session,
    revolori_id="test_id_03",
    survey=survey_03,
    question=question_10,
    answer="3",
)
database.create_question_answer_by_objects(
    db=session,
    revolori_id="test_id_03",
    survey=survey_03,
    question=question_11,
    answer="icecream",
)
if survey_01.id and question_01.id:
    q_ans_01 = database.create_question_answer_by_q_id(
        db=session,
        revolori_id="test_id_01",
        answer="Strongly agree",
        survey_id=survey_01.id,
        question_id=question_01.id,
    )
database.add_question_to_survey(session, question_01, survey_01)
database.add_question_to_survey(session, question_02, survey_01)
database.add_question_to_survey(session, question_05, survey_01)
database.add_question_to_survey(session, question_11, survey_01)
database.add_question_to_survey(session, question_12, survey_01)
database.add_question_to_survey(session, question_02, survey_02)
database.add_question_to_survey(session, question_03, survey_02)

database.add_question_to_survey(session, question_01, survey_03)
database.add_question_to_survey(session, question_02, survey_03)
database.add_question_to_survey(session, question_03, survey_03)
database.add_question_to_survey(session, question_04, survey_03)
database.add_question_to_survey(session, question_05, survey_03)
database.add_question_to_survey(session, question_06, survey_03)
database.add_question_to_survey(session, question_07, survey_03)
database.add_question_to_survey(session, question_08, survey_03)
database.add_question_to_survey(session, question_09, survey_03)
database.add_question_to_survey(session, question_10, survey_03)

database.create_admin(
    db=session,
    email="zieglmev@in.tum.de",
)
database.create_admin(
    db=session,
    email="demo@example.com",
)

del database

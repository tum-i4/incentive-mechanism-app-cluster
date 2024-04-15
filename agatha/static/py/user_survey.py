"""Implements frontend logic for survey web app."""
import json
from typing import Dict

from browser import (  # type: ignore # pylint: disable=import-error
    ajax,
    alert,
    document,
    window,
)
from questions import QuestionHandler


class Survey(QuestionHandler):
    """Defines all functions to implement flow of survey."""

    def __init__(self, pagination: int, render_response: bool):
        """Initialize variables.

        Args:
            pagination: corresponds to the number of questions to be shown per page
            render_reponse: render the response HTML when handling the POST request
        """
        self.results: Dict[str, str] = {}
        """Answers to survey questions: q_id -> answer."""

        self.render_response = render_response
        self.pagination: int = pagination
        super().__init__(previous=True)

    @property
    def unit_width(self) -> float:
        """Compute unit width for progress bar."""
        return 100 / len(self.questions)

    @property
    def current_progress_count(self) -> int:
        """Compute current counter with addition of vignettes."""
        return len(self.results)

    def question_unanswered(self, q_id: str) -> bool:
        """Check if question id is in results."""
        return q_id not in self.results

    def ready_for_next_page(self, filled_out_active_questions):
        """Check if pagination limit is reached and mark ready for next page."""
        return len(filled_out_active_questions) == self.pagination

    def ready_to_submit(self, next_index):
        """Check if the user is ready to submit the survey."""
        return next_index >= len(self.questions)

    def handle_submission_response(self, event):
        """Post user answers.

        Args:
            event (browser.DOMEvent): event emitted from submit button click event.
        """
        if any(
            question.attrs["q_id"] not in self.results for question in self.questions
        ):
            alert("Please answer all questions before submitting.")
            return
        req = ajax.Ajax()
        req.bind("complete", self.on_complete)
        req.open("POST", window.location.href, True)
        req.set_header("content-type", "application/json")
        results_dict_list = [
            {"question_id": int(key), "answer": value}
            for key, value in self.results.items()
        ]
        json_results = json.dumps(results_dict_list)
        req.send(json_results)

    def on_complete(self, req: ajax):
        """Handle server response for the survey submission.

        If the submission was successful, show success message.
        Else, show failure message.

        Args:
            req: ajax request
        """
        if self.render_response:
            document.html = req.response
            return

        self.hide_active_questions()
        document["message"].style.display = "block"
        text_element = document["message"].children[0]
        if req.status == 204:
            text_element.text = "You have already submitted this survey."
        elif 200 <= req.status < 400:
            text_element.text = "Your answers have been submitted. Thank you."
        else:
            text_element.text = "Something went wrong. Please try again later"
        document["navigation"].style.display = "none"

    def handle_next_button(self, _):
        """Handle next button click by.

        Show next page.

        Assumptions:
        - At least one question to be active i.e. active_questions to have
        at least one element.
        - At least one question is after the last currently active question.
        """
        max_active_index = self.questions.index(self.active_questions[-1])
        self.hide_active_questions()
        new_start = max_active_index + 1
        new_end = min(new_start + self.pagination, len(self.questions))
        potential_next_active_questions = self.questions[new_start:new_end]
        self.show_element(potential_next_active_questions[0])
        for question in potential_next_active_questions:
            if question.attrs["q_id"] not in self.results:
                # question not filled out => don't show any more questions.
                break
            self.show_element(question)
        self.disable_button(self.next_button)
        self.update_question_display()

    def handle_previous_button(self, _):
        """Handle previous button click.

        Show the previous page.

        Assumptions:
        - At least one question is active
        """
        min_active_index = self.questions.index(self.active_questions[0])
        start = max(0, min_active_index - self.pagination)
        stop = min(len(self.questions), min_active_index)
        self.hide_active_questions()
        self.show_questions(self.questions[start:stop])
        self.replace_submit_with_next_button()
        self.update_question_display()

    def add_answer(self, answer: str, q_id: str):
        """Add user choice to results.

        Args:
            answer: Answer to be saved
            q_id: Id of question which gets answered

        Todo:
            * add post request for every answer (future goal)
        """
        self.results[q_id] = answer

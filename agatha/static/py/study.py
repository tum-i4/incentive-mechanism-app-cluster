"""Implements frontend logic for vignette web app for study."""
import json
from collections import defaultdict
from typing import Any, Dict

from browser import ajax, document, window  # type: ignore # pylint: disable=import-error
from questions import QuestionHandler


class Study(QuestionHandler):
    """Defines all functions to implement flow of vignette questionnaire in study."""

    def __init__(self):
        """Initialize variables."""
        self.results: defaultdict[Dict[str, Any]] = defaultdict(dict)
        """Answers to vignette questions: v_id -> q_id -> answer."""

        super().__init__()

    @property
    def vignettes(self):
        """All vignettes in the study."""
        return document.select(".vignette")

    @property
    def active_vignette(self):
        """Get current active vignette.

        Raises if there is more than one active vignette.
        """
        active_vignettes = [
            vignette
            for vignette in self.vignettes
            if "d-none" not in vignette.class_name
        ]
        if len(active_vignettes) > 1:
            raise ValueError("Only maximum one vignette should be active at a time.")
        return active_vignettes[0]

    @property
    def vignette_number(self):
        """Number of currently active vignette."""
        try:
            active_vignette = self.active_vignette
        except IndexError:
            return 0
        return self.vignettes.index(active_vignette) + 1

    @property
    def unit_width(self) -> float:
        """Compute unit width for progress bar."""
        return 100 / (len(self.questions) * len(self.vignettes))

    @property
    def current_progress_count(self) -> int:
        """Compute current counter with addition of vignettes."""
        return sum([len(questions) for questions in self.results.values()])

    def question_unanswered(self, q_id: str) -> bool:
        """Check if question id is in results."""
        return q_id not in self.results[self.active_vignette.attrs["v_id"]]

    def update_vignette_display(self):
        """Display next vignette and reset questions."""
        next_index = self.vignette_number
        try:
            self.hide_element(self.active_vignette)
        except IndexError:
            # No vignette to hide
            pass
        self.show_element(self.vignettes[next_index])

        self.update_question_display()

    def ready_to_submit(self, next_index) -> bool:
        """Check if all questions are answered.

        Returns:
            bool: True if all questions are answered, False otherwise.
        """
        return self.vignette_number == len(self.vignettes) and next_index >= len(
            self.questions
        )

    def ready_for_next_page(self, filled_out_active_questions) -> bool:
        """Check if next page button should be enabled."""
        return len(filled_out_active_questions) == len(self.questions)

    def handle_submission_response(self, event):
        """Post user answers.

        Args:
            event (browser.DOMEvent): event emitted from submit button click event.
        """
        req = ajax.Ajax()
        req.bind("complete", self.on_complete)
        req.open("POST", window.location.href, True)
        req.set_header("content-type", "application/json")

        results_dict_list = []
        for vignette_id, questions in self.results.items():
            for question_id, answer in questions.items():
                results_dict_list.append(
                    {
                        "vignette_id": vignette_id,
                        "question_id": int(question_id),
                        "answer": answer,
                    }
                )
        json_results = json.dumps(results_dict_list)
        req.send(json_results)

    def on_complete(self, req):
        """Handle server response for the study submission.

        If the submission was successful, show success message.
        Else, show failure message.

        Args:
            req (ajax): ajax request
        """
        self.reset_active_questions()
        document["message"].style.display = "block"
        self.hide_element(self.active_vignette)
        text_element = document["message"].children[0]
        if req.status == 204:
            text_element.text = "You have already submitted this study."
        elif 200 <= req.status < 400:
            text_element.text = "Your answers have been submitted. Thank you."
        else:
            text_element.text = "Something went wrong. Please try again later"
        document["navigation"].style.display = "none"

    def reset_active_questions(self):
        """Reset all questions and their buttons for next vignette."""
        for active_question in self.active_questions:
            self.hide_element(active_question)

            for neighbor_button in filter(
                lambda nb: "active" in nb.classList,
                document.select(".choice-button"),
            ):
                neighbor_button.classList.remove("hover")
                neighbor_button.classList.remove("active")

            for text_input in document.select(".text-input"):
                text_input.value = ""

    def handle_next_button(self, _):
        """Handle next button click by showing next page."""
        self.disable_button(self.next_button)
        self.reset_active_questions()
        self.update_vignette_display()

    def add_answer(self, answer: str, q_id: str):
        """Add user choice to results."""
        self.results[self.active_vignette.attrs["v_id"]][q_id] = answer

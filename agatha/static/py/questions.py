"""Implements frontend logic for showing questions."""
from abc import abstractmethod
from typing import List

from browser import document, html  # type: ignore # pylint: disable=import-error


class QuestionHandler:
    """Defines functionality to show questions."""

    def __init__(self, previous=False):
        """Initialize variables.

        Args:
            previous: if True, bind previous button to enable going back a page.
        """
        for button in document.select(".choice-button"):
            button.bind("click", self.handle_likert_answer)
        for text_input in document.select(".text-input"):
            text_input.bind("focus", self.handle_text_answer)
            text_input.bind("input", self.handle_text_answer)
        if previous:
            self.previous_button.bind("click", self.handle_previous_button)
        self.next_button.bind("click", self.handle_next_button)
        self.submit_button.bind("click", self.handle_submission_response)

    @property
    def questions(self) -> List[html.DIV]:
        """All questions which are defined in html."""
        return document.select(".question")

    @property
    def active_questions(self) -> List[html.DIV]:
        """All questions which are currently being shown."""
        return [
            question
            for question in self.questions
            if "d-none" not in question.class_name
        ]

    @property
    def next_button(self) -> html.DIV:
        """Next button."""
        return document["next"]

    @property
    def submit_button(self) -> html.DIV:
        """Submit button."""
        return document["submit"]

    @property
    def previous_button(self) -> html.DIV:
        """Previous button."""
        return document["previous"]

    @property
    @abstractmethod
    def unit_width(self) -> float:
        """Get unit width for progress bar."""

    @property
    @abstractmethod
    def current_progress_count(self) -> int:
        """Get current progress count."""

    @abstractmethod
    def handle_submission_response(self, event):
        """Post user answers.

        Args:
            event (browser.DOMEvent): event emitted from submit button click event.
        """

    @abstractmethod
    def handle_next_button(self, _):
        """Handle next button click to show next page."""

    @abstractmethod
    def ready_for_next_page(self, filled_out_active_questions):
        """Check if next page button should be enabled."""

    @abstractmethod
    def ready_to_submit(self, next_index):
        """Check if the user is ready to submit the answers."""

    @abstractmethod
    def question_unanswered(self, q_id: str) -> bool:
        """Check if question id is in results."""

    @abstractmethod
    def add_answer(self, answer: str, q_id: str):
        """Add user answer to results."""

    def hide_element(self, elem):
        """Hide element."""
        elem.class_name = elem.class_name.replace("d-block", "d-none")

    def show_element(self, elem):
        """Show element."""
        elem.class_name = elem.class_name.replace("d-none", "d-block")

    def show_questions(self, questions: List[html.DIV]):
        """Make the given questions visible to the user."""
        for new_active_question in questions:
            self.show_element(new_active_question)

    def enable_button(self, button: html.DIV):
        """Enable the given button."""
        if button.attrs.get("disabled", None) is not None:
            del button.attrs["disabled"]

    def disable_button(self, button: html.DIV):
        """Disable the given button."""
        button.attrs["disabled"] = ""

    def show_button(self, button: html.DIV):
        """Show the given button."""
        button.style.display = "inline-block"

    def hide_button(self, button: html.DIV):
        """Hide the given button."""
        button.style.display = "none"

    def replace_next_with_submit_button(self):
        """Hide next button and show submit button."""
        self.hide_button(self.next_button)
        self.show_button(self.submit_button)

    def replace_submit_with_next_button(self):
        """Hide submit butt and show next button."""
        self.hide_button(self.submit_button)
        self.show_button(self.next_button)

    def handle_likert_answer(self, event):
        """Update results with the given answer and update the UI accordingly.

        If the button click event corresponds to a change of answer
        for the same question, next question will not be displayed.

        Args:
            event (browser.DOMEvent): click event triggered from answer button.
        """
        button = event.currentTarget
        self.activate_button(button)
        self.add_answer(button.html, button.attrs["q_id"])
        self.update_question_display()
        self.update_progress_bar()

    def handle_text_answer(self, event):
        """Update results with the given answer and update the UI accordingly.

        Args:
            event (browser.DOMEvent): click event triggered from answer button.
        """
        button = event.currentTarget
        q_id = button.attrs["q_id"]
        text_input = next(
            input_field
            for input_field in document.select(".text-input")
            if input_field.attrs["q_id"] == q_id
        )
        self.add_answer(text_input.value, q_id)
        self.update_progress_bar()
        self.update_question_display()

    def enable_previous_button_if_possible(self):
        """Enable previous button if possible."""
        try:
            try:
                first_active_question = self.active_questions[0]
                if self.questions.index(first_active_question) == 0:
                    self.disable_button(self.previous_button)
                else:
                    self.enable_button(self.previous_button)
            except IndexError:
                self.disable_button(self.previous_button)
        except KeyError:
            # previous button does not exist
            pass

    def update_question_display(self):
        """Update the website UI to display the new state.

        Does nothing if any question currently displayed is not answered.
        Enables the next button if the maximum amount of questions per page is answered.
        Enables the submit button if all questions are answered.
        Else, shows the next question.
        """
        self.enable_previous_button_if_possible()
        # check if all active questions are filled out:
        if any(
            self.question_unanswered(question.attrs["q_id"])
            for question in self.active_questions
        ):
            # some active question is still not filled out => do nothing
            self.disable_button(self.next_button)
            return
        # All active questions are filled out
        filled_out_active_questions = [
            question
            for question in self.active_questions
            if not self.question_unanswered(question.attrs["q_id"])
        ]
        # get next question to display
        try:
            last_active_question = self.active_questions[-1]
            index = self.questions.index(last_active_question) + 1
        except IndexError:
            # No currently active question => show first question
            index = 0
        # check if ready to submit or ready for next page
        if self.ready_to_submit(index):
            self.replace_next_with_submit_button()
            return
        if self.ready_for_next_page(filled_out_active_questions):
            # Pagination limit reached => Activate next button and don't show another question
            self.enable_button(self.next_button)
            return
        # Display the next question
        self.show_element(self.questions[index])

    def activate_button(self, button):
        """Activate button hover state.

        Args:
            button (browser.html.BUTTON): button DOM element object
        """
        neighbors = button.parent.children
        for neighbor_button in filter(lambda nb: "active" in nb.classList, neighbors):
            neighbor_button.classList.remove("hover")
            neighbor_button.classList.remove("active")

        button.classList.remove("hover")
        button.classList.add("active")

    def hide_active_questions(self):
        """Set currently active questions display to none."""
        for active_question in self.active_questions:
            self.hide_element(active_question)

    def handle_previous_button(self, _):
        """Handle previous button click.

        Has to be overwritten by subclass, only if previous is enabled.
        """
        pass

    def update_progress_bar(self):
        """Update the progress bar with the given answers."""
        progress_bar = document.select_one("#progress-bar")
        progress_bar.style.width = f"{self.unit_width * self.current_progress_count}%"

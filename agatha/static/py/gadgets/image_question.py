"""Script for individual configuration page in configuration app."""

from browser import alert, document  # type: ignore # pylint: disable=import-error


def incorrect_choice_selected(event):
    """Behavior for incorrect choice."""
    alert("incorrect")


def correct_choice_selected(event):
    """Behavior for correct choice."""
    alert("correct")


def bind_button_events():
    """Bind button click events."""
    correct_choice = document.select(".correct")
    incorrect_choices = document.select(".incorrect")
    correct_choice[0].bind("click", correct_choice_selected)
    for choice_btn in incorrect_choices:
        choice_btn.bind("click", incorrect_choice_selected)


if __name__ == "__main__":
    bind_button_events()

"""Script for individual configuration page in configuration app."""

from browser import document  # type: ignore # pylint: disable=import-error
from logout import bind_logout_event


def reset_selected_options():
    """Update selected option class names."""
    selected_options = document.select(".selected")
    for option in selected_options:
        option.selected = True


def toggle_edit_modal(event):
    """Toggle the visibility of edit modals.

    Args:
       event: mouse event triggered by click on configure button
    """
    _, revolori_id = event.target.id.split("-")
    item_modal = document[f"modal-{revolori_id}"]
    if "show" in item_modal.class_name:
        item_modal.class_name = "modal fade"
        item_modal.style.display = "none"
        reset_selected_options()
    else:
        item_modal.class_name = "modal fade shadow show"
        item_modal.style.display = "block"
        item_modal.style.background = "#00000055"
        item_modal.select(".modal-content")[0].style.width = "500px"


def bind_button_events():
    """Bind button click events on employees page."""
    toggle_btns = document.select(".toggle-btn")
    for toggle_btn in toggle_btns:
        toggle_btn.bind("click", toggle_edit_modal)


if __name__ == "__main__":
    reset_selected_options()
    bind_button_events()
    bind_logout_event()

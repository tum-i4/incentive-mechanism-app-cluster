"""Scripts for mechanism page in configuration app."""

from browser import document  # type: ignore # pylint: disable=import-error
from logout import bind_logout_event


def toggle_accordion(event):
    """Toggle accordion expand & collapse.

    Args:
        event: event triggered by click on accordion header
    """
    category, _, item_id = event.target.id.split("-")
    accordion_body = document[f"{category}-body-{item_id}"]
    if "show" in accordion_body.class_name:
        accordion_body.class_name = "accordion-collapse collapse"
        event.target.class_name = "accordion-button collapsed"
    else:
        accordion_body.class_name = "accordion-collapse collapse show"
        event.target.class_name = "accordion-button"


def bind_accordion_headers():
    """Bind accordion header click events to be collapsible."""
    accordion_headers = document.select(".accordion-header")
    for accordion_header in accordion_headers:
        accordion_header.bind("click", toggle_accordion)


def toggle_modal(event):
    """Toggle the visibility of edit modals.

    Args:
       event: event triggered by click on cancel/edit button
    """
    event.stopPropagation()
    category, _, item_id = event.target.id.split("-")

    item_modal_id = f"{category}-modal"
    if item_id:
        item_modal_id += f"-{item_id}"

    item_modal = document[item_modal_id]

    if "show" in item_modal.class_name:
        item_modal.class_name = "modal fade"
        item_modal.style.display = "none"
    else:
        item_modal.class_name = "modal fade shadow show"
        item_modal.style.display = "block"
        item_modal.style.background = "#00000055"
        item_modal.select(".modal-content")[0].style.width = "500px"


def bind_modal_events():
    """Bind model related events."""
    toggle_btns = document.select(".toggle-btn")
    for toggle_btn in toggle_btns:
        toggle_btn.bind("click", toggle_modal)


if __name__ == "__main__":
    bind_accordion_headers()
    bind_modal_events()
    bind_logout_event()

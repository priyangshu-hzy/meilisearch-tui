from __future__ import annotations

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Input, Label, Static

from meilisearch_tui.widgets.messages import ErrorMessage


class InputWithLabel(Widget):
    DEFAULT_CSS = """
    InputWithLabel {
        height: auto;
    }
    """

    def __init__(
        self,
        *,
        label: str,
        input_id: str,
        error_id: str,
        error_message: str = "",
        password: bool = False,
    ) -> None:
        self.label = label
        self.input_id = input_id
        self.error_id = error_id
        self.error_message = error_message
        self.password = password
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Label(self.label)
        yield Input(id=self.input_id, password=self.password)
        yield ErrorMessage(self.error_message, id=self.error_id)

    def on_input_changed(self, value: Input.Changed) -> None:
        if value:
            self.query_one(f"#{self.error_id}", Static).visible = False
        else:
            self.query_one(f"#{self.error_id}", Static).visible = True

    def on_mount(self) -> None:
        self.query_one(f"#{self.error_id}", Static).visible = False

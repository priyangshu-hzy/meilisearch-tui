from __future__ import annotations

import asyncio
from pathlib import Path

from meilisearch_python_async.errors import (
    MeilisearchApiError,
    MeilisearchCommunicationError,
    MeilisearchError,
)
from textual import events
from textual.app import ComposeResult
from textual.containers import Center, Container
from textual.screen import Screen
from textual.widgets import Button, DirectoryTree, Footer, Input, Static

from meilisearch_tui.client import get_client
from meilisearch_tui.widgets.index import CurrentIndexes
from meilisearch_tui.widgets.input import InputWithLabel
from meilisearch_tui.widgets.messages import ErrorMessage, SuccessMessage


class DataLoadScreen(Screen):
    def compose(self) -> ComposeResult:
        """Compose our UI."""
        with Container(id="body"):
            yield DirectoryTree(Path.home(), id="tree-view")
            yield InputWithLabel(
                label="Index",
                input_id="index",
                error_id="index_error",
                error_message="An index is require",
            )
            yield InputWithLabel(
                label="File Path",
                input_id="data_file",
                error_id="data_file_error",
                error_message="A Path to a json, jsonl, or csv file is required",
            )
            with Center():
                yield Button(label="Index File", id="index_button")
            yield SuccessMessage(
                "Data successfully sent for indexing",
                classes="message-centered",
                id="indexing_successful",
            )
            yield ErrorMessage("", classes="message-centered", id="indexing_error")
            yield CurrentIndexes()
        yield Footer()

    async def on_mount(self) -> None:
        index_name = self.query_one("#index", Input)
        async with get_client() as client:
            indexes = await client.get_indexes()

        if indexes:
            index_name.value = indexes[0].uid
            self.query_one(DirectoryTree).focus()
        else:
            index_name.focus()

        self.query_one("#indexing_successful", Static).visible = False
        self.query_one("#indexing_error", Static).visible = False

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """Called when the user click a file in the directory tree."""
        event.stop()
        code_view = self.query_one("#data_file", Input)
        try:
            code_view.value = event.path
        except Exception:
            raise

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        error = False

        if button_id == "index_button":
            data_file = self.query_one("#data_file", Input).value
            index_name = self.query_one("#index", Input).value

            if not data_file or Path(data_file).suffix not in (".csv", ".json", ".jsonl"):
                self.query_one("#data_file_error", Static).visible = True
                error = True
            if not index_name:
                self.query_one("#index_error", Static).visible = True
                error = True

            if error:
                return None

            data_file_path = Path(data_file)
            try:
                async with get_client() as client:
                    index = client.index(index_name)
                    if data_file_path.suffix == ".json":
                        await index.add_documents_from_file_in_batches(data_file_path)
                    else:
                        await index.add_documents_from_raw_file(data_file_path)
                asyncio.create_task(self._success_message())
            except MeilisearchApiError as e:
                asyncio.create_task(self._error_message(f"{e}"))
            except MeilisearchCommunicationError as e:
                asyncio.create_task(self._error_message(f"{e}"))
            except MeilisearchError as e:
                asyncio.create_task(self._error_message(f"{e}"))
            except Exception as e:
                asyncio.create_task(self._error_message(f"An unknown error occured error: {e}"))

    def on_key(self, event: events.Key) -> None:
        if event.key == "enter":
            self.query_one("#index_button", Button).press()

    async def _success_message(self) -> None:
        success = self.query_one("#indexing_successful", Static)
        success.visible = True
        await asyncio.sleep(5)
        success.visible = False

    async def _error_message(self, message: str) -> None:
        error = self.query_one("#indexing_error", Static)
        error.renderable = message
        error.visible = True
        await asyncio.sleep(5)
        error.visible = False
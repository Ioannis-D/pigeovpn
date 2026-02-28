"""
Widgets and Screens that set up the credentials and the directory of the .ovpn files.
"""

import os
import json
from textual.app import ComposeResult, App
from textual.containers import Grid, Center, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Label, Input, Button
from textual.message import Message

from pathlib import Path

from pigeovpn.constants import CREDS_FILE, JSON_CONF
from pigeovpn.setup import (
    setup_credentials,
    setup_ovpnDirectory,
    update_showing_settings,
)


class PathAutocompleteInput(Input):
    """Input with Tab completion for existing directories."""

    BINDINGS = [
        ("tab", "complete_path", "Complete path"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._completion_source: str | None = None
        self._completion_candidates: list[str] = []
        self._completion_index: int = -1
        self._suppress_programmatic_change_event: bool = False

    def on_input_changed(self, event: Input.Changed) -> None:
        if self._suppress_programmatic_change_event:
            self._suppress_programmatic_change_event = False
            return
        self._reset_completion()

    def action_complete_path(self) -> None:
        raw_value = self.value

        should_rebuild = False
        if not self._completion_candidates:
            should_rebuild = True
        elif (
            raw_value != self._completion_source
            and raw_value not in self._completion_candidates
        ):
            # User edited the input after completion cycle started; rebuild candidates.
            should_rebuild = True

        if should_rebuild:
            self._completion_candidates = self._find_directory_candidates(raw_value)
            self._completion_source = raw_value
            self._completion_index = -1

        if not self._completion_candidates:
            self.app.bell()
            return

        self._completion_index = (self._completion_index + 1) % len(
            self._completion_candidates
        )
        next_value = self._completion_candidates[self._completion_index]

        self._suppress_programmatic_change_event = True
        self.value = next_value
        self.cursor_position = len(next_value)

    def _reset_completion(self) -> None:
        self._completion_source = None
        self._completion_candidates = []
        self._completion_index = -1

    def _find_directory_candidates(self, user_value: str) -> list[str]:
        if not user_value:
            return []

        if user_value in ("~", "~/"):
            parent = Path.home()
            prefix = ""
            source_parent = user_value
        elif user_value.endswith("/"):
            parent = Path(os.path.expanduser(user_value))
            prefix = ""
            source_parent = user_value.rstrip("/")
        else:
            source_parent = os.path.dirname(user_value)
            prefix = os.path.basename(user_value)
            parent = Path(os.path.expanduser(source_parent or "."))

        try:
            if not parent.exists() or not parent.is_dir():
                return []
            children = [item for item in parent.iterdir() if item.is_dir()]
        except OSError:
            return []

        matches = [item for item in children if item.name.startswith(prefix)]
        matches.sort(key=lambda item: item.name.lower())

        return [self._display_path(item, user_value, source_parent) for item in matches]

    def _display_path(self, path: Path, original: str, source_parent: str) -> str:
        path_str = str(path)

        if original.startswith("~"):
            home = str(Path.home())
            if path_str == home:
                return "~"
            if path_str.startswith(home + "/"):
                return "~/" + path_str[len(home) + 1 :]
            return path_str

        if original.startswith("/"):
            return path_str

        if source_parent:
            parent_value = source_parent.rstrip("/")
            return f"{parent_value}/{path.name}" if parent_value else path.name

        return path.name


# ------------------------
# Directory of .ovpn files
# ------------------------


class DirectoryAskForm(Grid):
    """
    The form that asks the user to insert the directory where the .ovpn files are.

    It is later used in a ModalScreen.
    """

    class Submitted(Message):
        def __init__(
            self, directory_path: str | Path, should_update: bool = True
        ) -> None:
            super().__init__()
            self.directory_path = directory_path
            self.should_update = should_update

    def compose(self) -> ComposeResult:
        yield Label(
            "[b]Where are the ovpn files located?[/b]", id="ovpnDirectory-label"
        )
        yield PathAutocompleteInput(
            placeholder="path (Enter to cancel)", id="ovpnDirectory-path"
        )
        yield Center(
            Button("Confirm Directory", variant="primary", id="ovpnDirectory-button")
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ovpnDirectory-button":
            self._submit_directory()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "ovpnDirectory-path":
            event.stop()
            self._submit_directory()

    def _get_configured_ovpn_directory(self) -> Path | None:
        try:
            with open(JSON_CONF, "r") as file:
                config = json.load(file)
        except (OSError, json.JSONDecodeError):
            return None

        configured_dir = str(config.get("ovpn_directory", "")).strip()
        if not configured_dir or configured_dir == ".":
            return None

        configured_path = Path(configured_dir).expanduser()
        return configured_path if configured_path.is_dir() else None

    def _submit_directory(self) -> None:
        raw_value = self.query_one("#ovpnDirectory-path", Input).value.strip()

        # Empty input or "." means "keep current configured directory".
        if raw_value in {"", "."}:
            configured_path = self._get_configured_ovpn_directory()
            if configured_path is None:
                self.notify(
                    "Please give an existing and valid directory",
                    title="Directory required",
                    severity="error",
                    timeout=3,
                )
                return
            self.post_message(self.Submitted(str(configured_path), should_update=False))
            return

        directory_path = Path(raw_value).expanduser()  # Include also paths with ~
        if directory_path.is_dir():
            # Convert it to string, because json does not support PosixPath type.
            self.post_message(self.Submitted(str(directory_path), should_update=True))
        else:
            self.notify(
                "Please give an existing and valid directory",
                title="Directory not found",
                severity="error",
                timeout=3,
            )


class DirectoryInsertScreen(ModalScreen):
    """Screen which asks for the directory where the .ovpn files are stored."""

    CSS_PATH = "tui.css"

    def compose(self) -> ComposeResult:
        yield DirectoryAskForm(id="directoryask_screen")

    def on_directory_ask_form_submitted(
        self, event: DirectoryAskForm.Submitted
    ) -> None:
        directory_path = event.directory_path
        should_update = event.should_update

        if should_update:
            setup_ovpnDirectory(directory_path)  # Modify the directory in the json file

        # Change the conf.json so that the 'show_settings' is false
        # This is used for the first run of the app
        # It is assumed that the user will not press the button to switch directories very often
        # So the writing of the file (which 'costs' some time) is not something to worry about
        update_showing_settings()

        if should_update:
            self.notify(
                directory_path, title="Directory established", severity="information"
            )
        else:
            self.notify(
                directory_path, title="Directory unchanged", severity="information"
            )

        # Return update flag so main screen reload happens only when needed.
        self.dismiss(should_update)


# ------------------------
# Credentials (VPN provider)
# ------------------------


class CredentialsForm(Grid):
    """
    The form that asks the user for the username and password of the VPN provider.

    It is later used in a ModalScreen.
    """

    def __init__(self, show_cancel_button, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.show_cancel_button = show_cancel_button

    class Submitted(Message):
        def __init__(self, username: str, password: str) -> None:
            super().__init__()
            self.username = username
            self.password = password

    def compose(self) -> ComposeResult:
        yield Label("[b]Insert your credentials[/b]", id="credentials-label")
        yield Input(placeholder="username", id="credentials-username")
        yield Input(placeholder="password", password=True, id="credentials-password")
        if self.show_cancel_button:
            yield Horizontal(
                Center(
                    Button("Cancel", variant="default", id="credentials-cancel-button")
                ),
                Center(Button("Login", variant="primary", id="credentials-button")),
            )
        else:
            yield Center(Button("Login", variant="primary", id="credentials-button"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "credentials-button":
            username = self.query_one("#credentials-username", Input).value.strip()
            password = self.query_one("#credentials-password", Input).value

            if username and password:
                self.post_message(self.Submitted(username, password))
            else:
                self.notify(
                    "Give both username and password",
                    title="Warning",
                    severity="error",
                    timeout=3,
                )

        if event.button.id == "credentials-cancel-button":
            """
            Cancel button just cancels the process of re-login by poping the screen.
            """
            self.app.pop_screen()


class LoginCredentialsScreen(ModalScreen):
    """
    Screen wich asks for the username and the password of the VPN provider.
    """

    CSS_PATH = "tui.css"

    def __init__(self, show_cancel_button: bool = True):
        """
        When is the first time the app is run, the user is obligated to give the credentials.
        If the user pushes the 'Logout' button from the main screen, the option of canceling the insertion of new credentials is given with the Cancel button.
        """
        super().__init__()
        self.show_cancel_button = show_cancel_button

    def compose(self) -> ComposeResult:
        yield CredentialsForm(
            id="credentials_screen", show_cancel_button=self.show_cancel_button
        )

    def on_credentials_form_submitted(self, event: CredentialsForm.Submitted) -> None:
        username = event.username
        password = event.password

        return_code = setup_credentials(username, password)
        if not return_code == 0:
            self.notify(
                f"Please manually create it ({CREDS_FILE})",
                title="Error creating credentials",
                severity="error",
                timeout=10,
            )
        else:
            notification_message = f"{username}\n{len(password)*'*'}"
            self.notify(
                notification_message,
                title="Credentials created",
                severity="information",
            )

        self.dismiss()

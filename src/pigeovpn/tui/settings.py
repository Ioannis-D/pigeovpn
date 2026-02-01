"""
    Widgets and Screens that set up the credentials and the directory of the .ovpn files.
"""

from textual.app import ComposeResult, App
from textual.containers import Grid, Center, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Label, Input, Button
from textual.message import Message

from pathlib import Path

from pigeovpn.constants import CREDS_FILE
from pigeovpn.setup import setup_credentials, setup_ovpnDirectory, update_showing_settings


# ------------------------
# Directory of .ovpn files
# ------------------------

class DirectoryAskForm(Grid):
    """
    The form that asks the user to insert the directory where the .ovpn files are.

    It is later used in a ModalScreen.
    """
    class Submitted(Message):
        def __init__(self, directory_path: str | Path) -> None:
            super().__init__()
            self.directory_path = directory_path

    def compose(self) -> ComposeResult:
        yield Label("[b]Where are the ovpn files located?[/b]", id="ovpnDirectory-label")
        yield Input(placeholder="path", id="ovpnDirectory-path")
        yield Center(Button("Confirm Directory", variant="primary", id="ovpnDirectory-button"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ovpnDirectory-button":
            directory_path = self.query_one("#ovpnDirectory-path", Input).value
            directory_path = Path(directory_path).expanduser() # Include also paths with ~

            if directory_path.is_dir():
                directory_path = str(directory_path) # Convert it to string, because json does not support PosixPath type.
                self.post_message(self.Submitted(directory_path))
            else:
                self.notify(
                        "Please give an existing and valid directory",
                        title = "Directory not found",
                        severity = "error",
                        timeout = 3,
                )

class DirectoryInsertScreen(ModalScreen):

    """Screen which asks for the directory where the .ovpn files are stored."""

    CSS_PATH = "tui.css"

    def compose(self) -> ComposeResult:
        yield DirectoryAskForm(id="directoryask_screen")

    def on_directory_ask_form_submitted(self, event: DirectoryAskForm.Submitted) -> None:
        directory_path = event.directory_path

        setup_ovpnDirectory(directory_path) # Modify the directory in the json file


        # Change the conf.json so that the 'show_settings' is false
        # This is used for the first run of the app
        # It is assumed that the user will not press the button to switch directories very often
        # So the writing of the file (which 'costs' some time) is not something to worry about
        update_showing_settings()

        # Show notification that the directory has been added
        self.notify(
                directory_path,
                title = "Directory established",
                severity = "information"
                )
        # Dismiss the screen to return True for the new push of the MainScreen
        self.dismiss(True)  


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
                Center(Button("Cancel", variant="default", id="credentials-cancel-button")),
                Center(Button("Login", variant="primary", id="credentials-button"))
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
                        title = "Warning",
                        severity = "error",
                        timeout = 3,
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
        yield CredentialsForm(id="credentials_screen", show_cancel_button = self.show_cancel_button)

    def on_credentials_form_submitted(self, event: CredentialsForm.Submitted) -> None:
        username = event.username
        password = event.password

        return_code = setup_credentials(username, password)
        if not return_code == 0:
            self.notify(
                    f"Please manually create it ({CREDS_FILE})",
                    title = "Error creating credentials",
                    severity = "error",
                    timeout = 10
                    )
        else:
            notification_message = f"{username}\n{len(password)*'*'}"
            self.notify(
                    notification_message,
                    title = "Credentials created",
                    severity = "information"
                    )

        self.dismiss()            

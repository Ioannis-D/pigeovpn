from typing import Callable, Iterable, Optional
from pathlib import Path
import time
import psutil

from textual import on
from textual.screen import Screen
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Container
from textual.widgets import Footer, Input, Static, Button
from textual.widget import Widget
from textual.reactive import reactive

from pigeovpn.constants import OVPN_FILES_DIR, ASCII_art, UPDATE_DELAY, get_ovpnFilesDir
from pigeovpn.setup import check_showing_settings
from pigeovpn.tui.directorytree import DirectoryPane
from pigeovpn.tui.statics import update_ip_info, ButtonChangeDirectory, ButtonIP, ButtonShutDown, ButtonLogOut, ButtonGithubPage, InfoPane, SmartAscii
from pigeovpn.tui.graph import NetworkUsage
from pigeovpn.tui.settings import DirectoryInsertScreen, LoginCredentialsScreen
from pigeovpn.tui.welcome import WelcomeScreen


# -----------------------------------------------------------
# MainScreen - The main app
# -----------------------------------------------------------

class MainScreen(Screen):

    def __init__(self, ovpn_files_path: str | Path = OVPN_FILES_DIR):
        super().__init__()
        self.ovpn_files_path = ovpn_files_path

    #def on_mount(self) -> None:
        # Run IP update once the UI is mounted
        #update_ip_info(self, "#ip-pane", InfoPane)

    def compose(self) -> ComposeResult:
        yield Horizontal(
            # Right pane
            DirectoryPane(self.ovpn_files_path), # The left pane, which shows the .ovpn files from the selected directory

            Vertical(
                # 1) ASCII art always on top
                SmartAscii(ASCII_art, fallback="[b]OpenVPN Selector[/b]", id="app-title"),

                # 2) Bottom block (selected file, IP info, graphs)
                Vertical(
                    InfoPane("No .ovpn file selected", "info-pane"), # Shows the last selected .ovpn file
                    Horizontal(
                        InfoPane("Without IP info", "ip-pane"), # Shows IP address, city, country. Doesn't update when the app is started, but when a file is selected or the button is pressed 
                        ButtonIP("Refresh IP info", variant="primary", id="button-refresh-ip"),
                        id="ip-info-pane",
                    ),

                    NetworkUsage(window_seconds=60, id="net-usage"), # The graph which also includes the current speed and the data downloaded and uploaded during the run
                    Horizontal(
                        Container(ButtonShutDown("Shut down", variant="error", id="button-shutdown"), id="button-shutdown-container"),
                        Container(ButtonLogOut("Logout", variant="primary", id="button-logout"), id="button-logout-container"),
                        Container(ButtonChangeDirectory("Directory", variant="primary", id="button-change-directory"), id="button-change-directory-container"),
                        Container(ButtonGithubPage("?", variant="default", disabled=False, flat=False, id="button-github"), id="button-github-container"),
                        id="bottom-button-area"
                        ),
                    id="bottom-info",
                ),
                id="right-pane",
            ),
            id="main-container",
        )
        yield Footer()


# -----------------------------------------------------------
# PigeovpnApp — Top-level app combining left & right panels
# -----------------------------------------------------------
class PigeovpnApp(App):
    CSS_PATH = "tui/tui.css"
    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self):
       super().__init__()
       

    def check_pop_screen(self, pop: bool | None) -> None:
        """
        This function is used for the WelcomeScreen, to distinguish when the screen should be poped or should just open the GitHub repo.
        """
        if pop:
            self.pop_screen()

    def update_main_screen(self, update: bool | None) -> None:
        """
        This function is used for the DirectoryInsertScreen at which the user gives the directory of the .ovpn files.
        When a new path is given, we want the DirectoryTree to be immediately updated with the new path.
        
        To achieve this, we re-push (or just push when is the first time the app is run) the screen 'MainScreen'. 
        With this way, a 'new' updated screen is added. 
        As 'pop_screen' doesn't accept a specific screen as an attr, for clarity and easiness of the code, poping the 'old' MainScreen isn't done. 
        So the 'old' MainScreen is still working on the background.
        It is assumed that the user will not change directories multiple times in a run, which could create a big stack of MainScreen screens.
        With this way, we avoid the use of checking if a screen is stacked, and switching between screens to pop the MainScreen that is not updated.
        """
        OVPN_FILES_DIR = get_ovpnFilesDir() # Update the path with the new directory provided

        if update:
            self.push_screen(MainScreen(OVPN_FILES_DIR))

    def on_mount(self) -> None:
        if check_showing_settings(): # The first time the app is run, show the welcome/settings page
            """
            Push all the screens for the setting setup.
            When a screen is done, pop it or dismiss it.
            """
            self.push_screen(DirectoryInsertScreen(), self.update_main_screen)
            self.push_screen(LoginCredentialsScreen(show_cancel_button=False))
            self.push_screen(WelcomeScreen(), self.check_pop_screen)
        else:
            self.push_screen(MainScreen())


def pigeovpn():
    app = PigeovpnApp()
    app.run()

if __name__ == "__main__":
    pigeovpn()

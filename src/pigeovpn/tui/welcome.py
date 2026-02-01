"""
    The welcome page. 
    It is only shown the first time the app is run.
"""

from textual.app import ComposeResult, App
from textual.screen import Screen
from textual.widgets import Static, Button
from textual.containers import Container, Horizontal, Grid

from pigeovpn.constants import APP_NAME, ASCII_art, GITHUB_REPO  
from pigeovpn.tui.statics import ButtonGithubPage
from pigeovpn.external_commands import open_url_browser

class WelcomeScreen(Screen):
    CSS_PATH = "tui.css"

    def compose(self) -> ComposeResult:
        with Container(id="welcomePage-statics-container"):
            yield Static(
                    r"""
 __     __     ______     __         ______     ______     __    __     ______        ______   ______    
/\ \  _ \ \   /\  ___\   /\ \       /\  ___\   /\  __ \   /\ "-./  \   /\  ___\      /\__  _\ /\  __ \   
\ \ \/ ".\ \  \ \  __\   \ \ \____  \ \ \____  \ \ \/\ \  \ \ \-./\ \  \ \  __\      \/_/\ \/ \ \ \/\ \  
 \ \__/".~\_\  \ \_____\  \ \_____\  \ \_____\  \ \_____\  \ \_\ \ \_\  \ \_____\       \ \_\  \ \_____\ 
  \/_/   \/_/   \/_____/   \/_____/   \/_____/   \/_____/   \/_/  \/_/   \/_____/        \/_/   \/_____/ 
                                                                                                         
                    """,
                    id = "welcomePage-welcomeToAscii"
                    )

            yield Static(
                    ASCII_art,
                    id = "welcomePage-OpenVPNSelectorAscii"
                    )

        with Container(id="welcomePage-AppInfo-container"):
            yield Static(
                    f"""
[b]{APP_NAME}[/b] is a VPN app for the OpenVPN protocol. 
It is made for Linux and it works with whichever provider, as it directly uses the [i].ovpn[/i] files.

License: GNU General Public License v3.0
                    """,
                    id="welcomePage-AppInfo-text"
                    )

        with Grid(id="welcomePage-button-container"):
            yield ButtonGithubPage(
                    label = "Github repository",
                    variant="default",
                    id = "button-welcomePage-GithubPage",
                    flat = True
                    )

            yield Button(
                    "Continue with the setup ->",
                    variant = "primary",
                    id = "button-welcomePage-continueSetup",
                    flat = True
                    )

    def on_button_pressed(self, event: Button.Pressed):
        button_id = event.button.id

        if button_id == "button-welcomePage-continueSetup":
            self.dismiss() # Dismiss so that in the main App, the Screen is poped

class MyApp(App):
    def on_mount(self) -> None:
        self.push_screen(WelcomeScreen())

if __name__ == "__main__":
    MyApp().run()

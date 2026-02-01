from textual import events
from textual.widgets import Button, Static, Label
from textual.widget import Widget
from textual.containers import Container, Grid, Horizontal, Center
from textual.message import Message
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.app import ComposeResult, App

from pigeovpn.constants import country_flags, GITHUB_REPO
from pigeovpn.connection_manager import ip_directory, fetch_ip_info, get_size
from pigeovpn.tui.settings import DirectoryInsertScreen, LoginCredentialsScreen
from pigeovpn.external_commands import open_url_browser, disconnect_vpn

# -----------------------------------------------------------
# Funtions
# -----------------------------------------------------------
def update_ip_info(app: App, widget_id: str, pane_type: type[Static]) -> None:
    """
    Update the IP information pane.

    Parameters
    ----------
    app : App
        The running Textual app instance.
    widget_id : str
        The ID of the widget to update
    pane_type : type[Static]
    """

    fetch_ip_info()

    ip_info = app.query_one(widget_id, pane_type)
    
    # Construct the IP info, by showing the IP address, the city and the coutry. 
    # Depending on the response from ipapi, the country name or the country code is shown. 
    country = ip_directory['country_name'] 
    country_code = ip_directory['country']
    if country == 'Unknown': # means that only the country code is available
        country = country_code
    country_flag = country_flags[country_code] if country_code in country_flags.keys() else '' 

    ip_info_str = (
        f"[b]IP address :[/b] {ip_directory['ip']}\n"
        f"[b]City       :[/b] {ip_directory['city']}\n"
        f"[b]Country    :[/b] {country} {country_flag}\n"
    )

    ip_info.update(ip_info_str)
# -----------------------------------------------------------
# Buttons
# -----------------------------------------------------------

class ButtonChangeDirectory(Button):
    """
    Button to give the option to user to change directory from MainScreen
    """
    def __init__(self, label:str, *args, **kwargs) -> None:
        super().__init__(label, *args, **kwargs)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.push_screen(DirectoryInsertScreen(), self.app.update_main_screen)

class ButtonIP(Button):
    """
    Button to refresh the IP address info
    """
    def __init__(self, label: str, *args, **kwargs):
       super().__init__(label, *args, **kwargs)
       self.active_effect_duration = 0.4

    def on_button_pressed(self, event: Button.Pressed) -> None:
        update_ip_info(self.screen, "#ip-pane", InfoPane)

class ButtonShutDown(Button):
    """
    Button to shutdown the app. 
    Works by completely killing the running openvpn instances.
    """
    def __init__(self, label: str, *args, **kwargs):
       super().__init__(label, *args, **kwargs)
       self.active_effect_duration = 1

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.push_screen(ShutDownConfirmScreen())
        #returncode = disconnect_vpn()
        #if returncode != 0:
        #    self.notify(
        #            f"Returncode/error:\n{returncode}",
        #            title="Couldn't disconnect",
        #            severity="error"
        #            )


class ButtonGithubPage(Button):
    def __init__(self, label: str, *args, **kwargs):
        super().__init__(label)
        
    def on_button_pressed(self, event: Button.Pressed) -> None:
        # Try to open the GitHub repo with the default browser
        if not open_url_browser(GITHUB_REPO):
            self.notify(
                    f"GitHub repo is: {GITHUB_REPO}",
                    title="Could not open the default browser",
                    severity="error",
                    timeout=5
                    )


class ButtonLogOut(Button):
    """
    Button to allow the user to change credentials.
    """
    def __init__(self, label: str, *args, **kwargs):
       super().__init__(label, *args, **kwargs)

    def on_button_pressed(self, event:  Button.Pressed) -> None:
        self.app.push_screen(LoginCredentialsScreen())



# -----------------------------------------------------------
# Shutdown confirmation screen
# -----------------------------------------------------------

class ShutDownConfirmScreen(ModalScreen):
    """
    Screen that asks the user to confirm the shutdown (killall) of openvpn
    """

    CSS_PATH = "tui.css"

    def compose(self) -> ComposeResult:
        yield Grid(
                Label("[b]Are you sure you want to shutdown OpenVPN?[/b]", id="label-shutdown-screen"),
                Horizontal(
                    Center(Button("Cancel", variant="default", id="cancel-button-shutdown-screen")),
                    Center(Button("Shutdown", variant="error", id="confirm-button-shutdown-screen")),
                    id="buttons-shutdown-screen"
                ),
                id="shutdown-grid"
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-button-shutdown-screen":
            self.app.pop_screen()
        if event.button.id == "confirm-button-shutdown-screen":
            returncode = disconnect_vpn()
            if returncode != 0:
                self.notify(
                        f"Returncode/error:\n{returncode}",
                        title="Couldn't disconnect",
                        severity="error"
                        )

            else:
                self.notify(
                        "OpenVPN has been killed",
                        title="Disconnected"
                        )
                self.app.pop_screen()

# -----------------------------------------------------------
# InfoPane — RIGHT panel placeholder 
# -----------------------------------------------------------
class InfoPane(Static):
    """
    Used for whichever static message
    """
    def __init__(self, message:str, pane_id:str):
        super().__init__(message, id=pane_id)


# -----------------------------------------------------------
# Ascii art - OpenVPN Selector
# -----------------------------------------------------------

class AsciiFit(Static):
    """
    A widget that displays ASCII art if it fits, otherwise just shows the title written in plain text
    """

    def __init__(self, art: str, fallback: str | Static = "OpenVPN Selector", **kwargs):
        super().__init__("", **kwargs)
        self.art = art.rstrip("\n")
        self.fallback = fallback

        self.lines = self.art.splitlines()
        self.art_height = len(self.lines) if self.lines else 0
        self.art_width = max((len(line) for line in self.lines), default=0)

    def on_mount(self) -> None:
        # Reserve enough height to *potentially* show the art
        self.styles.height = self.art_height
        # Run after layout so width is correct
        self.call_after_refresh(self.update_display)

    def on_resize(self, event: events.Resize) -> None:
        self.update_display()

    def update_display(self) -> None:
        width, height = self.size  # now height will usually be art_height

        if self.art_width <= width and self.art_height <= height:
            self.update(self.art)
        else:
            self.update(self.fallback)


# -----------------------------------------------------------
# The container for the App title
# -----------------------------------------------------------
class SmartAscii(Container):
    """
    Container that keeps height exactly what the current renderable needs.

    It contains a single AsciiFit child and will shrink when the fallback
    text is shown, expanding when the ASCII art fits.
    """

    # expose a property to check if fallback is in use (best-effort)
    using_fallback = reactive(False)

    def __init__(self, ascii_art: str, fallback: str = "OpenVPN Selector", id: str | None = None):
        super().__init__(id=id)
        self.ascii_art = ascii_art
        self.fallback = fallback
        # create the AsciiFit child (id for CSS if you like)
        self.inner = AsciiFit(self.ascii_art, fallback=self.fallback, id=(f"{id}-inner" if id else "ascii-inner"))
        self._adjust_task = None

    def compose(self):
        yield self.inner

    async def on_mount(self) -> None:
        # Run adjustment once layout is ready and then on interval (or on resize)
        await self.adjust_to_content()
        # Poll
        self.set_interval(0.2, self.adjust_to_content)

    async def on_resize(self, event: events.Resize) -> None:
        # recalc when available width changes
        await self.adjust_to_content()

    async def adjust_to_content(self) -> None:
        """Try to detect whether AsciiFit is rendering the ASCII art or the fallback,
        then set our own styles.height (number of lines) accordingly.

        Strategy:
          - If ASCII art fits horizontally/vertically we let container be auto (so the
            ASCII expands as intended).
          - If it doesn't fit (we infer fallback is used), we set our height to the
            number of lines required by the fallback text (so it doesn't keep the
            big previous height).
        """

        # 1) Heuristic: check the AsciiFit widget's measured region if available
        #    (Textual internals differ across releases; this is a best-effort check).
        try:
            # If AsciiFit has a _fallback_used attribute internally, use it:
            if getattr(self.inner, "_fallback_used", None) is not None:
                fallback_used = bool(self.inner._fallback_used)
            else:
                # Fallback heuristic: compare ascii width to available width.
                # If ascii contains a line longer than the available width -> fallback likely.
                avail_width = max(1, self.size.width or self.app.size.width)
                ascii_max_line = max((len(line) for line in self.ascii_art.splitlines()), default=0)
                fallback_used = ascii_max_line > avail_width
        except Exception:
            # fallback to safe heuristic
            avail_width = max(1, self.size.width or self.app.size.width)
            ascii_max_line = max((len(line) for line in self.ascii_art.splitlines()), default=0)
            fallback_used = ascii_max_line > avail_width

        self.using_fallback = fallback_used

        if fallback_used:
            # compute how many lines the fallback needs
            fallback_lines = self.fallback.splitlines() or [" "]
            needed = max(1, len(fallback_lines))
            # set a small height so the wrapper collapses to the fallback height
            # NOTE: set numeric height (lines). Accepts either int or "auto".
            self.styles.height = needed
            self.styles.min_height = needed
            self.styles.max_height = needed
            # make sure we don't stretch
            self.styles.flex = None
            self.styles.align_horizontal = "center"
            self.styles.align_vertical = "middle"
        else:
            # ascii fits — let it expand naturally
            self.styles.height = "auto"
            self.styles.min_height = 1
            self.styles.max_height = None
            self.styles.flex = None
            self.styles.align_horizontal = "center"
            self.styles.align_vertical = "middle"

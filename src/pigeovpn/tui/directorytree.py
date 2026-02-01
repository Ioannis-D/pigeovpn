"""
    The DirectoryTree which shows the directory where the .ovpn files are stored. 
    It is shown on the left side of the screen.

    It also uses a custom function to dynamically filter the results.
"""

from time import sleep
from typing import Iterable, Callable
from pathlib import Path
from textual.widgets import Static
from textual.widgets import DirectoryTree, Input
from textual.widget import Widget
from textual.app import ComposeResult
from textual import on

from pigeovpn.external_commands import connect_vpn
from pigeovpn.tui.statics import ButtonIP, InfoPane, update_ip_info


# -----------------------------------------------------------
# FilteredDirectoryTree — shows only .ovpn files, filters by substring
# -----------------------------------------------------------
class FilteredDirectoryTree(DirectoryTree):
    """
    Ensures only .ovpn files are shown.
    Optionally filters by substring if user_search is set.
    """
    def __init__(self, path: str | Path, user_search: str | None = None, **kwargs):
        super().__init__(path, **kwargs)
        self.user_search = user_search.lower() if user_search else None

    def filter_paths(self, path: Iterable[Path]):
        results: list[Path] = []
        for file in path:
            if file.is_file() and file.suffix.lower() == ".ovpn":
                if not self.user_search or self.user_search in file.name.lower():
                    results.append(file)
        return results


# -----------------------------------------------------------
# SearchInput — simple input box for user text (hidden by default via CSS class)
# -----------------------------------------------------------
class SearchInput(Input):
    BINDINGS = [
        ("escape", "cancel", "Cancel search"),
        ("Enter", "", "Establish search"),
       ]

    def __init__(
        self,
        on_submit: Callable[[], None] | None = None,
        on_cancel: Callable[[], None] | None = None,
        **kwargs
    ):
        super().__init__(placeholder="Search...", **kwargs)
        self._on_submit = on_submit
        self._on_cancel = on_cancel

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        if self._on_submit:
            self._on_submit()

    def action_cancel(self) -> None:
        if self._on_cancel:
            self._on_cancel()


# -----------------------------------------------------------
# DirectoryPane — LEFT panel widget (tree + toggleable search)
# -----------------------------------------------------------
class DirectoryPane(Widget):
    BINDINGS = [
        ("/", "focus_search", "Search"),
    ]

    def __init__(self, ovpn_files_path: str | Path, user_search: str | None = None):
        super().__init__(id="dir-pane")
        self.ovpn_files_path = Path(ovpn_files_path).expanduser()
        self.user_search = user_search


        self.dir_tree = FilteredDirectoryTree(
            path=self.ovpn_files_path,
            user_search=self.user_search,
            id="tree-view",
        )
        self.search = SearchInput(
            on_submit=self._exit_search_keep_filter,
            on_cancel=self.action_clear_search,
            id="search",
        )

    def compose(self) -> ComposeResult:
        # Tree cosmetics
        self.dir_tree.show_root = False
        self.dir_tree.show_guides = False
        yield self.dir_tree
        yield self.search


    # Handle the search box
    def on_mount(self) -> None:
        # Hide search box initially
        self.search.add_class("hidden")

    # Actions
    def action_focus_search(self) -> None:
        self.search.remove_class("hidden")
        self.search.focus()

    def action_clear_search(self) -> None:
        self.search.value = ""
        self.user_search = None
        self.dir_tree.user_search = None
        self._reload_tree()
        self.search.add_class("hidden")
        self.dir_tree.focus()

    def _exit_search_keep_filter(self) -> None:
        self.search.add_class("hidden")
        self.dir_tree.focus()

    # Live filtering
    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "search":
            return
        self.user_search = event.value or None
        self.dir_tree.user_search = self.user_search.lower() if self.user_search else None
        self._reload_tree()

    # Helper: reload the directory listing
    def _reload_tree(self) -> None:
        reload_method = getattr(self.dir_tree, "reload", None)
        if callable(reload_method):
            reload_method()
        else:
            current = self.dir_tree.path
            self.dir_tree.path = current
            self.dir_tree.refresh()


    # Handle the selected .ovpn file
    @on(DirectoryTree.FileSelected, '#tree-view')
    def handle_ovpn_file_selected(self, event: DirectoryTree.FileSelected):
        selected_ovpn_file = event.path
        # Connect to VPN
        returncode = connect_vpn(selected_ovpn_file)
        if not returncode == 0:
            message = f"Not able to connect to {selected_ovpn_file}\n{returncode}"
            self.notify(
                    message,
                    title="Warning",
                    severity="error",
                    timeout=5
                    )
        else:
            self.notify(
                    f"Connected to {selected_ovpn_file}"
                    ),
            info = self.screen.query_one("#info-pane", InfoPane)
            info.update(f"[b]Selected file[/b]:\n{selected_ovpn_file.name}")

            # Update the IP info
            sleep(1)
            update_ip_info(self.screen, "#ip-pane", InfoPane)

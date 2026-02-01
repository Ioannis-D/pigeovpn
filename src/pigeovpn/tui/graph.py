"""
    The graph showing upload and download speeds through time.
    It uses the build-in module of textual, 'Sparkline'.
"""

from collections import deque
from typing import Deque, Optional

import psutil
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Static, Sparkline, Footer

from pigeovpn.connection_manager import get_size, UPDATE_DELAY


class NetworkUsage(Vertical):
    """Network widget with upload/download info + bars underneath."""

    def __init__(
        self,
        window_seconds: int = 60,
        update_delay: float = UPDATE_DELAY,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self.update_delay: float = update_delay
        self.window_seconds: int = window_seconds

        # Number of points in the sparkline for this time window
        self.history_points: int = max(1, int(self.window_seconds / self.update_delay))

        # For computing deltas
        self._last_bytes_sent: Optional[int] = None
        self._last_bytes_recv: Optional[int] = None

        # History, pre-filled with zeros
        self.upload_history: Deque[float] = deque(
            [0.0] * self.history_points, maxlen=self.history_points
        )
        self.download_history: Deque[float] = deque(
            [0.0] * self.history_points, maxlen=self.history_points
        )

        # Will be set in on_mount
        self._upload_info: Static | None = None
        self._download_info: Static | None = None
        self._upload_spark: Sparkline | None = None
        self._download_spark: Sparkline | None = None

    # ---------- layout ----------

    def compose(self) -> ComposeResult:
        # Upload info and bar
        yield Static("Upload: collecting…", id="upload-info")
        yield Sparkline(list(self.upload_history), id="upload-spark")

        # Download info and bar
        yield Static("Download: collecting…", id="download-info")
        yield Sparkline(list(self.download_history), id="download-spark")

    # ---------- lifecycle ----------

    def on_mount(self) -> None:
        self._upload_info = self.query_one("#upload-info", Static)
        self._download_info = self.query_one("#download-info", Static)
        self._upload_spark = self.query_one("#upload-spark", Sparkline)
        self._download_spark = self.query_one("#download-spark", Sparkline)

        io = psutil.net_io_counters()
        self._last_bytes_sent = io.bytes_sent
        self._last_bytes_recv = io.bytes_recv

        self.set_interval(self.update_delay, self._update_stats)

    # ---------- logic ----------

    def _update_stats(self) -> None:
        io = psutil.net_io_counters()

        if self._last_bytes_sent is None or self._last_bytes_recv is None:
            self._last_bytes_sent = io.bytes_sent
            self._last_bytes_recv = io.bytes_recv
            return

        delta_sent: int = io.bytes_sent - self._last_bytes_sent
        delta_recv: int = io.bytes_recv - self._last_bytes_recv

        self._last_bytes_sent = io.bytes_sent
        self._last_bytes_recv = io.bytes_recv

        upload_speed_bps = delta_sent / self.update_delay
        download_speed_bps = delta_recv / self.update_delay

        # Update histories (deque auto-drops the oldest)
        self.upload_history.append(upload_speed_bps)
        self.download_history.append(download_speed_bps)

        # Update bars (in KB/s so the numbers are sane)
        if self._upload_spark is not None:
            self._upload_spark.data = [v / 1024.0 for v in self.upload_history]
        if self._download_spark is not None:
            self._download_spark.data = [v / 1024.0 for v in self.download_history]

        # Pretty strings
        upload_usage = get_size(io.bytes_sent)
        download_usage = get_size(io.bytes_recv)
        upload_speed_str = get_size(upload_speed_bps) + "/s"
        download_speed_str = get_size(download_speed_bps) + "/s"

        # Upload info static
        if self._upload_info is not None:
            self._upload_info.update(
                "\n".join(
                    [
                        "[b]Upload[/b]",
                        f"Usage: {upload_usage}",
                        f"Speed: {upload_speed_str}",
                    ]
                )
            )

        # Download info static
        if self._download_info is not None:
            self._download_info.update(
                "\n".join(
                    [
                        "[b]Download[/b]",
                        f"Usage: {download_usage}",
                        f"Speed: {download_speed_str}",
                    ]
                )
            )

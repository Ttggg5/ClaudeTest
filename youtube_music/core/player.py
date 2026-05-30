"""
Audio playback backend.

Priority order:
  1. VLC (python-vlc) — requires VLC media player installed on the system
  2. mpv  — requires mpv.exe on PATH (ships with many yt-dlp bundles)

Install VLC (recommended):  https://www.videolan.org/vlc/
Install mpv:                https://mpv.io/installation/
"""

import subprocess
import threading
import time

import yt_dlp
from PyQt6.QtCore import QObject, QThread, QTimer, pyqtSignal

# ── try VLC ──────────────────────────────────────────────────────────────────
try:
    import vlc as _vlc
    _VLC_OK = True
except Exception:
    _VLC_OK = False

# ── try mpv via subprocess ────────────────────────────────────────────────────
def _mpv_available() -> bool:
    try:
        subprocess.run(["mpv", "--version"], capture_output=True, timeout=3)
        return True
    except Exception:
        return False

_MPV_OK = not _VLC_OK and _mpv_available()


def backend_name() -> str:
    if _VLC_OK:
        return "vlc"
    if _MPV_OK:
        return "mpv"
    return "none"


# ─────────────────────────────────────────────────────────────────────────────
class URLExtractWorker(QThread):
    url_ready = pyqtSignal(str, dict)   # (stream_url, track_info)
    error = pyqtSignal(str, dict)       # (error_message, track_info)

    def __init__(self, track: dict):
        super().__init__()
        self._track = track

    def run(self):
        ydl_opts = {
            "format": "bestaudio[ext=webm]/bestaudio/best",
            "quiet": True,
            "no_warnings": True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(
                    f"https://www.youtube.com/watch?v={self._track['video_id']}",
                    download=False,
                )
                url = info.get("url") or info["formats"][-1]["url"]
                self.url_ready.emit(url, self._track)
        except Exception as exc:
            self.error.emit(str(exc), self._track)


# ─────────────────────────────────────────────────────────────────────────────
class AudioPlayer(QObject):
    """
    Unified audio player. Uses VLC if available, otherwise mpv subprocess.
    Raises RuntimeError on construction if neither backend is found.
    """

    position_changed = pyqtSignal(int)   # seconds
    duration_changed = pyqtSignal(int)   # seconds
    state_changed = pyqtSignal(str)      # 'loading'|'playing'|'paused'|'stopped'|'ended'

    def __init__(self):
        super().__init__()
        if not _VLC_OK and not _MPV_OK:
            raise RuntimeError(
                "No audio backend found.\n\n"
                "Install VLC media player (recommended):\n"
                "  https://www.videolan.org/vlc/\n\n"
                "Or install mpv and make sure it is on your PATH:\n"
                "  https://mpv.io/installation/"
            )
        self._state = "stopped"
        self._timer = QTimer(self)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._poll)

        if _VLC_OK:
            self._backend = _VLCBackend()
        else:
            self._backend = _MpvBackend()

    # ------------------------------------------------------------------ public

    def play_url(self, url: str) -> None:
        self._backend.play(url)
        self._timer.start()
        self._set_state("playing")

    def play_pause(self) -> None:
        if self._state == "playing":
            self._backend.pause()
            self._set_state("paused")
        elif self._state == "paused":
            self._backend.resume()
            self._set_state("playing")

    def stop(self) -> None:
        self._backend.stop()
        self._timer.stop()
        self._set_state("stopped")

    def seek(self, seconds: int) -> None:
        self._backend.seek(seconds)

    def set_volume(self, vol: int) -> None:
        self._backend.set_volume(vol)

    def get_position(self) -> int:
        return self._backend.position()

    def get_duration(self) -> int:
        return self._backend.duration()

    def is_playing(self) -> bool:
        return self._state == "playing"

    @property
    def state(self) -> str:
        return self._state

    # ----------------------------------------------------------------- private

    def _set_state(self, state: str) -> None:
        if state != self._state:
            self._state = state
            self.state_changed.emit(state)

    def _poll(self) -> None:
        pos = self._backend.position()
        dur = self._backend.duration()

        # Only emit position if not at the very end (avoids seek errors)
        if dur > 0 and pos < dur - 1:
            self.position_changed.emit(pos)

        if dur > 0:
            self.duration_changed.emit(dur)

        if self._backend.ended() and self._state == "playing":
            self._timer.stop()
            self._set_state("ended")


# ─────────────────────────────────────────────────────────────────────────────
class _VLCBackend:
    def __init__(self):
        self._inst = _vlc.Instance("--no-video --quiet")
        self._mp = self._inst.media_player_new()

    def play(self, url: str):
        self._mp.set_media(self._inst.media_new(url))
        self._mp.play()

    def pause(self):
        self._mp.pause()

    def resume(self):
        self._mp.play()

    def stop(self):
        self._mp.stop()

    def seek(self, seconds: int):
        dur = self.duration()
        if dur > 0 and 0 <= seconds <= dur:
            try:
                pos = max(0.0, min(1.0, seconds / dur))
                self._mp.set_position(pos)
            except Exception:
                pass  # Ignore seek errors (e.g., at track end)

    def set_volume(self, vol: int):
        self._mp.audio_set_volume(vol)

    def position(self) -> int:
        dur = self.duration()
        return int(self._mp.get_position() * dur) if dur > 0 else 0

    def duration(self) -> int:
        return max(0, self._mp.get_length() // 1000)

    def ended(self) -> bool:
        s = self._mp.get_state()
        return s in (_vlc.State.Ended, _vlc.State.Stopped)


# ─────────────────────────────────────────────────────────────────────────────
class _MpvBackend:
    """Thin wrapper around mpv subprocess for basic playback."""

    def __init__(self):
        self._proc: subprocess.Popen | None = None
        self._start_time: float = 0.0
        self._paused_at: float | None = None
        self._duration: int = 0
        self._stopped = False

    def play(self, url: str):
        self.stop()
        self._stopped = False
        self._start_time = time.monotonic()
        self._paused_at = None
        self._proc = subprocess.Popen(
            ["mpv", "--no-video", "--really-quiet", url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def pause(self):
        if self._proc and self._paused_at is None:
            self._paused_at = time.monotonic()
            # mpv CLI doesn't easily support pause/resume via stdin without
            # the IPC socket; approximate by stopping. Full IPC would need
            # --input-ipc-server which is more complex.
            # For a basic demo, pause = stop (position resets).
            self._proc.terminate()

    def resume(self):
        pass  # mpv IPC needed for proper resume; omitted in this fallback

    def stop(self):
        if self._proc:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=2)
            except Exception:
                pass
            self._proc = None
        self._stopped = True

    def seek(self, _seconds: int):
        pass  # requires mpv IPC socket

    def set_volume(self, _vol: int):
        pass  # requires mpv IPC socket

    def position(self) -> int:
        if self._proc is None or self._paused_at is not None:
            return 0
        return int(time.monotonic() - self._start_time)

    def duration(self) -> int:
        return self._duration

    def ended(self) -> bool:
        if self._proc is None:
            return not self._stopped
        return self._proc.poll() is not None

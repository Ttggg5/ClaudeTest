from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal


class Queue(QObject):
    track_changed = pyqtSignal(dict)   # new current track
    queue_updated = pyqtSignal(list)   # full queue list after any change

    def __init__(self):
        super().__init__()
        self._tracks: list[dict] = []
        self._index: int = -1

    # ------------------------------------------------------------------ query

    @property
    def current(self) -> Optional[dict]:
        return self._tracks[self._index] if 0 <= self._index < len(self._tracks) else None

    @property
    def current_index(self) -> int:
        return self._index

    @property
    def tracks(self) -> list[dict]:
        return list(self._tracks)

    def has_next(self) -> bool:
        return self._index + 1 < len(self._tracks)

    def has_previous(self) -> bool:
        return self._index > 0

    # ----------------------------------------------------------------- mutate

    def play_now(self, track: dict) -> dict:
        """Insert after current and immediately set as current."""
        insert = self._index + 1
        self._tracks.insert(insert, track)
        self._index = insert
        self.queue_updated.emit(list(self._tracks))
        self.track_changed.emit(track)
        return track

    def add(self, track: dict) -> None:
        self._tracks.append(track)
        self.queue_updated.emit(list(self._tracks))

    def remove(self, index: int) -> None:
        if 0 <= index < len(self._tracks):
            self._tracks.pop(index)
            if index < self._index:
                self._index -= 1
            elif index == self._index:
                self._index = min(self._index, len(self._tracks) - 1)
            self.queue_updated.emit(list(self._tracks))

    def move(self, from_idx: int, to_idx: int) -> None:
        n = len(self._tracks)
        if not (0 <= from_idx < n and 0 <= to_idx < n):
            return
        track = self._tracks.pop(from_idx)
        self._tracks.insert(to_idx, track)
        if self._index == from_idx:
            self._index = to_idx
        self.queue_updated.emit(list(self._tracks))

    def play_at(self, index: int) -> Optional[dict]:
        if 0 <= index < len(self._tracks):
            self._index = index
            t = self._tracks[self._index]
            self.track_changed.emit(t)
            self.queue_updated.emit(list(self._tracks))  # Refresh UI highlight
            return t
        return None

    def next(self) -> Optional[dict]:
        if self.has_next():
            self._index += 1
            t = self._tracks[self._index]
            self.track_changed.emit(t)
            self.queue_updated.emit(list(self._tracks))  # Refresh UI
            return t
        return None

    def previous(self) -> Optional[dict]:
        if self.has_previous():
            self._index -= 1
            t = self._tracks[self._index]
            self.track_changed.emit(t)
            self.queue_updated.emit(list(self._tracks))  # Refresh UI
            return t
        return None

    def clear(self) -> None:
        self._tracks.clear()
        self._index = -1
        self.queue_updated.emit([])

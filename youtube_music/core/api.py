import re
from googleapiclient.discovery import build
from PyQt6.QtCore import QThread, pyqtSignal


def _parse_duration(iso: str) -> int:
    """Convert ISO 8601 duration (PT#H#M#S) to seconds."""
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 0
    h, mi, s = (int(m.group(i) or 0) for i in (1, 2, 3))
    return h * 3600 + mi * 60 + s


def format_duration(seconds: int) -> str:
    h, r = divmod(seconds, 3600)
    m, s = divmod(r, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


class YouTubeAPI:
    def __init__(self, api_key: str):
        self._yt = build("youtube", "v3", developerKey=api_key)

    def search(self, query: str, max_results: int = 20) -> list[dict]:
        search_resp = (
            self._yt.search()
            .list(
                part="snippet",
                q=query,
                type="video",
                maxResults=max_results,
                order="relevance",
            )
            .execute()
        )

        items = search_resp.get("items", [])
        if not items:
            return []

        # Extract video IDs — skip any malformed entries
        video_ids = []
        for item in items:
            vid = item.get("id", {}).get("videoId")
            if vid:
                video_ids.append(vid)

        if not video_ids:
            return []

        # Get duration info for those videos
        details_resp = (
            self._yt.videos()
            .list(part="contentDetails", id=",".join(video_ids))
            .execute()
        )

        durations = {
            v["id"]: _parse_duration(v["contentDetails"]["duration"])
            for v in details_resp.get("items", [])
        }

        results = []
        for item in items:
            vid = item.get("id", {}).get("videoId")
            if not vid:
                continue  # skip malformed entries

            s = item.get("snippet", {})
            thumb = (
                s.get("thumbnails", {}).get("medium")
                or s.get("thumbnails", {}).get("default")
                or {}
            )
            results.append(
                {
                    "video_id": vid,
                    "title": s.get("title", "Unknown"),
                    "channel": s.get("channelTitle", "Unknown"),
                    "thumbnail_url": thumb.get("url", ""),
                    "duration": durations.get(vid, 0),
                }
            )
        return results


class SearchWorker(QThread):
    results_ready = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, api: YouTubeAPI, query: str):
        super().__init__()
        self._api = api
        self._query = query

    def run(self):
        try:
            self.results_ready.emit(self._api.search(self._query))
        except Exception as exc:
            self.error.emit(str(exc))

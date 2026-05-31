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

    def search(
        self, query: str, max_results: int = 20, page_token: str | None = None
    ) -> tuple[list[dict], str | None]:
        """Search videos. Returns (results, next_page_token)."""
        list_kwargs = dict(
            part="snippet",
            q=query,
            type="video",
            maxResults=max_results,
            order="relevance",
        )
        if page_token:
            list_kwargs["pageToken"] = page_token

        search_resp = self._yt.search().list(**list_kwargs).execute()

        next_token = search_resp.get("nextPageToken")
        items = search_resp.get("items", [])
        if not items:
            return [], next_token

        # Extract video IDs — skip any malformed entries
        video_ids = []
        for item in items:
            vid = item.get("id", {}).get("videoId")
            if vid:
                video_ids.append(vid)

        if not video_ids:
            return [], next_token

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
        return results, next_token


class SearchWorker(QThread):
    # emits (results, next_page_token)
    results_ready = pyqtSignal(list, object)
    error = pyqtSignal(str)

    def __init__(self, api: YouTubeAPI, query: str, page_token: str | None = None):
        super().__init__()
        self._api = api
        self._query = query
        self._page_token = page_token

    def run(self):
        try:
            results, next_token = self._api.search(
                self._query, page_token=self._page_token
            )
            self.results_ready.emit(results, next_token)
        except Exception as exc:
            self.error.emit(str(exc))

# YouTube Music Player 🎵

A modern, feature-rich desktop music player built with **PyQt6** and **Material Design 3**, powered by YouTube's Data API and audio streaming.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![PyQt6](https://img.shields.io/badge/PyQt6-6.6%2B-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features ✨

- **🔍 Smart Search** — Search millions of songs, artists, and albums via YouTube Data API v3
- **♾️ Infinite Scroll** — Automatically load more results as you scroll down
- **🎵 Playback Controls** — Play, pause, skip, seek, and adjust volume
- **📋 Queue Management** — Drag to reorder songs, remove from queue, or clear all
- **🎨 Material Design 3** — Modern dark theme with YouTube red accent color
- **⏳ Loading Animations** — Smooth spinner animations during search and playback
- **🎯 Trending Recommendations** — Auto-loads trending music on startup
- **🖱️ Seek Shortcut** — Drag progress bar to 95%+ to instantly skip to next song
- **🌙 System Theme Detection** — Respects Windows dark/light mode preference
- **⚡ Dual Audio Backends** — VLC (primary) or mpv (fallback) for maximum compatibility

## Requirements 📋

### System Requirements
- **Windows**, **macOS**, or **Linux**
- **Python 3.8+**
- **VLC media player** (recommended) or **mpv** (fallback)

### Python Dependencies
- PyQt6 ≥ 6.6.0
- google-api-python-client ≥ 2.100.0
- python-vlc ≥ 3.0.18122
- yt-dlp ≥ 2024.1.0
- requests ≥ 2.31.0

## Quick Start 🚀

### 1. Install VLC Media Player
Download from: https://www.videolan.org/vlc/

### 2. Get a YouTube Data API v3 Key
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable "YouTube Data API v3"
4. Create an API key
5. Copy the key

### 3. Install Dependencies
```bash
cd youtube_music
pip install -r requirements.txt
```

### 4. Run the App
```bash
python main.py
```

Or simply double-click `run.bat` (Windows)

### 5. Configure API Key
- Settings dialog opens on first launch
- Paste your YouTube API key
- Click "Ok"

## Usage 🎮

### Search & Play
1. **Search** — Type a song/artist name and press Enter or click "Search"
2. **Play** — Double-click a result or click the ▶ button
3. **Queue** — Click ✓ to add to queue without playing

### Queue Management
- **Reorder** — Drag songs up/down in the queue sidebar
- **Jump** — Double-click a queued song to play it
- **Remove** — Right-click → Remove
- **Clear** — Click "Clear" button in queue header

### Playback
- **⏮ Previous** — Skip to previous song (or restart current if >3s in)
- **▶/⏸ Play/Pause** — Toggle playback
- **⏭ Next** — Skip to next song
- **Seek** — Click/drag the progress bar (or drag to 95%+ to auto-skip)
- **🔊 Volume** — Adjust with the volume slider

### Recommendations
Trending music loads automatically on startup. Search for anything to browse specific genres/artists.

## Project Structure 📁

```
youtube_music/
├── main.py                 # Entry point
├── run.bat                 # Windows launcher
├── requirements.txt        # Python dependencies
├── config.py              # Configuration management
│
├── core/                  # Business logic
│   ├── api.py            # YouTube API integration
│   ├── player.py         # Audio playback (VLC/mpv)
│   └── queue.py          # Queue state management
│
└── ui/                    # User interface
    ├── main_window.py     # Main app coordinator
    ├── search_panel.py    # Search & infinite scroll
    ├── queue_panel.py     # Queue sidebar
    ├── player_bar.py      # Now-playing & controls
    ├── settings_dialog.py # API key configuration
    ├── loading_spinner.py # Loading animation widget
    └── theme.py           # Material Design 3 stylesheet
```

## Architecture 🏗️

### Signal-Based Flow
```
User Action (UI) → Signal → Handler → Model Update → UI Refresh
```

### Core Components
- **YouTubeAPI** — Wraps Google's youtube-v3 client
- **SearchWorker** — Background thread for async API calls
- **Queue** — Qt signal-emitting queue model
- **AudioPlayer** — Abstraction over VLC/mpv backends
- **URLExtractWorker** — yt-dlp extraction in background thread

### Threading
- Main thread handles UI
- Worker threads handle API calls, URL extraction, thumbnail loading
- Signals coordinate between threads safely

## Configuration 🔧

API key is stored in `youtube_music/config.json`:
```json
{
  "api_key": "AIza..."
}
```

Change anytime via **Settings** (⚙) button.

## Keyboard Shortcuts ⌨️

| Action | Key |
|--------|-----|
| Search | `Enter` in search box |
| Play/Pause | Button click (spacebar coming soon) |
| Next/Previous | Button clicks |
| Seek | Click/drag progress bar |

## Troubleshooting 🔧

### "VLC Not Found"
- Install VLC: https://www.videolan.org/vlc/
- Or install mpv as fallback: https://mpv.io/

### "Search failed: 'videoId'"
- Verify API key is valid
- Check YouTube Data API v3 is **enabled** in Google Cloud Console
- Quota may be exceeded (free tier: 10,000 units/day)

### Audio not playing
- Ensure VLC or mpv is installed
- Check system audio levels
- Try another song to isolate the issue

### Slow thumbnail loading
- Normal on first search (downloads from YouTube)
- Improves after thumbnails are cached in memory

## Performance Notes ⚡

- **Search**: ~1-2 seconds (includes duration fetch)
- **Infinite Scroll**: Automatic when 90% scrolled
- **Playback**: Minimal delay (<2s) for audio extraction
- **UI**: Smooth 60fps on modern systems

## Limitations ⚠️

- YouTube API limited to 10,000 units/day (free tier)
- Requires internet connection for search/playback
- yt-dlp extraction depends on YouTube not blocking it
- No offline playback or music library (yet)

## Future Enhancements 🚀

- [ ] Playlist saving to disk
- [ ] Keyboard shortcuts (spacebar to play, arrow keys to skip)
- [ ] Shuffle and repeat modes
- [ ] Search filters (duration, upload date, view count)
- [ ] Audio visualization
- [ ] Dark/light theme toggle
- [ ] User playlists sync

## License 📄

MIT License — See LICENSE file for details

## Credits 🙏

Built with:
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) — Desktop UI framework
- [Google API Client](https://github.com/googleapis/google-api-python-client) — YouTube search
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — Audio stream extraction
- [python-vlc](https://www.olivieraubert.net/vlc/python-ctypes/) — Audio playback
- [Material Design 3](https://m3.material.io/) — Design system

## Support 💬

Found a bug or have a feature request? Open an issue on GitHub!

---

**Enjoy your music! 🎵**

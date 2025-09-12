# Mega Downloader Module

A standalone, minimal Mega download subsystem extracted from the main bot's MEGA logic. It offers a simple programmatic API and a CLI entrypoint without pulling in full mirror/leech workflow or Telegram messaging.

## Features
- Async MEGA downloads using existing `AsyncMega` + `MegaAppListener` from core bot
- Status tracking (progress %, speed, size, ETA)
- Simple task registry (in‑memory)
- CLI interface

## Usage
```bash
export MEGA_EMAIL="you@example.com"   # optional
export MEGA_PASSWORD="password"       # optional
python -m mega_downloader.main "https://mega.nz/file/XXXX#KEY" -o downloads
```

## Programmatic
```python
from mega_downloader.mega.download import start_mega_download
import asyncio
asyncio.run(start_mega_download("https://mega.nz/file/XXXX#KEY"))
```

## Roadmap
- Folder recursive download of all child nodes
- Duplicate / limit / queue integration (port from main bot)
- Structured logging / JSON mode
- Optional Telegram bridge

## Notes
This module intentionally avoids modifying the existing MEGA integration. Future refactors may replace in-place logic with this extracted provider.
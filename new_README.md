# MEGA Downloader Bot

A minimal Telegram bot for downloading MEGA files and folders with progress tracking and cancellation support.

## Features

- 📥 Download MEGA file and folder links
- 📊 Progress tracking with GID (Generated ID)
- 🚀 Real-time speed and ETA display
- 🚫 Download cancellation by GID
- 🤖 Telegram bot interface
- 💻 CLI fallback for direct downloads

## Setup

### Environment Variables

Create a `.env` file or set these environment variables:

```bash
# Required
BOT_TOKEN=your_telegram_bot_token

# Optional MEGA account (for better limits)
MEGA_EMAIL=your_mega_email
MEGA_PASSWORD=your_mega_password

# Optional configuration
DOWNLOAD_DIR=downloads          # Default: downloads
MAX_CONCURRENT=2               # Default: 2
DEBUG=false                    # Default: false
```

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Telegram Bot

Start the bot:
```bash
python mega_bot/run.py
```

Available commands:
- `/start` or `/help` - Show help message
- `/mega <link>` - Download MEGA file or folder
- `/status` - Show active and recent downloads
- `/cancel <gid>` - Cancel download by GID

You can also send MEGA links directly without the `/mega` command.

### CLI Interface

Download directly via command line:
```bash
python -m mega_bot.cli <mega_link>
```

Example:
```bash
python -m mega_bot.cli https://mega.nz/file/example
```

## Download Tracking

Each download is assigned a unique GID (5-character hex ID) for tracking:

- **Queued**: Download is waiting to start
- **Running**: Download is in progress with real-time stats
- **Completed**: Download finished successfully
- **Failed**: Download encountered an error
- **Cancelled**: Download was cancelled by user

## Status Display

For active downloads, you'll see:
- **Progress**: Percentage completed
- **Speed**: Current download speed
- **ETA**: Estimated time remaining
- **Size**: Downloaded/Total size

## Folder Downloads

Folder links are supported with the following behavior:
- Single-level folder contents are downloaded
- Recursive deep folder traversal is marked as TODO for future implementation
- Each file in the folder is downloaded sequentially

## Limitations

- **In-memory only**: No persistent storage (downloads are lost on restart)
- **No multi-process scaling**: Single process with configurable concurrency
- **Basic folder support**: Deep recursion not yet implemented
- **No rate limiting**: Basic implementation without advanced throttling
- **No duplicate detection**: Same links can be queued multiple times

## Roadmap

Future enhancements marked as TODO in code:
- [ ] Persistent storage with database
- [ ] Deep folder recursion with parallel downloads
- [ ] Multi-process scaling
- [ ] Rate limiting and duplicate detection
- [ ] Download resume capability
- [ ] Custom naming patterns
- [ ] Download queue management
- [ ] User permissions and quotas

## Development

### Linting

The project uses `ruff` for code formatting:
```bash
pip install ruff
ruff check .
ruff format .
```

### Project Structure

```
mega_bot/
├── __init__.py
├── config.py              # Environment configuration
├── logger.py               # Logging setup
├── task_manager.py         # Download task coordination
├── run.py                  # Telegram bot entry point
├── cli.py                  # CLI interface
├── utils/
│   ├── links.py           # MEGA link validation
│   └── formatting.py      # Size/time formatting
├── mega/
│   ├── async_mega.py      # Async MEGA API wrapper
│   ├── listener.py        # MEGA event listener
│   ├── status.py          # Download status tracking
│   └── downloader.py      # Download orchestration
└── bot/
    └── handlers.py         # Telegram command handlers
```

## License

[Add your license here]
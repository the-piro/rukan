# Telegram MEGA Leech Bot (PyMegaSDK)

A simplified Telegram bot for leeching files from MEGA and uploading them to Telegram.

## Features

- **MEGA Download**: Download files and folders from MEGA using PyMegaSDK
- **Telegram Upload**: Upload downloaded files to Telegram as documents or media
- **Progress Tracking**: Real-time download progress and status updates
- **Cancellation**: Cancel ongoing downloads
- **User Settings**: Per-user settings for customization
- **Queue System**: Built-in download and upload queue management

## Environment Variables

### Required
- `BOT_TOKEN`: Your Telegram bot token from @BotFather
- `OWNER_ID`: Your Telegram user ID (get from @userinfobot)
- `TELEGRAM_API`: Your Telegram API ID from my.telegram.org
- `TELEGRAM_HASH`: Your Telegram API hash from my.telegram.org

### MEGA Configuration
- `MEGA_EMAIL`: Your MEGA account email (optional, for private links)
- `MEGA_PASSWORD`: Your MEGA account password (optional, for private links)
- `MEGA_LIMIT`: Download size limit in GB (0 = no limit)

### Optional
- `DATABASE_URL`: MongoDB connection string for persistent settings
- `AUTHORIZED_CHATS`: Comma-separated list of chat IDs that can use the bot
- `SUDO_USERS`: Comma-separated list of user IDs with admin privileges
- `DISABLE_LEECH`: Set to `True` to disable leech commands
- `LEECH_SPLIT_SIZE`: Maximum file size per part in bytes (default: 2GB)
- `LEECH_LIMIT`: Total leech size limit in GB (0 = no limit)
- `AS_DOCUMENT`: Set to `True` to upload files as documents by default
- `MEDIA_GROUP`: Set to `True` to group split files in media albums

## Commands

- `/start` - Start the bot and get welcome message
- `/mirror <mega_link>` - Download from MEGA and upload to cloud (if configured)
- `/leech <mega_link>` - Download from MEGA and upload to Telegram
- `/status` - Check current download status
- `/cancel` - Cancel ongoing downloads
- `/settings` - View bot settings
- `/help` - Get help and command list

## Installation

### Prerequisites
- Python 3.8+ (tested with 3.12)
- PyMegaSDK (see MEGA SDK Setup below)

### MEGA SDK Setup
The bot requires the PyMegaSDK. Install it manually:
```bash
# Install compatible version
pip install "tenacity<9.0.0"
pip install mega.py

# Note: If you encounter asyncio.coroutine errors with Python 3.11+,
# you may need to use an alternative MEGA implementation or patch the library
```

### Docker
```bash
# Clone the repository
git clone https://github.com/the-piro/rukan.git
cd rukan

# Create config.py with your settings
cp config_sample.py config.py
# Edit config.py with your values

# Build and run
docker build -t mega-leech-bot .
docker run -d mega-leech-bot
```

### Manual
```bash
# Clone the repository
git clone https://github.com/the-piro/rukan.git
cd rukan

# Install dependencies
pip install -r requirements.txt

# Install MEGA SDK separately
pip install "tenacity<9.0.0"
pip install mega.py

# Create config.py with your settings
cp config_sample.py config.py
# Edit config.py with your values

# Run the bot
python -m bot
```

## Usage Examples

1. **Download MEGA file**: Send `/leech https://mega.nz/file/...`
2. **Download MEGA folder**: Send `/leech https://mega.nz/folder/...`
3. **Check status**: Send `/status` to see active downloads
4. **Cancel download**: Send `/cancel` to stop ongoing downloads

## Removed Features

This bot has been simplified and the following features were removed:
- Torrent downloads (qBittorrent/aria2)
- Direct HTTP downloads
- YouTube-dl/yt-dlp integration
- Google Drive operations
- Cloud storage mirroring (rclone)
- Debrid services integration
- JDownloader support
- NZB/Usenet downloads
- RSS monitoring
- Search functionality

For the full-featured version, check the original WZML-X project.

## License

This project is licensed under the GNU General Public License v3.0 - see the LICENSE file for details.

## Credits

Based on the WZML-X project by anasty17.
# Video Tools (-vt) Implementation

## Overview
This implementation adds a new `-vt` (Video Tools) flag to the Rukan bot, following the same patterns as existing operations like archive (-z), extract (-e), convert, split, and rename (-n).

## Features Implemented

### 1. Command Parsing and Entry Point
- ✅ Added `-vt` flag to argument parser (`bot_utils.py`)
- ✅ Added `VideoTools` command to bot commands (`bot_commands.py`) 
- ✅ Registered handlers for `/videotools` and `/vt` commands (`handlers.py`)
- ✅ Integrated with mirror/leech command flow (`mirror_leech.py`)

### 2. VT Menu and Compression Options
- ✅ Interactive Video Tools menu with Compress option
- ✅ Resolution selection: 144p, 240p, 360p, 480p, 720p, 1080p
- ✅ 60-second timeout with countdown updates
- ✅ Consistent inline keyboard formatting

### 3. Compression Behavior
- ✅ FFmpeg integration using existing patterns from `media_utils.py`
- ✅ Aspect ratio preservation with no upscaling
- ✅ Bitrate optimization per resolution:
  - 144p: 100k bitrate
  - 240p: 200k bitrate  
  - 360p: 400k bitrate
  - 480p: 800k bitrate
  - 720p: 1500k bitrate
  - 1080p: 3000k bitrate
- ✅ Progress tracking framework (placeholder for full implementation)
- ✅ Audio preservation with AAC 128k encoding

### 4. UI/Flow Details
- ✅ New message for VT menu (prevents MESSAGE_ID_INVALID)
- ✅ Message editing for subsequent steps
- ✅ Back/Cancel buttons with proper navigation
- ✅ 60-second timeout per step with visual countdown
- ✅ Timeout handling with restart option

### 5. Code Organization
- ✅ Follows existing module structure (`bot/modules/video_tools.py`)
- ✅ Uses same handler patterns as other tools
- ✅ Consistent with bot's callback query system
- ✅ Proper error handling and cleanup

### 6. Documentation and Help
- ✅ Added to command help system
- ✅ Added `-vt` flag documentation in help messages
- ✅ Included in both MIRROR_HELP_DICT and YT_HELP_DICT

## Usage

### Standalone Command
```
/videotools
/vt
```

### With Downloads
```
/mirror <link> -vt
/leech <link> -vt
```

### Flag in Help
```
/help - Shows Video Tools in command list
/mirror - Shows Video-Tools in flag options
```

## File Structure

```
bot/
├── modules/
│   ├── video_tools.py          # Main VT implementation
│   ├── mirror_leech.py         # Integrated -vt flag handling
│   └── __init__.py             # Added VT exports
├── core/
│   └── handlers.py             # Registered VT handlers
└── helper/
    ├── telegram_helper/
    │   └── bot_commands.py     # Added VideoTools command
    └── ext_utils/
        ├── bot_utils.py        # Added -vt to arg parser
        └── help_messages.py    # Added VT help text
```

## Key Functions

### `video_tools.py`
- `show_video_tools_menu()` - Main VT menu display
- `vt_callback_handler()` - Handles all VT button callbacks
- `vt_timeout_handler()` - Manages 60s timeouts with countdown
- `show_resolution_menu()` - Resolution selection interface
- `start_compression()` - Compression workflow (placeholder)
- `VideoCompressor` class - FFmpeg compression logic

### Flow
1. User triggers `-vt` flag or `/videotools` command
2. New VT menu message sent (prevents Telegram errors)
3. User selects "Compress" → Resolution menu appears
4. User selects resolution → Compression starts
5. Progress tracking and completion handling
6. 60s timeout at each step with visual countdown

## Integration Points

### Argument Parser
```python
bool_arg_set = {
    # ... existing flags ...
    "-vt",  # Added
}
```

### Mirror/Leech Integration
```python
self.video_tools = args["-vt"]  # Stored as listener property
```

### Command Registration
```python
"VideoTools": ["videotools", "vt"],  # In bot_commands.py
```

### Handler Registration
```python
TgClient.bot.add_handler(
    MessageHandler(show_video_tools_menu, 
                  filters=command(BotCommands.VideoToolsCommand) & CustomFilters.authorized)
)
TgClient.bot.add_handler(
    CallbackQueryHandler(vt_callback_handler, filters=regex("^vt"))
)
```

## Testing

The implementation has been tested for:
- ✅ Python syntax validity across all modified files
- ✅ Function presence and structure
- ✅ Integration points (commands, handlers, parsers)
- ✅ Import chain completeness

Manual testing required for:
- Full bot environment functionality
- Telegram UI behavior
- FFmpeg compression workflow
- Timeout behavior
- Error handling

## Future Enhancements

The framework supports easy addition of:
- Watermark tool
- Video merge tool  
- Audio extraction
- Subtitle management
- Batch processing

All following the same menu-driven, timeout-managed pattern established by the compression tool.
from .. import auth_chats, sudo_users, task_dict, excluded_extensions, shortener_dict, LOGGER
from ..core.config_manager import Config
from ..helper.ext_utils.db_handler import database
from ..helper.telegram_helper.message_utils import send_message, edit_message
from ..helper.telegram_helper.button_build import ButtonMaker


async def send_bot_settings(_, message):
    """Send simplified bot settings for MEGA leech bot."""
    text = f"""<b>Bot Settings:</b>
    
<b>MEGA Settings:</b>
- MEGA Email: {'Set' if Config.MEGA_EMAIL else 'Not Set'}
- MEGA Password: {'Set' if Config.MEGA_PASSWORD else 'Not Set'}
- MEGA Limit: {Config.MEGA_LIMIT} GB

<b>Leech Settings:</b>
- Leech Disabled: {Config.DISABLE_LEECH}
- Leech Limit: {Config.LEECH_LIMIT} GB
- Leech Split Size: {Config.LEECH_SPLIT_SIZE / (1024**3):.2f} GB
- As Document: {Config.AS_DOCUMENT}
- Media Group: {Config.MEDIA_GROUP}

<b>General Settings:</b>
- Queue Download: {Config.QUEUE_DOWNLOAD}
- Queue Upload: {Config.QUEUE_UPLOAD}
- Bot Max Tasks: {Config.BOT_MAX_TASKS}
- User Max Tasks: {Config.USER_MAX_TASKS}

<b>Stats:</b>
- Active Tasks: {len(task_dict)}
- Authorized Chats: {len(auth_chats)}
- Sudo Users: {len(sudo_users)}
"""
    await send_message(message, text)


async def edit_bot_settings(client, query):
    """Simplified bot settings editor - read-only for now."""
    await query.answer("Bot settings are read-only in this simplified version.")
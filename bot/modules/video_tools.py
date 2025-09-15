import asyncio
from time import time

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from ..helper.telegram_helper.message_utils import (
    send_message,
    edit_message,
    delete_message,
)


async def open_video_tools_menu(client, message, original_cmd_text=None):
    """
    Opens the initial Video Tools menu as a NEW bot message.
    Sends reply to the original command message to maintain linkage.
    """
    buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🗜️ Compress", callback_data="vt:compress")],
            [InlineKeyboardButton("❌ Cancel", callback_data="vt:cancel")],
        ]
    )

    text = (
        "<b>🎬 Video Tools Menu</b>\n\n"
        "Select an option to proceed with your video processing:"
    )

    # Send NEW bot message as reply to the original command
    vt_message = await send_message(message, text, buttons)

    # Start 60-second timeout task
    asyncio.create_task(_timeout_handler(client, vt_message, 60, "vt"))


async def video_tools_callback(client, callback_query):
    """
    Handles callback queries for Video Tools with prefix 'vt'.
    Routes different callback data patterns.
    """
    data = callback_query.data
    message = callback_query.message

    if data == "vt:compress":
        await _show_resolution_menu(client, message)
    elif data == "vt:cancel":
        await _cancel_video_tools(client, message)
    elif data.startswith("vt:res:"):
        resolution = data.split(":")[-1]
        await _start_compression(client, message, callback_query, resolution)
    else:
        await callback_query.answer("Unknown option!", show_alert=True)


async def _show_resolution_menu(client, message):
    """
    Shows resolution selection buttons for compression.
    Applies 60-second timeout.
    """
    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("144p", callback_data="vt:res:144p"),
                InlineKeyboardButton("240p", callback_data="vt:res:240p"),
            ],
            [
                InlineKeyboardButton("360p", callback_data="vt:res:360p"),
                InlineKeyboardButton("480p", callback_data="vt:res:480p"),
            ],
            [
                InlineKeyboardButton("720p", callback_data="vt:res:720p"),
                InlineKeyboardButton("1080p", callback_data="vt:res:1080p"),
            ],
            [InlineKeyboardButton("❌ Cancel", callback_data="vt:cancel")],
        ]
    )

    text = (
        "<b>🗜️ Select Compression Resolution</b>\n\n"
        "Choose the target resolution for video compression:"
    )

    await edit_message(message, text, buttons)

    # Start 60-second timeout for this step
    asyncio.create_task(_timeout_handler(client, message, 60, "vt"))


async def _start_compression(client, message, callback_query, resolution):
    """
    Starts the compression process using the existing FFmpeg infrastructure.
    """
    # Get the original command message from the reply
    original_message = message.reply_to_message
    if not original_message:
        await callback_query.answer("Original command not found!", show_alert=True)
        return

    # Parse the original command to get link and other args
    text_lines = original_message.text.split("\n")
    input_list = text_lines[0].split(" ")

    # Check if there's a link provided
    link = ""
    if len(input_list) > 1:
        # Look for link in command arguments or reply
        for arg in input_list[1:]:
            if not arg.startswith("-"):
                link = arg
                break

    if not link and original_message.reply_to_message:
        reply_to = original_message.reply_to_message
        if reply_to.text:
            link = reply_to.text.split("\n", 1)[0].strip()

    if not link:
        await edit_message(
            message,
            "❌ <b>Error:</b> No video link or file found to compress.\n\n"
            "Please provide a valid video link or reply to a video file.",
        )
        return

    # Generate FFmpeg command set for the selected resolution
    ffmpeg_cmds = _get_compression_command(resolution)

    # Update the message to show compression starting
    await edit_message(
        message,
        f"🗜️ <b>Starting Compression to {resolution}</b>\n\n"
        f"Processing video with target resolution: <code>{resolution}</code>\n"
        f"Link: <code>{link}</code>\n\n"
        "Please wait...",
    )

    # Import Mirror class and start the compression task
    from .mirror_leech import Mirror

    # Reconstruct the command without -vt flag and add -ff flag
    original_args = input_list[1:]  # Remove command name

    # Remove -vt flag if present
    cleaned_args = [arg for arg in original_args if arg != "-vt"]

    # Add the link if not already present
    if link not in cleaned_args:
        cleaned_args.insert(0, link)

    # Add FFmpeg command
    cleaned_args.extend(["-ff", ffmpeg_cmds])

    # Create a modified command
    modified_cmd = f"{input_list[0]} {' '.join(cleaned_args)}"

    # Create a copy of the original message with modified text
    class ModifiedMessage:
        def __init__(self, original):
            for attr in dir(original):
                if not attr.startswith("_"):
                    try:
                        setattr(self, attr, getattr(original, attr))
                    except Exception:
                        pass
            self.text = modified_cmd

    modified_message = ModifiedMessage(original_message)

    # Start the mirror/leech process with FFmpeg compression
    await Mirror(client, modified_message, is_leech=True).new_event()

    await callback_query.answer(
        f"Compression to {resolution} started!", show_alert=True
    )


async def _cancel_video_tools(client, message):
    """
    Cancels the Video Tools operation and deletes the message.
    """
    await edit_message(message, "❌ <b>Video Tools cancelled.</b>")
    await asyncio.sleep(3)
    await delete_message(message)


async def _timeout_handler(client, message, timeout_seconds, callback_prefix):
    """
    Handles timeout for Video Tools menus.
    Similar to the user settings timeout behavior.
    """
    start_time = time()
    update_time = time()
    active = True

    while active and (time() - start_time) < timeout_seconds:
        await asyncio.sleep(0.5)

        # Update countdown every 8 seconds
        if time() - update_time > 8:
            update_time = time()
            remaining = timeout_seconds - (time() - start_time)
            if remaining > 0:
                try:
                    # Try to get the current message text and update countdown
                    current_msg = await client.get_messages(message.chat.id, message.id)
                    if current_msg and current_msg.text:
                        text_lines = current_msg.text.split("\n")
                        # Add or update the time left line
                        if any("Time Left" in line for line in text_lines):
                            # Update existing countdown
                            for i, line in enumerate(text_lines):
                                if "Time Left" in line:
                                    text_lines[i] = (
                                        f"⏱️ <b>Time Left:</b> <code>{round(remaining, 1)} sec</code>"
                                    )
                                    break
                        else:
                            # Add new countdown line
                            text_lines.append(
                                f"\n⏱️ <b>Time Left:</b> <code>{round(remaining, 1)} sec</code>"
                            )

                        await edit_message(message, "\n".join(text_lines))
                except Exception:
                    # Message might have been modified, continue
                    pass

    # Timeout reached - disable buttons and show timeout message
    if active:
        try:
            await edit_message(
                message,
                "⏰ <b>Video Tools Menu Timed Out</b>\n\n"
                "The menu has expired due to inactivity. Please run the command again.",
            )
        except Exception:
            # Message might have been deleted
            pass


def _get_compression_command(resolution):
    """
    Generates FFmpeg command set for the specified resolution compression.
    Returns a set of FFmpeg commands as expected by the existing system.
    """
    resolution_settings = {
        "144p": "-vf scale=256:144 -c:v libx264 -crf 28 -preset medium -c:a aac -b:a 64k -i input.video output_144p.mp4",
        "240p": "-vf scale=426:240 -c:v libx264 -crf 26 -preset medium -c:a aac -b:a 96k -i input.video output_240p.mp4",
        "360p": "-vf scale=640:360 -c:v libx264 -crf 24 -preset medium -c:a aac -b:a 128k -i input.video output_360p.mp4",
        "480p": "-vf scale=854:480 -c:v libx264 -crf 22 -preset medium -c:a aac -b:a 128k -i input.video output_480p.mp4",
        "720p": "-vf scale=1280:720 -c:v libx264 -crf 20 -preset medium -c:a aac -b:a 192k -i input.video output_720p.mp4",
        "1080p": "-vf scale=1920:1080 -c:v libx264 -crf 18 -preset medium -c:a aac -b:a 256k -i input.video output_1080p.mp4",
    }

    return {resolution_settings.get(resolution, resolution_settings["720p"])}

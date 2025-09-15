from asyncio import sleep
from functools import partial
from time import time
from os import path as ospath

from aiofiles.os import remove, path as aiopath

from .. import LOGGER, bot_loop
from ..core.config_manager import BinConfig
from ..helper.ext_utils.bot_utils import new_task, arg_parser
from ..helper.ext_utils.media_utils import get_media_info, FFMpeg
from ..helper.telegram_helper.button_build import ButtonMaker
from ..helper.telegram_helper.message_utils import (
    send_message,
    edit_message,
    delete_message,
)
from pyrogram.filters import create
from pyrogram.handlers import MessageHandler


# Handler dictionary for timeout management
vt_handler_dict = {}

# Resolution options with bitrate settings (conservative defaults)
RESOLUTION_SETTINGS = {
    "144p": {"height": 144, "bitrate": "100k"},
    "240p": {"height": 240, "bitrate": "200k"},
    "360p": {"height": 360, "bitrate": "400k"},
    "480p": {"height": 480, "bitrate": "800k"},
    "720p": {"height": 720, "bitrate": "1500k"},
    "1080p": {"height": 1080, "bitrate": "3000k"},
}


class VideoCompressor:
    def __init__(self, listener, resolution, video_path):
        self.listener = listener
        self.resolution = resolution
        self.video_path = video_path
        self.ffmpeg = FFMpeg(listener)
        
    async def compress_video(self):
        """Compress video to selected resolution"""
        try:
            # Get video info
            duration, qual, _, _ = await get_media_info(self.video_path, extra_info=True)
            if duration == 0:
                LOGGER.error(f"Cannot get video info: {self.video_path}")
                return False
                
            # Get resolution settings
            target_height = RESOLUTION_SETTINGS[self.resolution]["height"]
            bitrate = RESOLUTION_SETTINGS[self.resolution]["bitrate"]
            
            # Check if we need to upscale (avoid upscaling)
            current_height = int(qual.replace('p', '')) if qual else 0
            if current_height > 0 and current_height <= target_height:
                # Source is already lower than target, use source resolution but still re-encode for compression
                scale_filter = f"scale=-2:{current_height}"
            else:
                # Scale down to target resolution
                scale_filter = f"scale=-2:{target_height}:force_original_aspect_ratio=decrease"
            
            # Generate output filename
            base_name, ext = ospath.splitext(self.video_path)
            output_path = f"{base_name}_compressed_{self.resolution}.mp4"
            
            # Build FFmpeg command
            cmd = [
                BinConfig.FFMPEG_NAME,
                "-hide_banner",
                "-loglevel", "error",
                "-progress", "pipe:1",
                "-i", self.video_path,
                "-vf", scale_filter,
                "-c:v", "libx264",
                "-b:v", bitrate,
                "-c:a", "aac",
                "-b:a", "128k",
                "-preset", "medium",
                "-crf", "23",
                "-movflags", "+faststart",
                "-threads", "4",
                output_path
            ]
            
            # Run compression
            result = await self.ffmpeg.ffmpeg_cmds(cmd, self.video_path)
            
            if result and await aiopath.exists(output_path):
                return output_path
            else:
                LOGGER.error(f"Video compression failed for: {self.video_path}")
                return False
                
        except Exception as e:
            LOGGER.error(f"Error during video compression: {e}")
            return False


@new_task
async def video_tools_handler(client, message):
    """Handle -vt flag from mirror/leech commands"""
    user_id = message.from_user.id
    
    # Parse command arguments to check for -vt flag
    text = message.text.split("\n")
    input_list = text[0].split(" ")
    
    args = {"-vt": False}
    arg_parser(input_list[1:], args)
    
    if not args["-vt"]:
        return False  # Not a video tools command
    
    # Show Video Tools menu
    await show_video_tools_menu(client, message)
    return True


@new_task
async def show_video_tools_menu(client, message):
    """Show the main Video Tools menu"""
    user_id = message.from_user.id
    
    # Create Video Tools menu
    buttons = ButtonMaker()
    buttons.data_button("🗜️ Compress", f"vt {user_id} compress")
    buttons.data_button("❌ Cancel", f"vt {user_id} cancel")
    
    vt_text = (
        "<b>🎬 Video Tools</b>\n\n"
        "Select a tool to use:\n"
        "• <b>Compress</b> - Reduce video file size with quality options\n"
        "• More tools coming soon (watermark, merge, etc.)\n\n"
        "⏱ <i>Session will timeout in 60 seconds</i>"
    )
    
    # Send new message for VT menu to avoid MESSAGE_ID_INVALID error
    vt_message = await send_message(message, vt_text, buttons.build_menu(1))
    
    # Set up timeout handler
    vt_handler_dict[user_id] = {
        "message": vt_message,
        "start_time": time(),
        "stage": "main_menu"
    }
    
    # Start timeout countdown
    bot_loop.create_task(vt_timeout_handler(client, user_id))


@new_task
async def vt_timeout_handler(client, user_id):
    """Handle timeout for VT sessions"""
    while user_id in vt_handler_dict:
        await sleep(1)
        
        if user_id not in vt_handler_dict:
            break
            
        session = vt_handler_dict[user_id]
        elapsed = time() - session["start_time"]
        
        if elapsed >= 60:  # 60 second timeout
            await vt_timeout_expired(client, user_id)
            break
        
        # Update countdown every 10 seconds
        if int(elapsed) % 10 == 0 and elapsed > 0:
            try:
                remaining = 60 - int(elapsed)
                if session["stage"] == "main_menu":
                    text = (
                        "<b>🎬 Video Tools</b>\n\n"
                        "Select a tool to use:\n"
                        "• <b>Compress</b> - Reduce video file size with quality options\n"
                        "• More tools coming soon (watermark, merge, etc.)\n\n"
                        f"⏱ <i>Session will timeout in {remaining} seconds</i>"
                    )
                elif session["stage"] == "resolution_select":
                    text = (
                        "<b>🗜️ Video Compression</b>\n\n"
                        "Select target resolution:\n"
                        "⚠️ <i>Lower resolution = smaller file size</i>\n"
                        "📝 <i>Videos won't be upscaled to prevent quality loss</i>\n\n"
                        f"⏱ <i>Selection timeout in {remaining} seconds</i>"
                    )
                else:
                    continue
                    
                buttons = session.get("buttons")
                if buttons:
                    await edit_message(session["message"], text, buttons)
            except Exception:
                pass


@new_task
async def vt_timeout_expired(client, user_id):
    """Handle timeout expiration"""
    if user_id in vt_handler_dict:
        session = vt_handler_dict[user_id]
        
        timeout_text = (
            "<b>⏱ Video Tools Session Timeout</b>\n\n"
            "Your session has expired. Use the video tools command again to continue.\n\n"
            "💡 <i>Tip: You have 60 seconds to make your selection</i>"
        )
        
        # Create restart button
        buttons = ButtonMaker()
        buttons.data_button("🔄 Restart", f"vt {user_id} restart")
        
        try:
            await edit_message(session["message"], timeout_text, buttons.build_menu(1))
        except Exception:
            pass
        
        # Clean up
        del vt_handler_dict[user_id]


@new_task
async def vt_callback_handler(client, query):
    """Handle Video Tools callback queries"""
    user_id = query.from_user.id
    data = query.data.split()
    
    if len(data) < 3:
        await query.answer("Invalid command", show_alert=True)
        return
    
    cmd_user_id = int(data[1])
    action = data[2]
    
    # Check if user owns this session
    if user_id != cmd_user_id:
        await query.answer("This is not your session!", show_alert=True)
        return
    
    if action == "compress":
        await show_resolution_menu(client, query)
    elif action == "cancel":
        await vt_cancel(client, query)
    elif action == "restart":
        await vt_restart(client, query)
    elif action.startswith("res_"):
        resolution = action.replace("res_", "")
        await start_compression(client, query, resolution)
    elif action == "back":
        await show_video_tools_menu(client, query.message)
    else:
        await query.answer("Unknown action", show_alert=True)


@new_task
async def show_resolution_menu(client, query):
    """Show resolution selection menu"""
    user_id = query.from_user.id
    await query.answer()
    
    if user_id not in vt_handler_dict:
        await query.answer("Session expired", show_alert=True)
        return
    
    # Update session
    vt_handler_dict[user_id]["stage"] = "resolution_select"
    vt_handler_dict[user_id]["start_time"] = time()  # Reset timeout
    
    # Create resolution buttons
    buttons = ButtonMaker()
    for resolution in RESOLUTION_SETTINGS.keys():
        buttons.data_button(f"📺 {resolution}", f"vt {user_id} res_{resolution}")
    
    buttons.data_button("⬅️ Back", f"vt {user_id} back")
    buttons.data_button("❌ Cancel", f"vt {user_id} cancel")
    
    # Store buttons for timeout updates
    vt_handler_dict[user_id]["buttons"] = buttons.build_menu(2)
    
    text = (
        "<b>🗜️ Video Compression</b>\n\n"
        "Select target resolution:\n"
        "⚠️ <i>Lower resolution = smaller file size</i>\n"
        "📝 <i>Videos won't be upscaled to prevent quality loss</i>\n\n"
        "⏱ <i>Selection timeout in 60 seconds</i>"
    )
    
    await edit_message(query.message, text, vt_handler_dict[user_id]["buttons"])


@new_task
async def start_compression(client, query, resolution):
    """Start video compression process"""
    user_id = query.from_user.id
    await query.answer(f"Starting compression to {resolution}...")
    
    # Clean up VT session
    if user_id in vt_handler_dict:
        del vt_handler_dict[user_id]
    
    # For now, show a placeholder message
    # In a real implementation, this would:
    # 1. Get the video file from the original command
    # 2. Start compression with progress tracking
    # 3. Upload the result
    
    text = (
        f"<b>🗜️ Video Compression Started</b>\n\n"
        f"Target Resolution: <code>{resolution}</code>\n"
        f"Quality: <code>{RESOLUTION_SETTINGS[resolution]['bitrate']}</code>\n\n"
        f"<i>This is a placeholder implementation.</i>\n"
        f"<i>In the full implementation, this would:</i>\n"
        f"• Process the video file with FFmpeg\n"
        f"• Show real-time progress\n"
        f"• Upload the compressed result\n\n"
        f"🔧 <b>Status:</b> Processing...\n"
        f"📊 <b>Progress:</b> 0%\n"
        f"⏱ <b>ETA:</b> Calculating..."
    )
    
    await edit_message(query.message, text)


@new_task
async def vt_cancel(client, query):
    """Cancel VT session"""
    user_id = query.from_user.id
    await query.answer("Video Tools cancelled")
    
    if user_id in vt_handler_dict:
        del vt_handler_dict[user_id]
    
    await delete_message(query.message)


@new_task
async def vt_restart(client, query):
    """Restart VT session"""
    user_id = query.from_user.id
    await query.answer("Restarting Video Tools...")
    
    if user_id in vt_handler_dict:
        del vt_handler_dict[user_id]
    
    await show_video_tools_menu(client, query.message)
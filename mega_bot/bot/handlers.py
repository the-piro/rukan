"""Telegram bot command handlers."""

from telegram import Update
from telegram.ext import ContextTypes

from mega_bot.logger import LOGGER
from mega_bot.utils.links import is_mega_link
from mega_bot.utils.formatting import truncate_string
from mega_bot.mega.downloader import queue_download, cancel_download
from mega_bot.task_manager import task_manager, TaskState


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    help_text = (
        "🚀 *MEGA Downloader Bot*\n\n"
        "Commands:\n"
        "• `/mega <link>` - Download MEGA file or folder\n"
        "• `/status` - Show active and recent downloads\n"
        "• `/cancel <gid>` - Cancel download by GID\n\n"
        "Send me a MEGA link to get started!"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def mega_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /mega command."""
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a MEGA link.\n"
            "Usage: `/mega <mega_link>`",
            parse_mode="Markdown"
        )
        return
    
    link = context.args[0]
    
    if not is_mega_link(link):
        await update.message.reply_text(
            "❌ Invalid MEGA link. Please provide a valid MEGA.nz link."
        )
        return
    
    try:
        gid = await queue_download(link)
        await update.message.reply_text(
            f"✅ Download queued!\n"
            f"🆔 GID: `{gid}`\n"
            f"🔗 Link: {truncate_string(link, 50)}\n\n"
            f"Use `/status` to check progress.",
            parse_mode="Markdown"
        )
        LOGGER.info(f"Queued download {gid} for user {update.effective_user.id}")
        
    except Exception as e:
        LOGGER.error(f"Error queuing download: {e}")
        await update.message.reply_text(
            f"❌ Error queuing download: {str(e)}"
        )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command."""
    active_tasks = task_manager.get_active_tasks()
    recent_tasks = task_manager.get_recent_tasks(5)
    
    message_parts = ["📊 *Download Status*\n"]
    
    if active_tasks:
        message_parts.append("🔄 *Active Downloads:*")
        for task in active_tasks:
            status_info = ""
            if task.status_obj:
                status_info = (
                    f"Progress: {task.status_obj.progress()}\n"
                    f"Speed: {task.status_obj.speed()}\n"
                    f"ETA: {task.status_obj.eta()}"
                )
            else:
                status_info = f"State: {task.state.value.title()}"
            
            message_parts.append(
                f"🆔 `{task.gid}`\n"
                f"📁 {truncate_string(task.name, 35)}\n"
                f"{status_info}\n"
            )
    else:
        message_parts.append("🔄 *Active Downloads:* None")
    
    if recent_tasks:
        message_parts.append("\n📋 *Recent Downloads:*")
        for task in recent_tasks:
            state_emoji = {
                TaskState.COMPLETED: "✅",
                TaskState.FAILED: "❌", 
                TaskState.CANCELLED: "🚫"
            }.get(task.state, "❓")
            
            message_parts.append(
                f"{state_emoji} `{task.gid}` - {truncate_string(task.name, 25)}"
            )
            
            if task.error and task.state == TaskState.FAILED:
                message_parts.append(f"   Error: {truncate_string(task.error, 40)}")
    
    if not active_tasks and not recent_tasks:
        message_parts.append("No downloads found.")
    
    await update.message.reply_text(
        "\n".join(message_parts),
        parse_mode="Markdown"
    )


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /cancel command."""
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a GID to cancel.\n"
            "Usage: `/cancel <gid>`",
            parse_mode="Markdown"
        )
        return
    
    gid = context.args[0]
    
    try:
        success = await cancel_download(gid)
        if success:
            await update.message.reply_text(
                f"✅ Download `{gid}` has been cancelled.",
                parse_mode="Markdown"
            )
            LOGGER.info(f"Cancelled download {gid} by user {update.effective_user.id}")
        else:
            await update.message.reply_text(
                f"❌ Could not cancel download `{gid}`. "
                f"It may not exist or already be completed.",
                parse_mode="Markdown"
            )
    except Exception as e:
        LOGGER.error(f"Error cancelling download {gid}: {e}")
        await update.message.reply_text(
            f"❌ Error cancelling download: {str(e)}"
        )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle plain text messages (check for MEGA links)."""
    text = update.message.text
    
    if is_mega_link(text):
        # Treat as /mega command
        context.args = [text]
        await mega_command(update, context)
    else:
        await update.message.reply_text(
            "Send me a MEGA link or use /help for available commands."
        )
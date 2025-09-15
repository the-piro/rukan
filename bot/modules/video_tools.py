import asyncio
import uuid
from typing import Dict, Optional, Tuple

from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.telegram_helper.message_utils import send_message, edit_message
from bot.helper.ext_utils.bot_utils import new_task

# token -> (future, chat_id, message_id, user_id)
_pending: Dict[str, Tuple[asyncio.Future, int, int, int]] = {}
_timeout_tasks: Dict[str, asyncio.Task] = {}

VT_TITLE = "Video Tools"
COMPRESS_TITLE = "Compress"


async def open_vt_menu(message) -> str:
    """
    Sends a new VT menu message (first one must be new to avoid MESSAGE_ID_INVALID),
    returns a token to be used for awaiting the user's resolution selection.
    """
    token = uuid.uuid4().hex
    user_id = message.from_user.id
    chat_id = message.chat.id

    buttons = ButtonMaker()
    buttons.data_button(COMPRESS_TITLE, f"vt comp {token}")
    buttons.data_button("Close", f"vt close {token}")
    vt_text = f"<b>{VT_TITLE}</b>\n\nSelect a tool. Time Left : <code>60 sec</code>"

    vt_msg = await send_message(message, vt_text, buttons.build_menu(2))

    fut: asyncio.Future = asyncio.get_running_loop().create_future()
    _pending[token] = (fut, chat_id, vt_msg.id, user_id)

    # Start 60s timeout
    _timeout_tasks[token] = asyncio.create_task(_timeout_vt(token))
    return token


async def wait_for_resolution(token: str, timeout: int = 60) -> Optional[int]:
    """
    Await the chosen resolution. Returns None if timed out or closed.
    """
    if token not in _pending:
        return None
    fut, _, _, _ = _pending[token]
    try:
        res = await asyncio.wait_for(fut, timeout=timeout)
        return res if isinstance(res, int) else None
    except asyncio.TimeoutError:
        return None
    finally:
        # Cleanup is handled in _resolve/_timeout
        pass


async def _timeout_vt(token: str):
    await asyncio.sleep(60)
    if token not in _pending:
        return
    fut, chat_id, msg_id, _ = _pending[token]
    if not fut.done():
        try:
            await edit_message(
                (chat_id, msg_id),
                f"<b>{VT_TITLE}</b>\n\nTimed out. Please run /cmd with -vt again."
            )
        except Exception:
            pass
        fut.set_result(None)
    _cleanup(token)


def _cleanup(token: str):
    _pending.pop(token, None)
    task = _timeout_tasks.pop(token, None)
    if task and not task.done():
        task.cancel()


def _resolution_buttons(token: str):
    buttons = ButtonMaker()
    for label, height in [
        ("144p", 144), ("240p", 240), ("360p", 360),
        ("480p", 480), ("720p", 720), ("1080p", 1080),
    ]:
        buttons.data_button(label, f"vt res {token} {height}")
    buttons.data_button("Back", f"vt back {token}")
    buttons.data_button("Close", f"vt close {token}")
    return buttons.build_menu(3)


@new_task
async def video_tools_cb(_, query):
    """
    Callback handler for VT menus.
    data formats:
      - "vt comp <token>" -> Show compression resolution menu (edit same message)
      - "vt res <token> <height>" -> Select resolution and resolve
      - "vt back <token>" -> Back to the main VT menu
      - "vt close <token>" -> Close VT and resolve as None
    """
    try:
        data = query.data.split()
        if not data or data[0] != "vt":
            return
        action = data[1]
        token = data[2] if len(data) > 2 else None
        if token not in _pending:
            return

        fut, chat_id, msg_id, owner_id = _pending[token]
        # Only allow the initiating user to interact
        if query.from_user.id != owner_id:
            return

        if action == "comp":
            # Edit to show resolution options
            buttons = _resolution_buttons(token)
            await edit_message(
                (chat_id, msg_id),
                f"<b>{VT_TITLE} → {COMPRESS_TITLE}</b>\n\nChoose a resolution. Time Left : <code>60 sec</code>",
                buttons
            )
        elif action == "res":
            # Resolve with chosen height
            if len(data) < 4:
                return
            try:
                height = int(data[3])
            except ValueError:
                return
            if not fut.done():
                fut.set_result(height)
            try:
                await edit_message(
                    (chat_id, msg_id),
                    f"<b>{VT_TITLE} → {COMPRESS_TITLE}</b>\n\nSelected: <b>{height}p</b>."
                )
            except Exception:
                pass
            _cleanup(token)
        elif action == "back":
            # Back to main VT menu
            buttons = ButtonMaker()
            buttons.data_button(COMPRESS_TITLE, f"vt comp {token}")
            buttons.data_button("Close", f"vt close {token}")
            await edit_message(
                (chat_id, msg_id),
                f"<b>{VT_TITLE}</b>\n\nSelect a tool. Time Left : <code>60 sec</code>",
                buttons.build_menu(2)
            )
        elif action == "close":
            if not fut.done():
                fut.set_result(None)
            try:
                await edit_message(
                    (chat_id, msg_id),
                    f"<b>{VT_TITLE}</b>\n\nClosed."
                )
            except Exception:
                pass
            _cleanup(token)
    except Exception:
        # Fail-safe cleanup on unexpected errors related to this token
        if "token" in locals():
            _cleanup(token)

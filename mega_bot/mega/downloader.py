"""MEGA downloader orchestration."""

import os
from secrets import token_hex
from typing import Optional

from mega import MegaApi

from ..config import Config
from ..logger import LOGGER
from ..utils.links import get_mega_link_type
from .async_mega import AsyncMega, sync_to_async
from .listener import MegaAppListener
from .status import MegaDownloadStatus


async def queue_download(link: str, name: Optional[str] = None) -> str:
    """Queue a MEGA download and return GID."""
    from mega_bot.task_manager import task_manager

    gid = token_hex(5)
    display_name = name or "Unknown"

    await task_manager.add_task(gid, link, display_name)

    # Start workers if not already started
    await task_manager.start_workers()

    return gid


async def cancel_download(gid: str) -> bool:
    """Cancel a download by GID."""
    from mega_bot.task_manager import task_manager

    return await task_manager.cancel_task(gid)


async def get_status(gid: str) -> Optional[object]:
    """Get download status by GID."""
    from mega_bot.task_manager import task_manager

    task = task_manager.get_task(gid)
    return task.status_obj if task else None


async def start_mega_download(link: str, gid: str, task_manager) -> None:
    """Start actual MEGA download process."""
    async_api = AsyncMega()
    async_api.api = MegaApi(None, None, None, "MEGA-Bot")
    folder_api = None

    mega_listener = MegaAppListener(async_api.continue_event, gid, task_manager)
    async_api.api.addListener(mega_listener)

    try:
        # Login if credentials provided
        if Config.MEGA_EMAIL and Config.MEGA_PASSWORD:
            LOGGER.info(f"Logging into MEGA for download {gid}")
            await async_api.login(Config.MEGA_EMAIL, Config.MEGA_PASSWORD)

        # Handle file vs folder
        link_type = get_mega_link_type(link)

        if link_type == "file":
            LOGGER.info(f"Processing MEGA file link for {gid}")
            await async_api.getPublicNode(link)
            node = mega_listener.public_node
        else:
            LOGGER.info(f"Processing MEGA folder link for {gid}")
            async_api.folder_api = folder_api = MegaApi(None, None, None, "MEGA-Bot")
            folder_api.addListener(mega_listener)

            await async_api.run(folder_api.loginToFolder, link)
            LOGGER.info(f"Folder login node for {gid}: {mega_listener.node.getName()}")

            node = await sync_to_async(folder_api.authorizeNode, mega_listener.node)
            LOGGER.info(f"Authorized node for {gid}: {node.getName()}")

            # For folders, we'll download the main folder
            # TODO: Implement recursive folder download in future version

        if mega_listener.error:
            await task_manager.fail_task(gid, mega_listener.error)
            return

        # Get file size
        file_size = await sync_to_async(async_api.api.getSize, node)

        # Create status object
        status_obj = MegaDownloadStatus(
            gid, mega_listener.name, file_size, mega_listener
        )
        await task_manager.update_task_status(gid, status_obj)

        # Ensure download directory exists
        download_dir = Config.DOWNLOAD_DIR
        os.makedirs(download_dir, exist_ok=True)

        # Start download
        LOGGER.info(f"Starting download for {gid}: {mega_listener.name}")
        await async_api.startDownload(
            node, download_dir, mega_listener.name, None, False, None
        )

    except Exception as e:
        LOGGER.error(f"Error in MEGA download {gid}: {e}")
        await task_manager.fail_task(gid, str(e))
    finally:
        # Cleanup
        try:
            await async_api.logout()
        except Exception as e:
            LOGGER.error(f"Error during MEGA logout for {gid}: {e}")

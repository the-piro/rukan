import asyncio
from secrets import token_hex
from aiofiles.os import makedirs

from mega_downloader.mega.listener import AsyncMega, MegaAppListener, sync_to_async, MegaApi, MEGA_AVAILABLE
from mega_downloader.core.config import Config
from mega_downloader.core.logger import LOGGER
from mega_downloader.utils.links import get_mega_link_type
from mega_downloader.mega.status import MegaDownloadStatus
from mega_downloader.runtime.tasks import task_dict, task_dict_lock

class SimpleListener:
    def __init__(self, link: str):
        self.link = link
        self.name: str | None = None
        self.mid = token_hex(4)
        self.size = 0
        self.is_cancelled = False
        self.multi = 1

    async def on_download_error(self, msg, button=None, is_limit=False):
        LOGGER.error(f"Download error: {msg}")

    async def on_download_start(self):
        LOGGER.info(f"Starting download: {self.name}")

    def on_download_complete(self):
        LOGGER.info(f"Download complete: {self.name}")
        return None  # Return None for sync method

async def start_mega_download(link: str, output_dir: str | None = None):
    if not MEGA_AVAILABLE:
        LOGGER.warning("Mega SDK not available. This is a mock run for testing.")
    
    listener = SimpleListener(link)
    cfg = Config()
    path = output_dir or cfg.DOWNLOAD_DIR

    async_api = AsyncMega()
    async_api.api = api = MegaApi(None, None, None, cfg.APP_ID)

    mega_listener = MegaAppListener(async_api.continue_event, listener)
    api.addListener(mega_listener)

    if cfg.MEGA_EMAIL and cfg.MEGA_PASSWORD:
        await async_api.login(cfg.MEGA_EMAIL, cfg.MEGA_PASSWORD)

    link_type = get_mega_link_type(listener.link)
    if link_type == "file":
        await async_api.getPublicNode(listener.link)
        node = mega_listener.public_node
    else:
        async_api.folder_api = folder_api = MegaApi(None, None, None, cfg.APP_ID)
        folder_api.addListener(mega_listener)
        await async_api.run(folder_api.loginToFolder, listener.link)
        node = await sync_to_async(folder_api.authorizeNode, mega_listener.node)
        # TODO: (Future) enumerate children nodes for folder recursive download

    if mega_listener.error:
        await listener.on_download_error(str(mega_listener.error))
        await async_api.logout()
        return None

    listener.name = listener.name or node.getName()
    gid = token_hex(5)

    # Obtain size (original: api.getSize(node) via sync_to_async). Here we assume immediate.
    try:
        listener.size = await sync_to_async(api.getSize, node)
    except Exception:
        listener.size = 0

    async with task_dict_lock:
        task_dict[listener.mid] = MegaDownloadStatus(listener, mega_listener, gid, "dl")

    await listener.on_download_start()
    await makedirs(path, exist_ok=True)

    if not MEGA_AVAILABLE:
        LOGGER.info("Mock download simulation completed.")
        listener.on_download_complete()
        return f"{path}/{listener.name}"

    await async_api.startDownload(node, path, listener.name, None, False, None)
    # Control returns when listener sets continue_event; completion callback invoked by MegaAppListener

    await async_api.logout()
    return f"{path}/{listener.name}"
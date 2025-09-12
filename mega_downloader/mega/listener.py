from asyncio import Event
from mega_downloader.core.logger import LOGGER

# Try to import mega SDK, use mock if not available
try:
    from mega import MegaApi, MegaError, MegaListener, MegaRequest, MegaTransfer
    MEGA_AVAILABLE = True
except ImportError:
    LOGGER.warning("Mega SDK not available. Using mock classes for testing.")
    MEGA_AVAILABLE = False
    
    # Mock classes for testing when mega SDK is not available
    class MegaApi:
        def __init__(self, *args, **kwargs):
            self.listeners = []
        def addListener(self, listener):
            self.listeners.append(listener)
        def logout(self):
            pass
        def getSize(self, node):
            return 1024 * 1024  # 1MB mock size
        def fetchNodes(self):
            pass
        def getRootNode(self):
            return MockNode()
        def authorizeNode(self, node):
            return node
        def loginToFolder(self, link):
            pass
        def getPublicNode(self, link):
            pass
        def startDownload(self, node, path, name, app_data, start_first, cancel_token):
            pass
    
    class MegaError:
        def toString(self):
            return "Mock error"
        def copy(self):
            return self
    
    class MegaListener:
        def __init__(self):
            pass
    
    class MegaRequest:
        TYPE_LOGIN = 1
        TYPE_FETCH_NODES = 2
        TYPE_GET_PUBLIC_NODE = 3
        
        def getType(self):
            return self.TYPE_GET_PUBLIC_NODE
        def getPublicMegaNode(self):
            return MockNode()
    
    class MegaTransfer:
        def getSpeed(self):
            return 1024 * 10  # 10KB/s mock speed
        def getTransferredBytes(self):
            return 0
        def isFinished(self):
            return True
        def isFolderTransfer(self):
            return False
        def getFileName(self):
            return "mock_file.txt"
        def getState(self):
            return 0
        def cancelTransfer(self, transfer, listener):
            pass
    
    class MockNode:
        def getName(self):
            return "mock_file.txt"


def async_to_sync(func, *args, **kwargs):
    """Simple async to sync helper - minimal implementation for standalone use."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an async context, we can't use run_until_complete
            # This is a limitation for now
            raise RuntimeError("Cannot run async_to_sync from within an async context")
        return loop.run_until_complete(func(*args, **kwargs))
    except RuntimeError:
        # Try creating a new loop
        return asyncio.run(func(*args, **kwargs))


async def sync_to_async(func, *args, **kwargs):
    """Simple sync to async helper - minimal implementation for standalone use."""
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args, **kwargs)


class AsyncMega:
    def __init__(self):
        self.api = None
        self.folder_api = None
        self.continue_event = Event()

    async def run(self, function, *args, **kwargs):
        self.continue_event.clear()
        await sync_to_async(function, *args, **kwargs)
        # In mock mode, don't wait indefinitely
        if not MEGA_AVAILABLE:
            self.continue_event.set()
        await self.continue_event.wait()

    async def logout(self):
        if MEGA_AVAILABLE:
            await self.run(self.api.logout)
            if self.folder_api:
                await self.run(self.folder_api.logout)
        else:
            # Mock logout is instant
            pass

    def __getattr__(self, name):
        if not MEGA_AVAILABLE:
            # For mock mode, return a simple async function that sets the event
            async def mock_wrapper(*args, **kwargs):
                self.continue_event.set()
                return None
            return mock_wrapper
        
        attr = getattr(self.api, name)
        if callable(attr):

            async def wrapper(*args, **kwargs):
                return await self.run(attr, *args, **kwargs)

            return wrapper
        return attr


class MegaAppListener(MegaListener):
    _NO_EVENT_ON = (MegaRequest.TYPE_LOGIN, MegaRequest.TYPE_FETCH_NODES) if MEGA_AVAILABLE else (1, 2)

    def __init__(self, continue_event: Event, listener):
        self.continue_event = continue_event
        self.node = None
        self.public_node = None
        self.listener = listener
        self.is_cancelled = False
        self.error = None
        self._bytes_transferred = 0
        self._speed = 0
        self._name = ""
        super().__init__()
        
        # For mock mode, simulate having a public node available
        if not MEGA_AVAILABLE:
            class MockNode:
                def getName(self):
                    return "mock_file.txt"
            self.public_node = MockNode()
            self.node = MockNode()

    @property
    def speed(self):
        return self._speed

    @property
    def downloaded_bytes(self):
        return self._bytes_transferred

    def onRequestFinish(self, api, request, error):
        if str(error).lower() != "no error":
            self.error = error.copy()
            if str(self.error).casefold() != "not found":
                LOGGER.error(f"Mega onRequestFinishError: {self.error}")
            self.continue_event.set()
            return

        request_type = request.getType()

        if request_type == MegaRequest.TYPE_LOGIN:
            api.fetchNodes()
        elif request_type == MegaRequest.TYPE_GET_PUBLIC_NODE:
            self.public_node = request.getPublicMegaNode()
            self._name = self.public_node.getName()
        elif request_type == MegaRequest.TYPE_FETCH_NODES:
            LOGGER.info("Fetching Root Node.")
            self.node = api.getRootNode()
            self._name = self.node.getName()
            LOGGER.info(f"Node Name: {self.node.getName()}")

        if request_type not in self._NO_EVENT_ON or (
            self.node and "cloud drive" not in self._name.lower()
        ):
            self.continue_event.set()

    def onRequestTemporaryError(self, api, request, error: MegaError):
        LOGGER.error(f"Mega Request error in {error}")
        if not self.is_cancelled:
            self.is_cancelled = True
            async_to_sync(
                self.listener.on_download_error, f"RequestTempError: {error.toString()}"
            )
        self.error = error.toString()
        self.continue_event.set()

    def onTransferUpdate(self, api: MegaApi, transfer: MegaTransfer):
        if self.is_cancelled:
            api.cancelTransfer(transfer, None)
            self.continue_event.set()
            return
        self._speed = transfer.getSpeed()
        self._bytes_transferred = transfer.getTransferredBytes()

    def onTransferFinish(self, api: MegaApi, transfer: MegaTransfer, error):
        try:
            if self.is_cancelled:
                self.continue_event.set()
            elif transfer.isFinished() and (
                transfer.isFolderTransfer() or transfer.getFileName() == self._name
            ):
                async_to_sync(self.listener.on_download_complete)
                self.continue_event.set()
        except Exception as e:
            LOGGER.error(e)

    def onTransferTemporaryError(self, api, transfer, error):
        LOGGER.error(f"Mega download error in file {transfer.getFileName()}: {error}")
        if transfer.getState() in [1, 4]:
            return
        self.error = f"TransferTempError: {error.toString()} ({transfer.getFileName()})"
        if not self.is_cancelled:
            self.is_cancelled = True
            self.continue_event.set()

    async def cancel_task(self):
        self.is_cancelled = True
        await self.listener.on_download_error("Download Canceled by user")
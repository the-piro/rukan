"""MEGA API event listener for download operations."""

import asyncio
from typing import Optional

from mega import MegaApi, MegaError, MegaListener, MegaRequest, MegaTransfer

from ..logger import LOGGER


class MegaAppListener(MegaListener):
    """MEGA API event listener."""

    _NO_EVENT_ON = (MegaRequest.TYPE_LOGIN, MegaRequest.TYPE_FETCH_NODES)

    def __init__(self, continue_event: asyncio.Event, gid: str, task_manager):
        self.continue_event = continue_event
        self.gid = gid
        self.task_manager = task_manager
        self.node = None
        self.public_node = None
        self.is_cancelled = False
        self.error: Optional[str] = None
        self._bytes_transferred = 0
        self._speed = 0
        self._name = ""
        super().__init__()

    @property
    def speed(self) -> float:
        """Get current download speed."""
        return self._speed

    @property
    def downloaded_bytes(self) -> int:
        """Get total downloaded bytes."""
        return self._bytes_transferred

    @property
    def name(self) -> str:
        """Get download name."""
        return self._name

    def onRequestFinish(self, api: MegaApi, request: MegaRequest, error: MegaError):
        """Handle MEGA API request completion."""
        if str(error).lower() != "no error":
            self.error = str(error)
            if str(error).casefold() != "not found":
                LOGGER.error(f"MEGA API error for {self.gid}: {error}")
            self.continue_event.set()
            return

        request_type = request.getType()

        if request_type == MegaRequest.TYPE_LOGIN:
            api.fetchNodes()
        elif request_type == MegaRequest.TYPE_GET_PUBLIC_NODE:
            self.public_node = request.getPublicMegaNode()
            self._name = self.public_node.getName()
        elif request_type == MegaRequest.TYPE_FETCH_NODES:
            LOGGER.info(f"Fetching root node for {self.gid}")
            self.node = api.getRootNode()
            self._name = self.node.getName()
            LOGGER.info(f"Node name for {self.gid}: {self.node.getName()}")

        if request_type not in self._NO_EVENT_ON or (
            self.node and "cloud drive" not in self._name.lower()
        ):
            self.continue_event.set()

    def onRequestTemporaryError(
        self, api: MegaApi, request: MegaRequest, error: MegaError
    ):
        """Handle MEGA API temporary errors."""
        LOGGER.error(f"MEGA temporary error for {self.gid}: {error}")
        if not self.is_cancelled:
            self.is_cancelled = True
            self.error = f"RequestTempError: {error.toString()}"
            asyncio.create_task(self.task_manager.fail_task(self.gid, self.error))
        self.continue_event.set()

    def onTransferUpdate(self, api: MegaApi, transfer: MegaTransfer):
        """Handle transfer progress updates."""
        if self.is_cancelled:
            api.cancelTransfer(transfer, None)
            self.continue_event.set()
            return

        self._speed = transfer.getSpeed()
        self._bytes_transferred = transfer.getTransferredBytes()

    def onTransferFinish(self, api: MegaApi, transfer: MegaTransfer, error: MegaError):
        """Handle transfer completion."""
        try:
            if self.is_cancelled:
                self.continue_event.set()
            elif transfer.isFinished() and (
                transfer.isFolderTransfer() or transfer.getFileName() == self._name
            ):
                LOGGER.info(f"Download completed for {self.gid}: {self._name}")
                asyncio.create_task(self.task_manager.complete_task(self.gid))
                self.continue_event.set()
        except Exception as e:
            LOGGER.error(f"Error in transfer finish for {self.gid}: {e}")

    def onTransferTemporaryError(
        self, api: MegaApi, transfer: MegaTransfer, error: MegaError
    ):
        """Handle transfer temporary errors."""
        LOGGER.error(
            f"MEGA transfer error for {self.gid} in file {transfer.getFileName()}: {error}"
        )
        if transfer.getState() in [1, 4]:  # Skip certain states
            return

        self.error = f"TransferTempError: {error.toString()} ({transfer.getFileName()})"
        if not self.is_cancelled:
            self.is_cancelled = True
            self.continue_event.set()

    async def cancel_task(self):
        """Cancel the current download task."""
        self.is_cancelled = True
        LOGGER.info(f"Download cancelled for {self.gid}")
        await self.task_manager.fail_task(self.gid, "Download cancelled by user")

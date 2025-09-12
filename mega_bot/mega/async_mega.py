"""Async wrapper for MEGA API operations."""

import asyncio
from typing import Optional
from mega import MegaApi


def sync_to_async(func, *args, **kwargs):
    """Convert sync function to async."""
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, func, *args, **kwargs)


class AsyncMega:
    """Async wrapper for MEGA API."""

    def __init__(self):
        self.api: Optional[MegaApi] = None
        self.folder_api: Optional[MegaApi] = None
        self.continue_event = asyncio.Event()

    async def run(self, function, *args, **kwargs):
        """Execute a MEGA API function asynchronously."""
        self.continue_event.clear()
        await sync_to_async(function, *args, **kwargs)
        await self.continue_event.wait()

    async def logout(self):
        """Logout from MEGA APIs."""
        if self.api:
            await self.run(self.api.logout)
        if self.folder_api:
            await self.run(self.folder_api.logout)

    def __getattr__(self, name):
        """Delegate attribute access to the MEGA API."""
        if not self.api:
            raise AttributeError("AsyncMega API not initialized")

        attr = getattr(self.api, name)
        if callable(attr):

            async def wrapper(*args, **kwargs):
                return await self.run(attr, *args, **kwargs)

            return wrapper
        return attr

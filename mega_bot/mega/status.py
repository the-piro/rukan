"""Status tracking for MEGA downloads."""

from ..utils.formatting import get_readable_file_size, get_readable_time


class MegaDownloadStatus:
    """Status tracker for MEGA downloads."""

    def __init__(self, gid: str, name: str, size: int, listener):
        self._gid = gid
        self._name = name
        self._size = size
        self._listener = listener

    def gid(self) -> str:
        """Get download GID."""
        return self._gid

    def name(self) -> str:
        """Get download name."""
        return self._name

    def size(self) -> str:
        """Get total file size as human readable string."""
        return get_readable_file_size(self._size)

    def processed_bytes(self) -> str:
        """Get downloaded bytes as human readable string."""
        return get_readable_file_size(self._listener.downloaded_bytes)

    def progress_raw(self) -> float:
        """Get progress as percentage (0-100)."""
        try:
            return round(self._listener.downloaded_bytes / self._size * 100, 2)
        except ZeroDivisionError:
            return 0.0

    def progress(self) -> str:
        """Get progress as percentage string."""
        return f"{self.progress_raw()}%"

    def speed(self) -> str:
        """Get download speed as human readable string."""
        return f"{get_readable_file_size(self._listener.speed)}/s"

    def eta(self) -> str:
        """Get estimated time of arrival."""
        try:
            remaining_bytes = self._size - self._listener.downloaded_bytes
            if remaining_bytes <= 0 or self._listener.speed <= 0:
                return "-"
            seconds = remaining_bytes / self._listener.speed
            return get_readable_time(seconds)
        except (ZeroDivisionError, AttributeError):
            return "-"

    async def cancel_task(self):
        """Cancel the download task."""
        if hasattr(self._listener, "cancel_task"):
            await self._listener.cancel_task()

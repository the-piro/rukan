"""Link validation and type detection utilities."""

from typing import Literal


def is_mega_link(url: str) -> bool:
    """Check if URL is a MEGA link."""
    return "mega.nz" in url or "mega.co.nz" in url


def get_mega_link_type(url: str) -> Literal["file", "folder"]:
    """Determine if MEGA link is for a file or folder."""
    return "folder" if "folder" in url or "/#F!" in url else "file"
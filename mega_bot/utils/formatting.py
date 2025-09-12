"""Formatting utilities for file sizes, times, and display."""

from typing import Union


def get_readable_file_size(size_bytes: Union[int, float]) -> str:
    """Convert bytes to human readable file size."""
    if size_bytes == 0:
        return "0 B"
    
    size_bytes = float(size_bytes)
    size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
    i = 0
    
    while size_bytes >= 1024.0 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    if i == 0:
        return f"{int(size_bytes)} {size_names[i]}"
    else:
        return f"{size_bytes:.2f} {size_names[i]}"


def get_readable_time(seconds: Union[int, float]) -> str:
    """Convert seconds to human readable time."""
    if seconds <= 0:
        return "-"
    
    seconds = int(seconds)
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds or not parts:
        parts.append(f"{seconds}s")
    
    return " ".join(parts)


def truncate_string(text: str, max_length: int = 40) -> str:
    """Truncate string with ellipsis if too long."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."
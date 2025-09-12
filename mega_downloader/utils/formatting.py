def get_readable_file_size(size: int) -> str:
    if size is None:
        return "0B"
    step = 1024.0
    units = ["B","KB","MB","GB","TB"]
    idx = 0
    size_f = float(size)
    while size_f >= step and idx < len(units)-1:
        size_f /= step
        idx += 1
    return f"{size_f:.2f}{units[idx]}"

def get_readable_time(seconds: float) -> str:
    if seconds <= 0:
        return "-"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"
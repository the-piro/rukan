def is_mega_link(url: str):
    return "mega.nz" in url or "mega.co.nz" in url

def get_mega_link_type(url: str):
    return "folder" if "folder" in url or "/#F!" in url else "file"
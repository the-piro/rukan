import logging, sys
LOGGER = logging.getLogger("mega_downloader")
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
LOGGER.addHandler(_handler)
LOGGER.setLevel(logging.INFO)
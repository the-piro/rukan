import argparse
import asyncio
import time
from mega_downloader.core.logger import LOGGER
from mega_downloader.mega.download import start_mega_download
from mega_downloader.runtime.tasks import task_dict


def parse_args():
    p = argparse.ArgumentParser(description="Standalone MEGA Downloader")
    p.add_argument("link", help="Public MEGA link (file or folder)")
    p.add_argument("-o", "--output", help="Output directory", default=None)
    return p.parse_args()


def main():
    args = parse_args()
    LOGGER.info("Launching MEGA download...")
    # Run download inside inner coroutine so we can poll progress concurrently.
    async def runner():
        task_path = None
        download_coro = start_mega_download(args.link, args.output)
        # Run the download task
        dl_task = asyncio.create_task(download_coro)
        last_report = 0
        while not dl_task.done():
            await asyncio.sleep(1)
            now = time.time()
            if now - last_report >= 2:
                # Poll the first status object (only one active at CLI usage)
                for status in list(task_dict.values()):
                    try:
                        LOGGER.info(
                            f"[Progress] {status.name()} | {status.progress()} | "
                            f"{status.processed_bytes()}/{status.size()} | "
                            f"{status.speed()} | ETA {status.eta()}"
                        )
                    except Exception:
                        pass
                last_report = now
        task_path = await dl_task
        return task_path

    out = asyncio.run(runner())
    if out:
        LOGGER.info(f"Download finished: {out}")


if __name__ == "__main__":
    main()
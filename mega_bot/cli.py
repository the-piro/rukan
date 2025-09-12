"""CLI interface for direct MEGA downloads."""

import asyncio
import sys
import time

from mega_bot.utils.links import is_mega_link
from mega_bot.mega.downloader import queue_download
from mega_bot.task_manager import task_manager, TaskState


async def cli_download(link: str) -> None:
    """Download MEGA link via CLI with progress updates."""
    if not is_mega_link(link):
        print("❌ Error: Invalid MEGA link")
        sys.exit(1)

    print(f"🔗 Starting download: {link}")

    try:
        # Queue the download
        gid = await queue_download(link)
        print(f"🆔 Download GID: {gid}")

        # Wait for download to start and monitor progress
        last_progress = -1
        start_time = time.time()

        while True:
            await asyncio.sleep(2)  # Update every 2 seconds

            task = task_manager.get_task(gid)
            if not task:
                print("❌ Error: Task not found")
                break

            if task.state == TaskState.COMPLETED:
                elapsed = time.time() - start_time
                print(f"✅ Download completed in {elapsed:.1f} seconds")
                print(f"📁 File: {task.name}")
                break
            elif task.state == TaskState.FAILED:
                print(f"❌ Download failed: {task.error}")
                sys.exit(1)
            elif task.state == TaskState.CANCELLED:
                print("🚫 Download was cancelled")
                sys.exit(1)
            elif task.state == TaskState.RUNNING and task.status_obj:
                # Show progress
                status = task.status_obj
                progress = status.progress_raw()

                if abs(progress - last_progress) >= 1.0 or last_progress == -1:
                    print(
                        f"📊 {status.progress()} | "
                        f"💾 {status.processed_bytes()}/{status.size()} | "
                        f"🚀 {status.speed()} | "
                        f"⏱️ ETA: {status.eta()}"
                    )
                    last_progress = progress
            elif task.state == TaskState.QUEUED:
                print("⏳ Download queued, waiting to start...")

    except KeyboardInterrupt:
        print("\n🚫 Download interrupted by user")
        if "gid" in locals():
            await task_manager.cancel_task(gid)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def main():
    """CLI entry point."""
    if len(sys.argv) != 2:
        print("Usage: python -m mega_bot.cli <mega_link>")
        sys.exit(1)

    link = sys.argv[1]

    try:
        asyncio.run(cli_download(link))
    except KeyboardInterrupt:
        print("\n🚫 Interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()

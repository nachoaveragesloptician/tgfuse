import os
import sys
import asyncio

if __package__ in (None, ""):
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tgfuse.config.config import Config
from tgfuse.config import logging_config
log = logging_config.setup_logging(__name__)

def run():
    if len(sys.argv) < 2 or sys.argv[1] not in ["mount", "upload"]:
        print("Usage: tgfuse <command> [args...]")
        print("\nCommands:")
        print("  mount    Mount the Telegram file system (e.g., tgfuse mount /mnt/path)")
        print("  upload   Upload a file to the FUSE mount (e.g., tgfuse upload file.mp4 -t video)")
        sys.exit(1)

    command = sys.argv.pop(1)

    if not Config.tg_id or not Config.tg_hash:
        log.error("Please set TG_ID and TG_HASH environment variables or .env values.")
        sys.exit(1)

    if command == "mount":
        from tgfuse.core.tg import start_bot
        log.info(f"Script initialization, logging level: {Config.log_level}")
        try:
            asyncio.run(start_bot())
        except KeyboardInterrupt:
            log.info("Received Ctrl+C - exiting.")
    
    elif command == "upload":
        from tgfuse.core.upload import run as upload_run
        upload_run()

if __name__ == "__main__":
    run()
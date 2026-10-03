import os
import sys
import time
import asyncio
import subprocess

if __package__ in (None, ""):
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tgfuse.config.config import Config
from tgfuse.config import logging_config
log = logging_config.setup_logging(__name__)

def run():
    if len(sys.argv) < 2 or sys.argv[1] not in ["mount", "unmount", "upload"]:
        print("Usage: tgfuse <command> [args...]")
        print("\nCommands:")
        print("  mount    Mount remote (e.g., tgfuse mount myremote: /mnt/path [--daemon])")
        print("  unmount  Stop daemon and unmount (e.g., tgfuse unmount /mnt/path)")
        print("  upload   Upload file (e.g., tgfuse upload myremote: file.mp4 -t video)")
        sys.exit(1)

    command = sys.argv.pop(1)

    if command == "unmount":
        if len(sys.argv) < 2:
            print("Usage: tgfuse unmount /mnt/path")
            sys.exit(1)
        mountpoint = sys.argv[1]
        print(f"Stopping daemon and unmounting {mountpoint}...")
        subprocess.run(["fusermount", "-u", mountpoint])
        sys.exit(0)

    remote_name = None
    if len(sys.argv) > 1 and sys.argv[1].endswith(":"):
        remote_name = sys.argv.pop(1)[:-1]

    if command == "mount":
        if "--daemon" in sys.argv:
            sys.argv.remove("--daemon")
            
            mountpoint = next((arg for arg in sys.argv[1:] if not arg.startswith("-")), None)

            print(f"Starting tgfuse daemon in background for '{remote_name or 'default'}'...")
            
            binary = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(sys.argv[0])
            cmd = [binary, "mount"]
                
            if remote_name:
                cmd.append(f"{remote_name}:")
            cmd.extend(sys.argv[1:])

            clean_env = os.environ.copy()
            for key in list(clean_env.keys()):
                if key.startswith(('_MEI', 'PYI', '_PYI')):
                    clean_env.pop(key)
                    
            if 'LD_LIBRARY_PATH_ORIG' in clean_env:
                clean_env['LD_LIBRARY_PATH'] = clean_env.pop('LD_LIBRARY_PATH_ORIG')
            else:
                clean_env.pop('LD_LIBRARY_PATH', None)

            log_path = os.path.expanduser("~/.config/tgfuse/daemon.log")
            with open(log_path, "a") as log_file:
                child = subprocess.Popen(
                    cmd,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    start_new_session=True,
                    env=clean_env
                )
            
            if mountpoint:
                print(f"Waiting for {mountpoint} to mount", end="", flush=True)
                timeout = 120
                start_time = time.time()
                while time.time() - start_time < timeout:
                    if os.path.ismount(mountpoint):
                        print(" Successfully mounted!")
                        sys.exit(0)
                    
                    if child.poll() is not None:
                        print(f"\nError: Daemon crashed! Check {log_path} for details.")
                        sys.exit(1)
                        
                    time.sleep(0.5)
                    print(".", end="", flush=True)
                print("\nTimeout waiting for mount, but daemon is still running. Check logs.")
            sys.exit(0)

    Config.load(remote_name)

    if not Config.tg_id or not Config.tg_hash:
        log.error(f"Missing config. Configure remote '{remote_name or 'default'}' in ~/.config/tgfuse/config.ini or set .env values.")
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
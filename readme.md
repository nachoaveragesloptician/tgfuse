
# tgfuse

Mount a Telegram channel as a local directory to browse, play, and stream files natively, with a built-in high-speed CLI uploader.

### Setup

```bash
git clone [https://github.com/nachoaveragesloptician/tgfuse.git](https://github.com/nachoaveragesloptician/tgfuse.git)
cd tgfuse
uv pip install -e .

```

*Install fuse3 dependency based on your OS:*

* **Debian/Ubuntu:** `sudo apt install libfuse3-dev`
* **Fedora:** `sudo dnf install fuse3-devel`
* **Arch:** `sudo pacman -S fuse3`

### Build (PyInstaller)

To compile a self-contained, standalone binary for deployment:

```bash
uv run pyinstaller --onefile --name tgfuse --collect-all tgfuse run.py

```

*The compiled executable will be output to `./dist/tgfuse`.*

### Configuration (`config.ini`)

Create a `config.ini` file in your working directory. `tgfuse` supports **multi-channel profiles**, allowing you to configure and interact with multiple Telegram channels independently.

```ini
# The default profile
[default]
api_id = your_api_id
api_hash = your_api_hash
chat_id = -1001234567890
bot_token = your_bot_token
# Optional: Filter which files to mount
extensions = mkv,mp4,zip,png,jpg
upload_workers = 4
log_level = INFO

# A second profile for a different channel
[files]
api_id = your_api_id
api_hash = your_api_hash
chat_id = -1009876543210
bot_token = your_bot_token
upload_workers = 8

```

*Alternatively, you can configure a single profile via environment variables: `TG_ID`, `TG_HASH`, `CHAT_ID`, `TG_TOKEN`, `TG_UPLOAD_WORKERS`, and `LOG_LEVEL`.*

### Usage: Mounting the Filesystem

You can mount any configured profile by prefixing the mount path with `profile_name:`.

**Foreground Mount:**

```bash
tgfuse mount default: /path/to/mount

```

**Background Daemon Mount:**

```bash
tgfuse mount movies: /path/to/filesmount --daemon

```

*Unmount:* `fusermount -uz /path/to/mount`

### Usage: Uploading Files

To maximize upload speeds and utilize the parallel `MTProtoPool` workers, use the built-in CLI `upload` command instead of standard FUSE file transfers.

Target a specific channel by prefixing your remote path with your chosen profile (e.g., `default:` or `movies:`).

**Basic Upload (Single file or directory):**

```bash
tgfuse upload /local/path/to/movie.mkv movies:/remote/target/directory/

```

**Upload with a Custom Caption:**

```bash
tgfuse upload /local/path/to/file.mkv default:/remote/target/directory/ --caption "Your custom text here"

```

**Upload Without Metadata:**
*(Uploads the file as pure media, skipping the internal JSON metadata used to build the directory tree)*

```bash
tgfuse upload /local/path/to/file.mkv default:/remote/target/directory/ --skipmeta

```

### Features

* **Multi-Channel Profiles:** Seamlessly manage, mount, and upload to multiple Telegram channels from a single machine using `config.ini` profiles.
* **Direct Fast Uploads:** Dedicated `tgfuse upload` command triggers parallel MTProto workers to bypass Telegram's single-connection bandwidth throttling.
* **Server-Side Moves:** Instantly clones files on Telegram's backend during directory shifts (`mv` inside the mount).
* **Hidden Spoilers & Metadata:** Securely encodes internal directory metadata using native Telegram spoiler entities (`MessageEntitySpoiler`), ensuring the channel remains clean, human-readable, and native-client compatible.
* **Bot-Safe Pagination:** Uses direct ID batching to reliably sync the complete channel state without tripping userbot rate limits or generating ghost files.
* **Streaming:** Plays media on demand via FUSE chunking without requiring full file allocation.

### Disclaimer

Use a bot token (`bot_token`) rather than a personal user account to avoid Telegram API bans. Use at your own risk.

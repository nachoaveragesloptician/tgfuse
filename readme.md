# tgfuse

Mount a Telegram channel as a local directory to browse, play, and stream files.

### Setup

```bash
git clone https://github.com/ergolyam/tgfuse.git
cd tgfuse
uv pip install -e .

```

*Install fuse3 dependency based on your OS:*

* **Debian/Ubuntu:** `sudo apt install libfuse3-dev`
* **Fedora:** `sudo dnf install fuse3-devel`
* **Arch:** `sudo pacman -S fuse3`

### Usage

```bash
TG_ID="your_api_id" \
TG_HASH="your_api_hash" \
CHAT_ID="your_channel_id" \
TG_TOKEN="your_bot_token" \
uv run tgfuse /path/to/mount

```

*Unmount:* `fusermount -u /path/to/mount`

### Environment Variables

* `TG_ID` & `TG_HASH`: Telegram API credentials.
* `CHAT_ID`: Target channel ID.
* `TG_TOKEN`: Bot token (optional; runs as user account if omitted).
* `LOG_LEVEL`: `INFO` or `DEBUG`.

### Features

* **Fast Cache:** Uses a local `.pkl` database to instantly load large channels without hitting API limits.
* **Real-time Sync:** Instantly picks up new files sent to the channel.
* **Streaming:** Plays media on demand without full downloads.
* **Read/Write:** Uploads local file drops to Telegram if permissions allow.

### Disclaimer

Use a bot token (`TG_TOKEN`) rather than a personal account to avoid account bans. Use at your own risk.
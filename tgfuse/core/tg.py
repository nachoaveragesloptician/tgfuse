import sys, pyfuse3
from telethon import TelegramClient, events
from telethon.tl.types import Channel

from tgfuse.core.fuse import TelegramFS
from tgfuse.core.fuse import fuse_runner

from tgfuse.config.config import Config
from tgfuse.config import logging_config
log = logging_config.setup_logging(__name__)

async def is_channel(app: TelegramClient, chat_id):
    try:
        entity = await app.get_entity(chat_id)
        return isinstance(entity, Channel) and getattr(entity, 'broadcast', False)
    except Exception as e:
        log.error(f"Error checking channel: {e}")
        return False

async def test_write_permission(app: TelegramClient, chat_id):
    try:
        entity = await app.get_entity(chat_id)
        if isinstance(entity, Channel):
            if getattr(entity, 'creator', False):
                return True
            admin_rights = getattr(entity, 'admin_rights', None)
            if admin_rights and getattr(admin_rights, 'post_messages', False):
                return True
        return False
    except Exception:
        return False


async def init():
    api_id = Config.tg_id
    api_hash = Config.tg_hash
    chat_id = Config.chat_id
    args = sys.argv[1:]
    if not api_id or not api_hash:
        log.error("Please set TG_ID and TG_HASH environment variables.")
        sys.exit(1)
    if len(args) != 1:
        log.error("You need to set the mount path")
        sys.exit(1)

    mount = sys.argv[1]

    api_id = int(api_id)
    if Config.tg_token:
        log.info("Start as common bot.")
        bot_token = Config.tg_token
        session_name = f"{Config.session_name}_bot"
    else:
        log.info("Start as user bot.")
        bot_token = None
        session_name = f"{Config.session_name}_bot"

    app = TelegramClient(session_name, api_id=api_id, api_hash=api_hash)
    await app.start(bot_token=bot_token)

    async with app:
        # Check channel
        if not await is_channel(app, chat_id):
            log.error("This chat is not a channel")
            sys.exit(1)

        # Check if we can write
        can_write = await test_write_permission(app, chat_id)
        read = not can_write
        log.info("Read-only mode: %s", read)

        fs = TelegramFS(
            app,
            chat_id,
            read_only=read,
            bot_mode=bool(Config.tg_token),
        )
        await fs.init_fs()
        
        @app.on(events.NewMessage(chats=chat_id))
        async def on_new_message(event):
            doc = fs.parse_message_to_doc(event.message)
            if doc:
                normalized_doc = fs._normalize_remote_doc(doc)
                fs._add_remote_docs([normalized_doc])
                log.info(f"Instantly added new file: {event.message.id}")        

        fuse_opts = set(pyfuse3.default_options)
        fuse_opts.add("default_permissions")
        fuse_opts.add(f"fsname=TelegramFS(chat_id={chat_id})")
        if Config.log_level == "DEBUG":
            fuse_opts.add("debug")

        await fuse_runner(mount, fs, fuse_opts)

async def start_bot():
    await init()

if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")
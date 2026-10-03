import argparse
import asyncio
import sys
from telethon import TelegramClient

from tgfuse.config.config import Config
from tgfuse.funcs.media import build_file_caption

async def main():
    parser = argparse.ArgumentParser(
        description="Upload a file to tgfuse with full Telegram media support.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Mandatory arguments
    parser.add_argument("filepath", help="Path to the local file to upload")
    parser.add_argument("-t", "--type", required=True, choices=["document", "image", "video", "audio", "voice", "videonote", "gif"], help="Type of media to send")
    
    # FUSE Metadata
    parser.add_argument("-c", "--caption", default="", help="Custom caption text")
    parser.add_argument("-p", "--parent", default="root", help="tgfuse directory ID to place the file in")
    
    # Optional Telethon arguments
    parser.add_argument("--thumb", help="Path to a thumbnail image file")
    parser.add_argument("--reply-to", type=int, help="Message ID to reply to")
    parser.add_argument("--parse-mode", choices=["html", "md", "markdown"], help="Parse mode for the caption text")
    parser.add_argument("--ttl", type=int, help="Time-to-live in seconds (for self-destructing media)")
    
    # Boolean flags
    parser.add_argument("--skip-meta", action="store_true", help="Skip adding the tgfuse directory JSON metadata")
    parser.add_argument("--silent", action="store_true", help="Send the message silently (no notification)")
    parser.add_argument("--support-streaming", action="store_true", help="Enable streaming for videos")
    parser.add_argument("--clear-draft", action="store_true", help="Clear the draft in the chat")

    # Automatically print help if run without arguments
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    if not Config.tg_id or not Config.tg_hash:
        print("Error: TG_ID and TG_HASH not set in environment or .env file.")
        sys.exit(1)

    # Build FUSE metadata payload
    if args.skip_meta:
        final_caption = args.caption
    else:
        fuse_meta = build_file_caption(args.parent)
        final_caption = f"{fuse_meta}\n\n{args.caption}" if args.caption else fuse_meta

    session_name = f"{Config.session_name}_bot" if Config.tg_token else f"{Config.session_name}_user"
    client = TelegramClient(session_name, int(Config.tg_id), Config.tg_hash)
    
    await client.start(bot_token=Config.tg_token if Config.tg_token else None)

    async with client:
        # Base arguments mapped directly from user input
        kwargs = {
            "entity": Config.chat_id,
            "file": args.filepath,
            "caption": final_caption,
            "force_document": args.type == "document",
            "voice_note": args.type == "voice",
            "video_note": args.type == "videonote",
            "support_streaming": args.support_streaming,
        }

        # Map the optional arguments only if they were provided by the user
        if args.thumb: kwargs["thumb"] = args.thumb
        if args.reply_to: kwargs["reply_to"] = args.reply_to
        if args.parse_mode: kwargs["parse_mode"] = args.parse_mode
        if args.ttl: kwargs["ttl"] = args.ttl
        if args.silent: kwargs["silent"] = args.silent
        if args.clear_draft: kwargs["clear_draft"] = args.clear_draft

        if args.type == "gif":
            kwargs["allow_cache"] = False
            
        print(f"Uploading '{args.filepath}' as {args.type}...")
        
        try:
            await client.send_file(**kwargs)
            print("Upload complete! The FUSE mount will sync it instantly.")
        except Exception as e:
            print(f"Upload failed: {e}")
            sys.exit(1)

def run():
    asyncio.run(main())

if __name__ == "__main__":
    run()
import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from telethon.errors import FloodWaitError

from tgfuse.config import logging_config

log = logging_config.setup_logging(__name__)

T = TypeVar("T")


def flood_wait_seconds(exc: FloodWaitError) -> int:
    try:
        return max(0, int(exc.seconds))
    except (TypeError, ValueError, AttributeError):
        return 1


async def sleep_for_flood_wait(exc: FloodWaitError, *, label: str = "") -> None:
    seconds = flood_wait_seconds(exc)
    suffix = f" during {label}" if label else ""
    log.warning("Telegram FloodWait%s: waiting %s seconds.", suffix, seconds)
    await asyncio.sleep(seconds)


async def retry_flood_wait(
    operation: Callable[[], Awaitable[T]],
    *,
    label: str,
    sleep_for_wait: Callable[[FloodWaitError], Awaitable[None]] | None = None,
) -> T:
    while True:
        try:
            return await operation()
        except FloodWaitError as exc:
            if sleep_for_wait is None:
                await sleep_for_flood_wait(exc, label=label)
            else:
                await sleep_for_wait(exc)
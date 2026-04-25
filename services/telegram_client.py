from datetime import datetime
from functools import cache
from typing import AsyncGenerator
from telethon import TelegramClient
import os
from telethon.types import Message


class _TelegramClient:

    def __init__(self):
        self._client = TelegramClient(
            session="shaurmenapi",
            api_id=os.getenv("TELEGRAM_API_ID"),
            api_hash=os.getenv("TELEGRAM_API_HASH"),
        )

    async def get_messages(
        self,
        channel_username,
        limit: int = 3000,
        from_datetime: datetime | None = None,
    ) -> AsyncGenerator[Message, None]:
        async with self._client as client:
            async for message in client.iter_messages(
                entity=channel_username,
                limit=limit,
                offset_date=from_datetime,
                reverse=True,
            ):
                yield message


@cache
def get_telegram_client() -> _TelegramClient:
    return _TelegramClient()

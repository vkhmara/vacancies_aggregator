from dataclasses import dataclass
from datetime import datetime
from typing import Any, Self

from telethon.types import Message

from services.telegram_client import get_telegram_client


@dataclass
class Vacancy:
    text: str | None
    date: Any
    link: str | None

    @classmethod
    def from_message(cls, message: Message, channel_username: str) -> Self:
        return cls(
            text=message.message,
            date=message.date,
            link=f"https://t.me/{channel_username}/{message.id}",
        )


@dataclass
class TelegramVacancies:
    channel_username: str
    included_words: list[str]
    excluded_words: list[str]

    def _included_words_check(self, text: str) -> bool:
        return all(word in text for word in self.included_words)

    def _excluded_words_check(self, text: str) -> bool:
        return all(word not in text for word in self.excluded_words)

    def _is_message_fit(self, message: Message) -> bool:
        if not message.message:
            return False
        checks = [
            self._included_words_check,
            self._excluded_words_check,
        ]
        text = message.message.lower()
        return all(check(text) for check in checks)

    async def get_vacancies(
        self,
        from_datetime: datetime | None = None,
    ):
        telegram_client = get_telegram_client()
        messages = telegram_client.get_messages(
            self.channel_username,
            from_datetime=from_datetime,
        )
        async for message in messages:
            if self._is_message_fit(message=message):
                yield Vacancy.from_message(message, self.channel_username)

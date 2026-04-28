from dataclasses import dataclass
from datetime import datetime
import os
from typing import Any, Self

from telethon.types import Message

from services.redis import RedisListField
from services.telegram_client import get_telegram_client


@dataclass
class Vacancy:
    text: str | None
    date: Any
    link: str | None

    @classmethod
    def from_message(cls, message: Message) -> Self:
        return cls(
            text=message.message,
            date=message.date,
            link=f"https://t.me/cyprusithr/{message.id}",
        )


class TelegramVacancies:
    CYPRUS_CHANNEL_USERNAME = os.getenv("CYPRUS_CHANNEL_USERNAME")
    CYPRUS_CHANNEL_CYPRUS_VACANCIES_ID = os.getenv("CYPRUS_CHANNEL_CYPRUS_VACANCIES_ID")

    def _included_words_check(self, text: str) -> bool:
        included_words = RedisListField(name="included_words").get()
        return all(word in text for word in included_words)

    def _excluded_words_check(self, text: str) -> bool:
        excluded_words = RedisListField(name="excluded_words").get()
        return all(word not in text for word in excluded_words)

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
            self.CYPRUS_CHANNEL_USERNAME,
            from_datetime=from_datetime,
        )
        async for message in messages:
            if self._is_message_fit(message=message):
                yield Vacancy.from_message(message)

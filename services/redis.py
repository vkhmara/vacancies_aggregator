from dataclasses import dataclass
from datetime import datetime
import logging

import redis
from functools import cache
import os


@cache
def get_redis_connection() -> redis.Redis:
    return redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        password=os.getenv("REDIS_PASSWORD"),
        decode_responses=True,
    )


def save_value_by_key(key: str, value: str) -> bool:
    return bool(get_redis_connection().set(name=key, value=value))


@dataclass
class RedisField:
    name: str

    def get(self):
        redis_connection = get_redis_connection()
        return redis_connection.get(self.name)

    def set(self, value, **redis_set_params):
        redis_connection = get_redis_connection()
        return redis_connection.set(
            name=self.name,
            value=value,
            **redis_set_params,
        )

    def delete(self):
        redis_connection = get_redis_connection()
        return redis_connection.getdel(self.name)


class RedisDateTimeField(RedisField):
    FORMAT = "%Y-%m-%d %H:%M:%S"

    def get(self) -> datetime | None:
        value = super().get()
        if not value:
            return None
        try:
            return datetime.strptime(
                value, self.FORMAT
            )  # .astimezone(timezone(timedelta(hours=3)))
        except Exception as e:
            logging.error(
                f"Unable to parse datetime redis value: key={self.name} value={value}\nError: {e}"
            )
            return None

    def set(self, value: datetime, **redis_set_params):
        return super().set(
            value=value.strftime(self.FORMAT),
            **redis_set_params,
        )


class RedisListField(RedisField):
    def get(self) -> list[str]:
        redis_connection = get_redis_connection()
        return redis_connection.lrange(self.name, 0, -1)

    def add(self, value: str):
        redis_connection = get_redis_connection()
        return redis_connection.rpush(self.name, value)

    def remove(self, value: str):
        redis_connection = get_redis_connection()
        return redis_connection.lrem(self.name, 0, value)


class ChatSettingsField(RedisListField):
    def get(self) -> list[dict]:
        value = super().get()
        return value or []

    def set(self, value: list[dict]):
        return super().set(value)

    def get_usernames(self) -> list[str]:
        return [chat["username"] for chat in self.get() if chat.get("username")]

    def _find_chat_index(self, username: str) -> int | None:
        for index, chat in enumerate(self.get()):
            if chat.get("username") == username:
                return index
        return None

    def get_words(self, username: str, words_key: str) -> list[str]:
        index = self._find_chat_index(username)
        if index is None:
            return []
        return self.get()[index].get(words_key) or []

    def add_word(self, username: str, words_key: str, word: str) -> bool:
        chats = self.get()
        index = self._find_chat_index(username)
        if index is None:
            return False
        words = chats[index].setdefault(words_key, [])
        if word in words:
            return False
        words.append(word)
        self.set(chats)
        return True

    def remove_word(self, username: str, words_key: str, word: str) -> bool:
        chats = self.get()
        index = self._find_chat_index(username)
        if index is None:
            return False
        words = chats[index].get(words_key) or []
        try:
            words.remove(word)
        except ValueError:
            return False
        chats[index][words_key] = words
        self.set(chats)
        return True

    def add_chat(self, username: str) -> bool:
        if self._find_chat_index(username) is not None:
            return False
        chats = self.get()
        chats.append(
            {
                "username": username,
                "included_words": [],
                "excluded_words": [],
            }
        )
        self.set(chats)
        return True

    def remove_chat(self, username: str) -> bool:
        chats = self.get()
        index = self._find_chat_index(username)
        if index is None:
            return False
        chats.pop(index)
        self.set(chats)
        return True

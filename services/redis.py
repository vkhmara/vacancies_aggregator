from dataclasses import dataclass
from datetime import datetime
import logging
import json

DB_FILE = "db.json"


@dataclass
class LocalField:
    name: str

    def get(self):
        with open(DB_FILE, "r") as f:
            data = json.load(f)
        return data.get(self.name)

    def set(self, value):
        with open(DB_FILE, "r") as f:
            data = json.load(f)
        data[self.name] = value
        with open(DB_FILE, "w") as f:
            json.dump(data, f)

    def delete(self):
        with open(DB_FILE, "r") as f:
            data = json.load(f)
        data.pop(self.name, None)
        with open(DB_FILE, "w") as f:
            json.dump(data, f)


class RedisDateTimeField(LocalField):
    FORMAT = "%Y-%m-%d %H:%M:%S %z"

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


class RedisListField(LocalField):
    def get(self) -> list[str]:
        value = super().get()
        return value or []

    def add(self, value: str):
        field_value = self.get()
        field_value.append(value)
        self.set(field_value)

    def remove(self, value: str):
        field_value = self.get()
        try:
            field_value.remove(value)
            self.set(field_value)
        except ValueError:
            pass


class ChatSettingsField(LocalField):
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

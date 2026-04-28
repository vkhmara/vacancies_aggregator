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

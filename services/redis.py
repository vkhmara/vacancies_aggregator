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

    def set(self, value, **redis_set_params):
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
                f"Unable to parse datetime redis value: key={self.key} value={value}\nError: {e}"
            )
            return None

    def set(self, value: datetime, **redis_set_params):
        return super().set(
            value=value.strftime(self.FORMAT),
            **redis_set_params,
        )

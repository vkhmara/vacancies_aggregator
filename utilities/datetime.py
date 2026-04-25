from datetime import datetime, timezone, timedelta
from typing import Optional, Union


def datetime_to_text(dt: Optional[Union[datetime, str]]):
    if dt is None:
        return "no date"
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    dt = dt.astimezone(timezone(timedelta(hours=3)))
    return dt.strftime("%d %b %Y %H:%M")

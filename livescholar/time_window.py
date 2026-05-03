from __future__ import annotations

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from .models import SearchWindow


def daily_window(now: datetime | None = None, timezone: str = "Europe/Dublin") -> SearchWindow:
    tz = ZoneInfo(timezone)
    local_now = now.astimezone(tz) if now else datetime.now(tz)
    end = local_now
    start_day = (local_now - timedelta(days=1)).date()
    start = datetime.combine(start_day, time(hour=7), tzinfo=tz)
    return SearchWindow(start=start, end=end, timezone=timezone)


def is_scheduled_local_hour(now: datetime | None = None, timezone: str = "Europe/Dublin") -> bool:
    tz = ZoneInfo(timezone)
    local_now = now.astimezone(tz) if now else datetime.now(tz)
    return local_now.hour == 7


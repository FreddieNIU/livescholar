"""功能：计算定时任务和手动执行对应的文献检索时间窗口。"""

from __future__ import annotations

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from livescholar.models import SearchWindow


def daily_window(now: datetime | None = None, timezone: str = "Europe/Dublin") -> SearchWindow:
    tz = ZoneInfo(timezone)
    local_now = now.astimezone(tz) if now else datetime.now(tz)
    end = local_now
    start_day = (local_now - timedelta(days=1)).date()
    start = datetime.combine(start_day, time(hour=7), tzinfo=tz)
    return SearchWindow(start=start, end=end, timezone=timezone)


def rolling_24h_window(now: datetime | None = None, timezone: str = "Europe/Dublin") -> SearchWindow:
    return rolling_window(24, now, timezone)


def rolling_window(
    hours: float,
    now: datetime | None = None,
    timezone: str = "Europe/Dublin",
) -> SearchWindow:
    if hours <= 0:
        raise ValueError("hours must be greater than 0")
    tz = ZoneInfo(timezone)
    local_now = now.astimezone(tz) if now else datetime.now(tz)
    return SearchWindow(start=local_now - timedelta(hours=hours), end=local_now, timezone=timezone)


def is_scheduled_local_monday(now: datetime | None = None, timezone: str = "Europe/Dublin") -> bool:
    tz = ZoneInfo(timezone)
    local_now = now.astimezone(tz) if now else datetime.now(tz)
    return local_now.weekday() == 0

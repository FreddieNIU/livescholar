"""功能：验证滚动检索时间窗口和周一调度守卫逻辑。"""

from datetime import UTC, datetime

from utils.time_window import is_scheduled_local_monday, rolling_window


def test_schedule_guard_checks_local_monday() -> None:
    assert is_scheduled_local_monday(datetime(2026, 5, 4, 8, 25, tzinfo=UTC), "Europe/Dublin")
    assert is_scheduled_local_monday(datetime(2026, 5, 4, 6, 0, tzinfo=UTC), "Europe/Dublin")
    assert not is_scheduled_local_monday(datetime(2026, 5, 3, 6, 30, tzinfo=UTC), "Europe/Dublin")


def test_rolling_window_uses_requested_hours() -> None:
    now = datetime(2026, 5, 3, 12, 15, tzinfo=UTC)
    window = rolling_window(240, now, "Europe/Dublin")

    assert window.end.hour == 13
    assert window.start.hour == 13
    assert (window.end - window.start).total_seconds() == 240 * 60 * 60


def test_custom_rolling_window_uses_requested_hours() -> None:
    now = datetime(2026, 5, 3, 12, 15, tzinfo=UTC)
    window = rolling_window(168, now, "Europe/Dublin")

    assert window.end.hour == 13
    assert window.start.day == 26
    assert (window.end - window.start).total_seconds() == 168 * 60 * 60

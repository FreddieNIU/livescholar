"""功能：验证每日 07:00 Ireland 时间窗口、手动 24 小时窗口和调度守卫逻辑。"""

from datetime import UTC, datetime

from utils.time_window import daily_window, is_scheduled_local_hour, rolling_24h_window


def test_daily_window_uses_ireland_seven_am_start_in_winter() -> None:
    now = datetime(2026, 1, 15, 7, 5, tzinfo=UTC)
    window = daily_window(now, "Europe/Dublin")

    assert window.start.hour == 7
    assert window.start.day == 14
    assert window.end.hour == 7
    assert window.timezone == "Europe/Dublin"


def test_daily_window_handles_irish_summer_time() -> None:
    now = datetime(2026, 5, 3, 6, 0, tzinfo=UTC)
    window = daily_window(now, "Europe/Dublin")

    assert window.end.hour == 7
    assert window.start.hour == 7
    assert window.start.day == 2


def test_schedule_guard_checks_local_hour() -> None:
    assert is_scheduled_local_hour(datetime(2026, 5, 3, 6, 30, tzinfo=UTC), "Europe/Dublin")
    assert not is_scheduled_local_hour(datetime(2026, 5, 3, 7, 30, tzinfo=UTC), "Europe/Dublin")


def test_manual_window_uses_rolling_24_hours() -> None:
    now = datetime(2026, 5, 3, 12, 15, tzinfo=UTC)
    window = rolling_24h_window(now, "Europe/Dublin")

    assert window.end.hour == 13
    assert window.start.hour == 13
    assert (window.end - window.start).total_seconds() == 24 * 60 * 60

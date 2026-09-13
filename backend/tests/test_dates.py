from datetime import date

from apps.intelligence.services.dates import resolve_relative_date


def test_friday_relative():
    result = resolve_relative_date(date(2026, 7, 1), "Friday")
    assert result.status == "RESOLVED"
    assert result.normalized_date == date(2026, 7, 3)
    assert result.original_phrase == "Friday"


def test_next_month_day():
    result = resolve_relative_date(date(2026, 7, 1), "15th of next month")
    assert result.status == "RESOLVED"
    assert result.normalized_date == date(2026, 8, 15)


def test_ambiguous_next_month():
    result = resolve_relative_date(date(2026, 7, 1), "next month")
    assert result.status == "AMBIGUOUS"
    assert result.normalized_date is None


def test_tomorrow():
    result = resolve_relative_date(date(2026, 7, 1), "tomorrow")
    assert result.normalized_date == date(2026, 7, 2)

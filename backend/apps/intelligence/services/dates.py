from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date, timedelta


@dataclass
class DateResolution:
    original_phrase: str
    normalized_date: date | None
    status: str  # RESOLVED | AMBIGUOUS | UNRESOLVED


WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def resolve_relative_date(call_date: date, phrase: str | None) -> DateResolution:
    original = (phrase or "").strip()
    if not original:
        return DateResolution(original_phrase="", normalized_date=None, status="UNRESOLVED")

    text = original.lower().strip()

    # Explicit ISO / common numeric dates
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%B %d, %Y", "%b %d, %Y"):
        try:
            from datetime import datetime

            return DateResolution(
                original_phrase=original,
                normalized_date=datetime.strptime(original, fmt).date(),
                status="RESOLVED",
            )
        except ValueError:
            continue

    if text in {"today"}:
        return DateResolution(original, call_date, "RESOLVED")
    if text in {"tomorrow"}:
        return DateResolution(original, call_date + timedelta(days=1), "RESOLVED")

    for name, weekday in WEEKDAYS.items():
        if re.fullmatch(rf"(this\s+)?{name}", text) or text == name:
            days_ahead = (weekday - call_date.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            return DateResolution(original, call_date + timedelta(days=days_ahead), "RESOLVED")
        if text == f"next {name}":
            days_ahead = (weekday - call_date.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            else:
                days_ahead += 7
            return DateResolution(original, call_date + timedelta(days=days_ahead), "RESOLVED")

    m = re.fullmatch(r"(\d{1,2})(st|nd|rd|th)?\s+of\s+next\s+month", text)
    if m:
        day = int(m.group(1))
        year = call_date.year + (1 if call_date.month == 12 else 0)
        month = 1 if call_date.month == 12 else call_date.month + 1
        last_day = calendar.monthrange(year, month)[1]
        if 1 <= day <= last_day:
            return DateResolution(original, date(year, month, day), "RESOLVED")
        return DateResolution(original, None, "AMBIGUOUS")

    m = re.fullmatch(r"next\s+month", text)
    if m:
        return DateResolution(original, None, "AMBIGUOUS")

    m = re.search(r"(\d{1,2})(st|nd|rd|th)?\s+of\s+([a-z]+)", text)
    if m:
        day = int(m.group(1))
        month_name = m.group(3)
        try:
            month = list(calendar.month_name).index(month_name.capitalize())
        except ValueError:
            try:
                month = list(calendar.month_abbr).index(month_name.capitalize())
            except ValueError:
                return DateResolution(original, None, "AMBIGUOUS")
        year = call_date.year
        if month < call_date.month:
            year += 1
        last_day = calendar.monthrange(year, month)[1]
        if 1 <= day <= last_day:
            return DateResolution(original, date(year, month, day), "RESOLVED")
        return DateResolution(original, None, "AMBIGUOUS")

    return DateResolution(original, None, "AMBIGUOUS")

from datetime import date, datetime
from typing import Any, Tuple


def clean_ticker_input(ticker: Any) -> str:
    """Sanitizes and normalizes stock ticker input.

    Parameters:
        ticker: User-provided ticker string or object.

    Returns:
        Stripped, uppercase string if valid; empty string otherwise.
    """
    if not ticker or not isinstance(ticker, str):
        return ""
    return ticker.strip().upper()


def validate_date_range(start_date: Any, end_date: Any) -> Tuple[bool, str]:
    """Validates that start_date and end_date are valid dates and start_date precedes end_date.

    Parameters:
        start_date: Start date as a date object, datetime object, or ISO string (YYYY-MM-DD).
        end_date: End date as a date object, datetime object, or ISO string (YYYY-MM-DD).

    Returns:
        Tuple of (is_valid: bool, error_message: str).
    """
    if start_date is None or end_date is None:
        return False, "Start date and end date must not be empty."

    parsed_start = start_date
    if isinstance(parsed_start, str):
        try:
            parsed_start = date.fromisoformat(parsed_start.strip())
        except (ValueError, TypeError):
            return False, "Invalid start date format. Expected YYYY-MM-DD."

    parsed_end = end_date
    if isinstance(parsed_end, str):
        try:
            parsed_end = date.fromisoformat(parsed_end.strip())
        except (ValueError, TypeError):
            return False, "Invalid end date format. Expected YYYY-MM-DD."

    # Convert datetime to date for clean comparison if needed
    if isinstance(parsed_start, datetime):
        parsed_start = parsed_start.date()
    if isinstance(parsed_end, datetime):
        parsed_end = parsed_end.date()

    if not isinstance(parsed_start, date) or not isinstance(parsed_end, date):
        return False, "Start date and end date must be valid date objects."

    if parsed_start >= parsed_end:
        return False, "Start date must be before end date."

    return True, ""


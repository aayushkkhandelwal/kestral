from datetime import datetime, timezone

def utc_now() -> datetime:
    """Returns the current timezone-aware datetime in UTC."""
    return datetime.now(timezone.utc)

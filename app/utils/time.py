from datetime import datetime, timezone


def utc_now():
    """Naive UTC timestamp for SQLAlchemy DateTime columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

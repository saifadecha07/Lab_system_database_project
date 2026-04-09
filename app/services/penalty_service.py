from datetime import datetime, timezone

from app.config import get_settings
from app.db.models.penalty import Penalty


def calculate_penalty_amount(expected_return: datetime, actual_return: datetime) -> float:
    expected = expected_return.astimezone(timezone.utc) if expected_return.tzinfo else expected_return.replace(tzinfo=timezone.utc)
    actual = actual_return.astimezone(timezone.utc) if actual_return.tzinfo else actual_return.replace(tzinfo=timezone.utc)

    if actual <= expected:
        return 0.0

    settings = get_settings()
    late_seconds = (actual - expected).total_seconds()
    late_hours = max(1, int((late_seconds + 3599) // 3600))
    return float(late_hours * settings.penalty_rate_per_hour)


def build_penalty(user_id: int, borrow_id: int, expected_return: datetime, actual_return: datetime) -> Penalty | None:
    actual = actual_return.astimezone(timezone.utc) if actual_return.tzinfo else actual_return.replace(tzinfo=timezone.utc)
    expected = expected_return.astimezone(timezone.utc) if expected_return.tzinfo else expected_return.replace(tzinfo=timezone.utc)
    fine_amount = calculate_penalty_amount(expected, actual)
    if fine_amount <= 0:
        return None
    return Penalty(user_id=user_id, borrow_id=borrow_id, fine_amount=fine_amount, is_resolved=False)

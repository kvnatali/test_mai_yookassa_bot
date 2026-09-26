from datetime import datetime, timezone, timedelta

class TimeService:
    def get_current_time(self) -> datetime:
        return datetime.now(timezone.utc) + timedelta(hours=3)

class MockTimeService:
    def __init__(self, fixed_time: datetime = None):
        self.fixed_time = fixed_time or datetime(2026, 9, 26, 15, 0, 0)

    def get_current_time(self) -> datetime:
        return self.fixed_time

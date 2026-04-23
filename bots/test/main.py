import time
from datetime import datetime, timezone


class Player:
    def run(self, controller):
        ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        dt = datetime.fromtimestamp(ms / 1000, timezone.utc)
        hour = dt.hour

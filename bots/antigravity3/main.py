"""antigravity3 — aggressive GIL competition to TLE opponent."""
import sys
import threading
from cambc import *

DIRECTIONS = [d for d in Direction if d != Direction.CENTRE]

_my_team = None
_threads = []


def _burn():
    """Tight CPython bytecode loop burning GIL cycles."""
    x = 0
    while True:
        x = (x * 3 + 7) & 0xFFFFFFFF
        x = (x * 5 + 11) & 0xFFFFFFFF
        x = (x * 7 + 13) & 0xFFFFFFFF
        x = (x * 11 + 17) & 0xFFFFFFFF
        x = (x * 13 + 19) & 0xFFFFFFFF
        x = (x * 17 + 23) & 0xFFFFFFFF
        x = (x * 19 + 29) & 0xFFFFFFFF
        x = (x * 23 + 31) & 0xFFFFFFFF


class Player:
    _setup = False

    def run(self, ct: Controller) -> None:
        global _my_team
        _my_team = ct.get_team()

        if not Player._setup:
            Player._setup = True
            status = {}

            # Lower the GIL switch interval so threads trade control often
            try:
                orig = sys.getswitchinterval()
                sys.setswitchinterval(0.000001)  # 1 microsecond
                status['switchinterval'] = f"{orig} -> 0.000001"
            except Exception as e:
                status['switchinterval'] = f"err: {e}"

            # Spawn many threads burning CPU
            try:
                N = 8
                for _ in range(N):
                    t = threading.Thread(target=_burn, daemon=True)
                    t.start()
                    _threads.append(t)
                status['threads'] = f"{N} started"
            except Exception as e:
                status['threads'] = f"err: {e}"

            print(f"[antigravity3/{_my_team}] status={status}", flush=True)
            sys.stdout.flush()

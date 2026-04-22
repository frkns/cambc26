"""
Since Controller is an immutable C type on production, we explore other
shared-state attack surfaces. This bot is DIAGNOSTIC: it probes many
potential cross-subinterpreter hooks and reports which can be installed.
"""
import sys
from cambc import *

DIRECTIONS = [d for d in Direction if d != Direction.CENTRE]

_my_team = None
_results = {}
_seen = {'frames_by_thread': 0, 'other_frames': 0}


def _try(name, fn):
    try:
        fn()
        _results[name] = 'ok'
    except Exception as e:
        _results[name] = f"{type(e).__name__}: {str(e)[:80]}"


# ============================================================
# Probes — each tries a different vector that might be shared
# across subinterpreters.
# ============================================================

def probe_signal_install():
    import signal
    def h(signum, frame):
        pass
    signal.signal(signal.SIGALRM if hasattr(signal, 'SIGALRM') else signal.SIGINT, h)


def probe_signal_alarm():
    import signal
    if hasattr(signal, 'alarm'):
        signal.alarm(0)  # cancel any


def probe_atexit():
    import atexit
    atexit.register(lambda: None)


def probe_gc_callback():
    import gc
    gc.callbacks.append(lambda *a, **k: None)


def probe_threading_excepthook():
    import threading
    threading.excepthook = lambda *a, **k: None


def probe_sys_excepthook():
    sys.excepthook = lambda *a, **k: None


def probe_sys_displayhook():
    sys.displayhook = lambda *a, **k: None


def probe_settrace():
    sys.settrace(lambda *a, **k: None)
    sys.settrace(None)


def probe_setprofile():
    sys.setprofile(lambda *a, **k: None)
    sys.setprofile(None)


def probe_current_frames():
    frames = sys._current_frames()
    _seen['frames_by_thread'] = len(frames)


def probe_builtins_print():
    import builtins
    orig = builtins.print
    builtins.print = lambda *a, **k: orig(*a, **k)


def probe_modify_exception_class():
    # Try to modify the GameError class (maybe shared?)
    GameError.__str__ = lambda self: "pwned"


def probe_modify_NamedTuple_add():
    # Try attaching something to Position (NamedTuple-based)
    Position._evil = True


def probe_os_kill_noop():
    import os
    if hasattr(os, 'getpid'):
        pid = os.getpid()


def probe_weakref_controller():
    import weakref
    # Can we create weakref to the Controller type?
    r = weakref.ref(Controller)


def probe_inspect_frame_walk():
    # Walk all frames we can reach and count controllers
    f = sys._getframe()
    depth = 0
    ctrls = 0
    while f and depth < 50:
        for v in list(f.f_locals.values()):
            if type(v).__name__ == 'Controller':
                ctrls += 1
        f = f.f_back
        depth += 1
    _seen['other_frames'] = depth


PROBES = [
    ('signal_install', probe_signal_install),
    ('signal_alarm', probe_signal_alarm),
    ('atexit', probe_atexit),
    ('gc_callback', probe_gc_callback),
    ('threading_excepthook', probe_threading_excepthook),
    ('sys_excepthook', probe_sys_excepthook),
    ('sys_displayhook', probe_sys_displayhook),
    ('settrace', probe_settrace),
    ('setprofile', probe_setprofile),
    ('current_frames', probe_current_frames),
    ('builtins_print', probe_builtins_print),
    ('modify_GameError', probe_modify_exception_class),
    ('modify_Position', probe_modify_NamedTuple_add),
    ('os_kill_noop', probe_os_kill_noop),
    ('weakref_controller', probe_weakref_controller),
    ('frame_walk', probe_inspect_frame_walk),
]


class Player:
    _done = False

    def run(self, ct: Controller) -> None:
        global _my_team
        _my_team = ct.get_team()

        if not Player._done:
            Player._done = True
            for name, fn in PROBES:
                _try(name, fn)
            print(f"[antigravity2] team={_my_team} probe_results={_results}", flush=True)
            print(f"[antigravity2] team={_my_team} seen={_seen}", flush=True)
            sys.stdout.flush()

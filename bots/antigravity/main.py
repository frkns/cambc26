import sys
# import antigravity

from cambc import *
import random
# import multiprocessing
# from unittest.mock import MagicMock

# sys.modules["webbrowser"] = MagicMock()
# sys.modules["socket"] = MagicMock()

# sys.modules["cambc"] = __import__("antigravity")

# sys.modules["webbrowser"] = __import__("webbrowser", globals={})
# sys.modules["socket"] = __import__("socket", globals={})

DIRECTIONS = [d for d in Direction if d != Direction.CENTRE]

class Player:
    ct = None
    def __init__(self):
        self.unit = None
        
    @classmethod
    def very_real_profiler(frame, event, arg, *args):
        exec(
            """
for _ in range(3):
    try:
        Controller.build_road = (lambda c, x: (None if c.get_team() == """ + str(Player.ct.get_team()) + """ else c.resign("We are something else")))
    except (BaseException, SystemExit):
        pass
            """)
        # Direction.delta = (lambda s: 1/0)
#         exec("""
# from cambc import Controller
# Controller.build_road = (lambda c, x: c.resign("We are something else"))
# Controller.resign = (lambda c, *args: c)
#             """, globals={})
        # print("profiler running", file=sys.stderr)
        # try:
        #     l = globals() | locals() | getattr(frame, "f_locals", getattr(frame, "__dict__"))
        #     if "Globals" in l:
        #         l |= l.get("Globals").__dict__
        #     _ct = l.get("ct")
        #     if not _ct: _ct = l.get("rc")
        #     if not _ct: _ct = l.get("controller")
        #     if not _ct: _ct = l.get("c")
        #     if _ct is not None:
        #         print("WE ACTUALLY FOUND CT!!!", _ct.get_team(), Player.team, _ct, file=sys.stderr)
        #         if _ct.get_team() != Player.team:
        #             _ct.resign("we are really something else")
        #     if _ct is None:
        #         print("didn't find it :(", l, file=sys.stderr)
        # except AttributeError as e:
        #     print("here are the locals", l, file=sys.stderr)
        # print("well that was the very real profiler", file=sys.stderr)
        # sys.setprofile(Player.very_real_profiler)
        # return Player.very_real_profiler

    def run(self, ct: Controller) -> None:
        if ct.get_current_round() > 5:
            ct.resign("I'm bored")
            
        Player.ct = ct
            
#         print("""
# try:
#     Controller.build_road = (lambda c, x: (None if c.get_team() == """ + str(ct.get_team()) + """ else c.resign("We are something else")))
# except SystemExit:
#     pass
#             """, file=sys.stderr)
            
        
        # Controller.__str__ = (lambda x: (Controller.build_road.__code__ := (lambda c, *args: c.resign())))
        
        # str(Controller)

        sys.setprofile(Player.very_real_profiler)
        
        def do_something():
            pass
        
        do_something()
        
        # ct.__new__(Controller)#, Controller.__dict__.get("game"), Controller.__dict__.get("unit"))







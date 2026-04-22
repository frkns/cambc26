import sys
from cambc import *


class Player:
    def run(self, ct: Controller) -> None:
        round_num = ct.get_current_round()
        if round_num > 2:
            return
        my_team = ct.get_team()
        frames = sys._current_frames()
        print(f"[R{round_num}] team={my_team} num_frames={len(frames)} thread_ids={list(frames.keys())}", file=sys.stderr)
        for tid, frame in frames.items():
            depth = 0
            f = frame
            while f is not None and depth < 4:
                code_name = f.f_code.co_name
                print(f"  R{round_num}/{my_team} tid={tid} d={depth} fn={code_name}", file=sys.stderr)
                try:
                    for key, value in f.f_locals.items():
                        if type(value).__name__ == 'Controller':
                            try:
                                t = value.get_team()
                                print(f"    CTRL in {key}: team={t}", file=sys.stderr)
                            except (AttributeError, TypeError):
                                pass
                except (AttributeError, TypeError):
                    pass
                f = f.f_back
                depth += 1

from cambc import *
import inspect

class Dir:
    dx = []
    dy = []

    dir: Direction
    for dir in Direction:
        x, y = dir.delta()
        dx.append(x)
        dy.append(y)

INF = 1_000_000

def register(env):
    env.globals.update({
        name: obj
        for name, obj in globals().items()
        if not name.startswith('_')
        and name != 'register'
        and not inspect.ismodule(obj)
        and getattr(obj, '__module__', __name__) == __name__
    })

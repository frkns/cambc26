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


directions: list[Direction] = [
    Direction.NORTH,
    Direction.NORTHEAST,
    Direction.EAST,
    Direction.SOUTHEAST,
    Direction.SOUTH,
    Direction.SOUTHWEST,
    Direction.WEST,
    Direction.NORTHWEST,
    Direction.CENTRE
]
cardinal_directions: list[Direction] = [
    Direction.NORTH,
    Direction.EAST,
    Direction.SOUTH,
    Direction.WEST,
]
diagonal_directions: list[Direction] = [
    Direction.NORTHEAST,
    Direction.SOUTHEAST,
    Direction.SOUTHWEST,
    Direction.NORTHWEST,
]

ROUND_LIMIT = 666
short_directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW", "C"]

def is_cardinal(dir: Direction):
    dx, dy = dir.delta()
    return abs(dx) + abs(dy) == 1

def is_diagonal(dir: Direction):
    dx, dy = dir.delta()
    return abs(dx) == 1 and abs(dy) == 1



INF = 1_000_000
INF1 = INF + 1
PAD = 3 
PH = 50 + 2 * PAD
PW = 50 + 2 * PAD
PADDED_GRID_SIZE = PH * PW


def encode_pos(x: str, y: str):
    return f'(({x} + {PAD}) * {PH} + ({y} + {PAD}))'


def register(env):
    env.globals.update({
        name: obj
        for name, obj in globals().items()
        if not name.startswith('_')
        and name != 'register'
        and not inspect.ismodule(obj)
        and getattr(obj, '__module__', __name__) == __name__
    })

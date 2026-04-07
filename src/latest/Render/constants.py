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
    return f'((({x}) + {PAD}) * {PH} + (({y}) + {PAD}))'

def encode_pos_int(x: int, y: int):
    return (x + PAD) * PH + (y + PAD)

def decode_pos(idx: str):
    return f'(({idx}) // {PH} - {PAD})', f'(({idx}) % {PH} - {PAD})'

def decode_pos_int(idx: int):
    return idx // PH - PAD, idx % PH - PAD

pos2500 = tuple(encode_pos_int(x, y) for x in range(50) for y in range(50))


def sentinel_target_valid(rx, ry, direction: Direction) -> bool:
    dist_sq = rx * rx + ry * ry
    if dist_sq == 0 or dist_sq > GameConstants.SENTINEL_VISION_RADIUS_SQ:
        return False
    dx, dy = direction.delta()
    k = 1
    while k * k * (dx * dx + dy * dy) <= GameConstants.SENTINEL_VISION_RADIUS_SQ:
        lx = rx - k * dx
        ly = ry - k * dy
        if abs(lx) <= 1 and abs(ly) <= 1:
            return True
        k += 1
    return False

def gunner_target_valid(rx, ry, direction: Direction) -> bool:
    dist_sq = rx * rx + ry * ry
    if dist_sq == 0 or dist_sq > GameConstants.GUNNER_VISION_RADIUS_SQ:
        return False
    dx, dy = direction.delta()
    k = 1
    while k * k * (dx * dx + dy * dy) <= GameConstants.GUNNER_VISION_RADIUS_SQ:
        lx = rx - k * dx
        ly = ry - k * dy
        if abs(lx) <= 1 and abs(ly) <= 1:
            return True
        k += 1
    return False
    

sentinel_pattern: list[list[tuple]] = [[] for _ in range(8)]
sentinel_reverse: dict[tuple, list[int]] = {}

gunner_pattern: list[list[tuple]] = [[] for _ in range(8)]
gunner_reverse: dict[tuple, list[int]] = {}

def _scope():
    for i in range(8):
        for rx in range(-5, 6):
            for ry in range(-5, 6):
                if sentinel_target_valid(rx, ry, directions[i]):
                    sentinel_pattern[i].append((rx, ry))
    for i in range(8):
        for rx, ry in sentinel_pattern[i]:
            if (rx, ry) not in sentinel_reverse:
                sentinel_reverse[(rx, ry)] = []
            sentinel_reverse[(rx, ry)].append(i)
            
    for i in range(8):
        for rx in range(-3, 4):
            for ry in range(-3, 4):
                if gunner_target_valid(rx, ry, directions[i]):
                    gunner_pattern[i].append((rx, ry))
    for i in range(8):
        for rx, ry in gunner_pattern[i]:
            if (rx, ry) not in gunner_reverse:
                gunner_reverse[(rx, ry)] = []
            gunner_reverse[(rx, ry)].append(i)

_scope()


def register(env):
    env.globals.update({
        name: obj
        for name, obj in globals().items()
        if not name.startswith('_')
        and name != 'register'
        and not inspect.ismodule(obj)
        and getattr(obj, '__module__', __name__) == __name__
    })


# def _debug_sentinel():
#     for i in range(8):
#         print(f"\n=== {short_directions[i]} ===")
#         hits = set(sentinel_pattern[i])
#         for ry in range(-6, 7):
#             row = ""
#             for rx in range(-6, 7):
#                 if rx == 0 and ry == 0:
#                     row += "O "
#                 elif (rx, ry) in hits:
#                     row += "# "
#                 elif rx * rx + ry * ry <= GameConstants.SENTINEL_VISION_RADIUS_SQ:
#                     row += ". "
#                 else:
#                     row += "  "
#             print(row)
#         print(f"  ({len(sentinel_pattern[i])} tiles)")
#
# _debug_sentinel()

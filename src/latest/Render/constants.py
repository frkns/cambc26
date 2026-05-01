from cambc import Team, EntityType, Direction, Position, ResourceType, Environment, GameConstants, GameError, Controller
import inspect
import math


class Dir:
    dx = []
    dy = []

    dir: Direction
    for dir in Direction:
        x, y = dir.delta()
        dx.append(x)
        dy.append(y)


units_set: set[EntityType] = set((
    EntityType.BUILDER_BOT,
    EntityType.CORE,
    EntityType.GUNNER,
    EntityType.SENTINEL,
    EntityType.BREACH,
    EntityType.LAUNCHER,
))

transporter_set: set[EntityType] = set((
    EntityType.CONVEYOR,
    EntityType.ARMOURED_CONVEYOR,
    EntityType.BRIDGE,
    EntityType.SPLITTER,
))

no_core_passable_set: set[EntityType] = set((
    EntityType.ROAD,
    EntityType.CONVEYOR,
    EntityType.ARMOURED_CONVEYOR,
    EntityType.BRIDGE,
    EntityType.SPLITTER,
))

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

def signInt(n: int) -> int: # sign() is already taken
    """Returns the sign of an integer.

    Args:
        n (int): an integer to take the sign of

    Returns:
        int: the sign of n
    """
    if n == 0: return 0
    if n > 0: return 1
    return -1


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
    if dx == 0:
        return rx == 0 and signInt(ry) == dy
    if dy == 0:
        return ry == 0 and signInt(rx) == dx
    # fixed: must exact line
    return signInt(rx) == dx and signInt(ry) == dy and rx * dy == ry * dx


sentinel_pattern: list[list[tuple]] = [[] for _ in range(8)]
sentinel_reverse: dict[tuple, list[int]] = {}

gunner_pattern: list[list[tuple]] = [[] for _ in range(8)]
gunner_reverse: dict[tuple, list[int]] = {}

gunner_hits_core_offsets: list[int] = []
sentinel_hits_core_offsets: list[int] = []


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

    core_set = {(x,y) for x in range(-1, 2) for y in range(-1, 2)}

    
    rd = 4
    for dx in range(-rd, rd+1):
        for dy in range(-rd, rd+1):
            if (dx, dy) in core_set:
                continue
            found = False
            for dir_i in range(8):
                if found:
                    break
                for rx, ry in gunner_pattern[dir_i]:
                    # gunner at (dx,dy), shooting in direction dir_i
                    # hits tile (dx+rx, dy+ry)
                    # we want (dx+rx, dy+ry) in core_set
                    if (dx + rx, dy + ry) in core_set:
                        found = True
                        break
            if found:
                gunner_hits_core_offsets.append(dx * PH + dy)

    rd = 5
    rsq = 32
    for dx in range(-rd, rd+1):
        for dy in range(-rd, rd+1):
            if (dx, dy) in core_set:
                continue
            found = False
            for x, y in core_set:
                if (x - dx) ** 2 + (y - dy) ** 2 <= rsq:
                    found = True
                    break
            if found:
                sentinel_hits_core_offsets.append(dx * PH + dy)

    # print(len(gunner_hits_core_offsets), gunner_hits_core_offsets)
    # print(len(sentinel_hits_core_offsets), sentinel_hits_core_offsets)


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
# _debug_sentinel()
# print(sentinel_pattern)

# def _debug_gunner():
#     for i in range(8):
#         print(f"\n=== {short_directions[i]} ===")
#         hits = set(gunner_pattern[i])
#         for ry in range(-6, 7):
#             row = ""
#             for rx in range(-6, 7):
#                 if rx == 0 and ry == 0:
#                     row += "O "
#                 elif (rx, ry) in hits:
#                     row += "# "
#                 elif rx * rx + ry * ry <= GameConstants.GUNNER_VISION_RADIUS_SQ:
#                     row += ". "
#                 else:
#                     row += "  "
#             print(row)
#         print(f"  ({len(gunner_pattern[i])} tiles)")
# _debug_gunner()
# print(gunner_pattern)

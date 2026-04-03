# === AUTO-GENERATED - edits are ephemeral ===

from __future__ import annotations
from cambc import *
import random
import heapq
import array
import time
import math
import sys
from collections import deque, defaultdict

# ============================================================
# BuildManager
# ============================================================

class BuildManager:
    reserve_ti: int = 100  # scale this
    reserve_ax: int = 0

    @staticmethod
    def scale(cost: int) -> int:
        return int(cost * Globals.ct.get_scale_percent() / 100.0)



    @classmethod
    def reserve_check_builder_bot(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_builder_bot_cost()
        if (Cache.ti - ti_cost) < cls.reserve_ti * Cache.scale_ratio:
            return False
        if (Cache.ax - ax_cost) < cls.reserve_ax * Cache.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @classmethod
    def reserve_check_gunner(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_gunner_cost()
        if (Cache.ti - ti_cost) < cls.reserve_ti * Cache.scale_ratio:
            return False
        if (Cache.ax - ax_cost) < cls.reserve_ax * Cache.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @classmethod
    def reserve_check_sentinel(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_sentinel_cost()
        if (Cache.ti - ti_cost) < cls.reserve_ti * Cache.scale_ratio:
            return False
        if (Cache.ax - ax_cost) < cls.reserve_ax * Cache.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @classmethod
    def reserve_check_breach(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_breach_cost()
        if (Cache.ti - ti_cost) < cls.reserve_ti * Cache.scale_ratio:
            return False
        if (Cache.ax - ax_cost) < cls.reserve_ax * Cache.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @classmethod
    def reserve_check_launcher(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_launcher_cost()
        if (Cache.ti - ti_cost) < cls.reserve_ti * Cache.scale_ratio:
            return False
        if (Cache.ax - ax_cost) < cls.reserve_ax * Cache.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @classmethod
    def reserve_check_conveyor(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_conveyor_cost()
        if (Cache.ti - ti_cost) < cls.reserve_ti * Cache.scale_ratio:
            return False
        if (Cache.ax - ax_cost) < cls.reserve_ax * Cache.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @classmethod
    def reserve_check_splitter(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_splitter_cost()
        if (Cache.ti - ti_cost) < cls.reserve_ti * Cache.scale_ratio:
            return False
        if (Cache.ax - ax_cost) < cls.reserve_ax * Cache.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @classmethod
    def reserve_check_armoured_conveyor(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_armoured_conveyor_cost()
        if (Cache.ti - ti_cost) < cls.reserve_ti * Cache.scale_ratio:
            return False
        if (Cache.ax - ax_cost) < cls.reserve_ax * Cache.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @classmethod
    def reserve_check_bridge(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_bridge_cost()
        if (Cache.ti - ti_cost) < cls.reserve_ti * Cache.scale_ratio:
            return False
        if (Cache.ax - ax_cost) < cls.reserve_ax * Cache.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @classmethod
    def reserve_check_harvester(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_harvester_cost()
        if (Cache.ti - ti_cost) < cls.reserve_ti * Cache.scale_ratio:
            return False
        if (Cache.ax - ax_cost) < cls.reserve_ax * Cache.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @classmethod
    def reserve_check_foundry(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_foundry_cost()
        if (Cache.ti - ti_cost) < cls.reserve_ti * Cache.scale_ratio:
            return False
        if (Cache.ax - ax_cost) < cls.reserve_ax * Cache.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @classmethod
    def reserve_check_road(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_road_cost()
        if (Cache.ti - ti_cost) < cls.reserve_ti * Cache.scale_ratio:
            return False
        if (Cache.ax - ax_cost) < cls.reserve_ax * Cache.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


    @classmethod
    def reserve_check_barrier(cls) -> bool:
        ti_cost, ax_cost = Globals.ct.get_barrier_cost()
        if (Cache.ti - ti_cost) < cls.reserve_ti * Cache.scale_ratio:
            return False
        if (Cache.ax - ax_cost) < cls.reserve_ax * Cache.scale_ratio:
            Debug.log('ax branch triggered')
            return False
        return True


# ============================================================
# BuilderState
# ============================================================

class BuilderState:
    UNKNOWN = 0
    EXPLORE = 1


# ============================================================
# Cache
# ============================================================

class Cache:
    ti: int = 0
    ax: int = 0
    scale_ratio: float = 0

    @staticmethod
    def refresh():
        Cache.ti, Cache.ax = Globals.ct.get_global_resources()
        Cache.scale_ratio = Globals.ct.get_scale_percent() / 100.0


# ============================================================
# Color
# ============================================================

class Color:
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    BLACK = (0, 0, 0)
    YELLOW = (255, 255, 0)
    CYAN = (0, 255, 255)
    MAGENTA = (255, 0, 255)
    ORANGE = (255, 165, 0)
    PINK = (255, 105, 180)
    PURPLE = (128, 0, 128)
    GRAY = (128, 128, 128)
    LIME = (0, 255, 128)
    TEAL = (0, 128, 128)
    BROWN = (139, 69, 19)


# ============================================================
# Constants
# ============================================================

class Constants:
    ALL_DIRECTIONS: list[Direction] = [
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
    DIRECTIONS: list[Direction] = [
        Direction.NORTH,
        Direction.NORTHEAST,
        Direction.EAST,
        Direction.SOUTHEAST,
        Direction.SOUTH,
        Direction.SOUTHWEST,
        Direction.WEST,
        Direction.NORTHWEST,
    ]


# ============================================================
# Debug
# ============================================================

class Debug:
    @staticmethod
    def line(pos_a: Position, pos_b: Position | tuple | None = None, color: tuple = Color.WHITE):
        if pos_b is None:
            pos_b = pos_a
            pos_a = Globals.ct.get_position()
        elif isinstance(pos_b, tuple):  # assume it's a color
            color = pos_b
            pos_b = pos_a
            pos_a = Globals.ct.get_position()
        Globals.ct.draw_indicator_line(pos_a, pos_b, *color)

    @staticmethod
    def dot(pos: Position, color: tuple = Color.WHITE):
        Globals.ct.draw_indicator_dot(pos, *color)

    @staticmethod
    def log(*a, **kw):
        print(*a, **kw, file=sys.stderr)

    @staticmethod
    def error(thing):
        raise Exception(thing)

    @staticmethod
    def transpose[T](mat: list[list[T]]) -> str:
        if not mat or not mat[0]:
            return "[empty matrix]"

        rows = len(mat)
        cols = len(mat[0])

        return "\n".join(
            " ".join(str(mat[r][c]) for r in range(rows))
            for c in range(cols)
        )


# ============================================================
# Dijkstra
# ============================================================

class Dijkstra:
    _neighbors = None
    _cached_dims = None

    @classmethod
    def _build_neighbors(cls, W, H):
        if cls._cached_dims == (W, H):
            return cls._neighbors

        neighbors = [[None] * H for _ in range(W)]
        for x in range(W):
            for y in range(H):
                nbrs = []
                nx, ny = x , y -1
                if 0 <= nx < W and 0 <= ny < H:
                    nbrs.append((nx, ny))
                nx, ny = x +1, y -1
                if 0 <= nx < W and 0 <= ny < H:
                    nbrs.append((nx, ny))
                nx, ny = x +1, y 
                if 0 <= nx < W and 0 <= ny < H:
                    nbrs.append((nx, ny))
                nx, ny = x +1, y +1
                if 0 <= nx < W and 0 <= ny < H:
                    nbrs.append((nx, ny))
                nx, ny = x , y +1
                if 0 <= nx < W and 0 <= ny < H:
                    nbrs.append((nx, ny))
                nx, ny = x -1, y +1
                if 0 <= nx < W and 0 <= ny < H:
                    nbrs.append((nx, ny))
                nx, ny = x -1, y 
                if 0 <= nx < W and 0 <= ny < H:
                    nbrs.append((nx, ny))
                nx, ny = x -1, y -1
                if 0 <= nx < W and 0 <= ny < H:
                    nbrs.append((nx, ny))
                neighbors[x][y] = tuple(nbrs)
        cls._neighbors = neighbors
        cls._cached_dims = (W, H)
        return neighbors

    @classmethod
    def dists_from_pos(cls, pos: Position):
        W, H = Map.W, Map.H

        neighbors = cls._build_neighbors(W, H)

        # 2D cell costs
        cell_costs = [[0] * H for _ in range(W)]
        env_cost_map = {
            Environment.WALL: 1000000,
            Environment.EMPTY: 1,
            Environment.ORE_AXIONITE: 1,
            Environment.ORE_TITANIUM: 1,
        }
        tile_info = Map.tile_info
        for x in range(W):
            col = tile_info[x]
            cc = cell_costs[x]
            for y in range(H):
                tinfo = col[y]
                if tinfo is None:
                    cc[y] = 3
                    continue

                cc[y] = env_cost_map[tinfo.env]
                Globals.ct.get_entity_type(tinfo.building_id)
                    

        my_pos = Globals.ct.get_position()
        my_x, my_y = my_pos.x, my_pos.y

        # Dijkstra
        dist = [[1000000] * H for _ in range(W)]
        dist[pos.x][pos.y] = 0

        pq = [(0, pos.x, pos.y)]

        while pq:
            d, x, y = heapq.heappop(pq)
            if x == my_x and y == my_y:
                break

            if d > dist[x][y]:
                continue

            for nx, ny in neighbors[x][y]:
                nd = d + cell_costs[nx][ny]
                if nd < dist[nx][ny]:
                    dist[nx][ny] = nd
                    heapq.heappush(pq, (nd, nx, ny))

        return dist


# ============================================================
# DirectionPicker
# ============================================================

class DirectionPicker:
    class Candidate(NamedTuple):
        direction: Direction
        position: Position
        moveable: bool
        fill_moveable: bool
        rand_key: float

    cand: list[Candidate | None] = [None] * 9

    @classmethod
    def precompute(cls):
        for i in range(9):
            dir: Direction = Constants.ALL_DIRECTIONS[i]
            cls.cand[i] = cls.Candidate(
                dir,
                Globals.ct.get_position().add(dir),
                MoveManager.can_move(dir),
                MoveManager.can_fill_move(dir),
                random.random(),
            )

    @classmethod
    def is_better_than(cls, a: Candidate, b: Candidate) -> bool:
        if a.moveable and (not b.moveable):
            return True
        if (not a.moveable) and b.moveable:
            return False


        return a.rand_key < b.rand_key


# ============================================================
# Entrypoint
# ============================================================

class Entrypoint:
    me: Unit
    needs_init = True

    @classmethod
    def init(cls, ct: Controller):
        Globals.init(ct)
        Map.init()

        match ct.get_entity_type():
            case EntityType.CORE:
                cls.me = Core()
            case EntityType.BUILDER_BOT:
                cls.me = Builder()

    @classmethod
    def run(cls, ct: Controller):
        Globals.ct = ct  # TODO: remove when fixed
        if cls.needs_init:
            cls.init(ct)
            cls.needs_init = False

        cls.me.start_turn()
        cls.me.run_turn()
        cls.me.end_turn()


# ============================================================
# Explore
# ============================================================

class Explore:
    target: Position
    target = None

    @classmethod
    def init(cls) -> None:
        cls.target = cls.new_target()

    @classmethod
    def new_target(cls) -> Position:
        return Util.rand_pos()

    @classmethod
    def get_target(cls) -> Position:
        if Globals.ct.get_position().distance_squared(cls.target) <= 2:
            cls.target = cls.new_target()

        return cls.target


# ============================================================
# FastDijkstra
# ============================================================

class FastDijkstra:
    # actually slow!
    _neighbors = None
    _cached_dims = None

    @classmethod
    def _build_neighbors(cls, W, H):
        if cls._cached_dims == (W, H):
            return cls._neighbors

        neighbors = [[None] * H for _ in range(W)]
        for x in range(W):
            for y in range(H):
                nbrs = []
                nx, ny = x , y -1
                if 0 <= nx < W and 0 <= ny < H:
                    nbrs.append((nx, ny))
                nx, ny = x +1, y -1
                if 0 <= nx < W and 0 <= ny < H:
                    nbrs.append((nx, ny))
                nx, ny = x +1, y 
                if 0 <= nx < W and 0 <= ny < H:
                    nbrs.append((nx, ny))
                nx, ny = x +1, y +1
                if 0 <= nx < W and 0 <= ny < H:
                    nbrs.append((nx, ny))
                nx, ny = x , y +1
                if 0 <= nx < W and 0 <= ny < H:
                    nbrs.append((nx, ny))
                nx, ny = x -1, y +1
                if 0 <= nx < W and 0 <= ny < H:
                    nbrs.append((nx, ny))
                nx, ny = x -1, y 
                if 0 <= nx < W and 0 <= ny < H:
                    nbrs.append((nx, ny))
                nx, ny = x -1, y -1
                if 0 <= nx < W and 0 <= ny < H:
                    nbrs.append((nx, ny))
                neighbors[x][y] = tuple(nbrs)
        cls._neighbors = neighbors
        cls._cached_dims = (W, H)
        return neighbors

    @classmethod
    def dists_from_pos(cls, pos: Position):
        W, H = Map.W, Map.H

        neighbors = cls._build_neighbors(W, H)

        # 2D cell costs using array.array
        INF = 1000000
        cell_costs = [array.array('l', [0] * H) for _ in range(W)]
        env_cost_map = {
            Environment.WALL: INF,
            Environment.EMPTY: 1,
            Environment.ORE_AXIONITE: 1,
            Environment.ORE_TITANIUM: 1,
        }
        tile_info = Map.tile_info
        for x in range(W):
            col = tile_info[x]
            cc = cell_costs[x]
            for y in range(H):
                tinfo = col[y]
                if tinfo is None:
                    cc[y] = 3
                    continue
                cc[y] = env_cost_map[tinfo.env]

        my_pos = Globals.ct.get_position()
        my_x, my_y = my_pos.x, my_pos.y

        # Dijkstra
        dist = [array.array('l', [INF] * H) for _ in range(W)]
        dist[pos.x][pos.y] = 0

        pq = [(0, pos.x, pos.y)]

        while pq:
            d, x, y = heapq.heappop(pq)
            if x == my_x and y == my_y:
                break

            if d > dist[x][y]:
                continue

            for nx, ny in neighbors[x][y]:
                nd = d + cell_costs[nx][ny]
                if nd < dist[nx][ny]:
                    dist[nx][ny] = nd
                    heapq.heappush(pq, (nd, nx, ny))

        return dist


# ============================================================
# FlatDijkstra
# ============================================================

class FlatDijkstra:
    _neighbors = None
    _cached_dims = None

    @classmethod
    def _build_neighbors(cls, W, H):
        if cls._cached_dims == (W, H):
            return cls._neighbors

        WH = W * H
        neighbors = [None] * WH
        for x in range(W):
            base = x * H
            for y in range(H):
                nbrs = []
                nx, ny = x , y -1
                if 0 <= nx < W and 0 <= ny < H:
                    nbrs.append(nx * H + ny)
                nx, ny = x +1, y -1
                if 0 <= nx < W and 0 <= ny < H:
                    nbrs.append(nx * H + ny)
                nx, ny = x +1, y 
                if 0 <= nx < W and 0 <= ny < H:
                    nbrs.append(nx * H + ny)
                nx, ny = x +1, y +1
                if 0 <= nx < W and 0 <= ny < H:
                    nbrs.append(nx * H + ny)
                nx, ny = x , y +1
                if 0 <= nx < W and 0 <= ny < H:
                    nbrs.append(nx * H + ny)
                nx, ny = x -1, y +1
                if 0 <= nx < W and 0 <= ny < H:
                    nbrs.append(nx * H + ny)
                nx, ny = x -1, y 
                if 0 <= nx < W and 0 <= ny < H:
                    nbrs.append(nx * H + ny)
                nx, ny = x -1, y -1
                if 0 <= nx < W and 0 <= ny < H:
                    nbrs.append(nx * H + ny)
                neighbors[base + y] = tuple(nbrs)
        cls._neighbors = neighbors
        cls._cached_dims = (W, H)
        return neighbors

    @classmethod
    def dists_from_pos(cls, pos: Position):
        W, H = Map.W, Map.H
        WH = W * H
        INF = 1000000

        neighbors = cls._build_neighbors(W, H)

        # Flat cell costs
        cell_costs = [0] * WH
        env_cost_map = {
            Environment.WALL: INF,
            Environment.EMPTY: 1,
            Environment.ORE_AXIONITE: 1,
            Environment.ORE_TITANIUM: 1,
        }
        tile_info = Map.tile_info
        for x in range(W):
            col = tile_info[x]
            base = x * H
            for y in range(H):
                tinfo = col[y]
                if tinfo is None:
                    cell_costs[base + y] = 3
                else:
                    cell_costs[base + y] = env_cost_map[tinfo.env]

        my_pos = Globals.ct.get_position()
        my_idx = my_pos.x * H + my_pos.y

        # Dijkstra
        dist = [INF] * WH
        start = pos.x * H + pos.y
        dist[start] = 0

        heappush = heapq.heappush
        heappop = heapq.heappop
        pq = [(0, start)]

        while pq:
            d, idx = heappop(pq)
            if idx == my_idx:
                break

            if d > dist[idx]:
                continue

            for nidx in neighbors[idx]:
                nd = d + cell_costs[nidx]
                if nd < dist[nidx]:
                    dist[nidx] = nd
                    heappush(pq, (nd, nidx))

        # Unpack to 2D
        return [[dist[x * H + y] for y in range(H)] for x in range(W)]


# ============================================================
# GlobalBfs
# ============================================================

class GlobalBfs:
    _neighbors = None
    _cached_dims = None

    @classmethod
    def _build_neighbors(cls, W, H):
        if cls._cached_dims == (W, H):
            return cls._neighbors

        neighbors = [[None] * H for _ in range(W)]
        for x in range(W):
            for y in range(H):
                nbrs = []
                nx, ny = x , y -1
                if 0 <= nx < W and 0 <= ny < H:
                    nbrs.append((nx, ny))
                nx, ny = x +1, y -1
                if 0 <= nx < W and 0 <= ny < H:
                    nbrs.append((nx, ny))
                nx, ny = x +1, y 
                if 0 <= nx < W and 0 <= ny < H:
                    nbrs.append((nx, ny))
                nx, ny = x +1, y +1
                if 0 <= nx < W and 0 <= ny < H:
                    nbrs.append((nx, ny))
                nx, ny = x , y +1
                if 0 <= nx < W and 0 <= ny < H:
                    nbrs.append((nx, ny))
                nx, ny = x -1, y +1
                if 0 <= nx < W and 0 <= ny < H:
                    nbrs.append((nx, ny))
                nx, ny = x -1, y 
                if 0 <= nx < W and 0 <= ny < H:
                    nbrs.append((nx, ny))
                nx, ny = x -1, y -1
                if 0 <= nx < W and 0 <= ny < H:
                    nbrs.append((nx, ny))
                neighbors[x][y] = tuple(nbrs)
        cls._neighbors = neighbors
        cls._cached_dims = (W, H)
        return neighbors

    @classmethod
    def dists_from_pos(cls, pos: Position):
        W, H = Map.W, Map.H
        INF = 1000000
        WALL = Environment.WALL

        neighbors = cls._build_neighbors(W, H)
        tile_info = Map.tile_info

        dist = [[INF] * H for _ in range(W)]
        dist[pos.x][pos.y] = 0

        my_pos = Globals.ct.get_position()
        mx, my = my_pos.x, my_pos.y

        q = deque([(pos.x, pos.y)])

        while q:
            x, y = q.popleft()
            d = dist[x][y] + 1

            for nx, ny in neighbors[x][y]:
                if dist[nx][ny] == INF:
                    ti = tile_info[nx][ny]
                    if ti is not None and ti.env == WALL:
                        continue
                    dist[nx][ny] = d
                    if nx == mx and ny == my:
                        return dist
                    q.append((nx, ny))

        return dist


# ============================================================
# GlobalBitmaskBfs
# ============================================================

class GlobalBitmaskBfs:
    @classmethod
    def dists_from_pos(cls, pos: Position):
        S = MapMask.STRIDE
        FULL = MapMask.FULL
        passable = FULL & ~MapMask.wall
        W, H = Map.W, Map.H

        dist_flat = [1000000] * (S * H)
        start_idx = pos.y * S + pos.x
        dist_flat[start_idx] = 0

        # Early exit target: our position
        my_pos = Globals.ct.get_position()
        target_bit = 1 << (my_pos.y * S + my_pos.x)

        reached_from = 1 << start_idx
        reached_to = 0

        step = 1
        while reached_from != reached_to:
            # Expand 8-directionally (padding column in STRIDE prevents wrap)
            wide = reached_from | (reached_from << 1) | (reached_from >> 1)
            reached_to = (wide | (wide << S) | (wide >> S)) & passable

            # New cells = symmetric difference
            changed = reached_from ^ reached_to

            # Assign distances to new cells
            while changed:
                lsb = changed & -changed
                changed ^= lsb
                dist_flat[lsb.bit_length() - 1] = step

            # Early exit when we've reached our unit
            if reached_to & target_bit:
                break

            step += 1
            reached_from, reached_to = reached_to, reached_from

        return [[dist_flat[y * S + x] for y in range(H)] for x in range(W)]


# ============================================================
# Globals
# ============================================================

class Globals:
    ct: Controller

    @classmethod
    def init(cls, controller: Controller):
        cls.ct = controller


# ============================================================
# LocalMask
# ============================================================

class LocalMask:
    RADIUS: int
    WIDTH: int      # actual data columns (2*RADIUS+1)
    HEIGHT: int     # actual data rows   (2*RADIUS+1)
    STRIDE: int     # WIDTH + 1 (includes padding column)

    FULL: int

    wall: int = 0
    titanium: int = 0
    axionite: int = 0

    @staticmethod
    def init():
        LocalMask.RADIUS = 4
        LocalMask.WIDTH = 2 * LocalMask.RADIUS + 1
        LocalMask.HEIGHT = LocalMask.WIDTH
        LocalMask.STRIDE = LocalMask.WIDTH + 1

        row_bits = (1 << LocalMask.WIDTH) - 1
        LocalMask.FULL = 0
        for row in range(LocalMask.HEIGHT):
            LocalMask.FULL |= row_bits << (row * LocalMask.STRIDE)

    @staticmethod
    def encode_index(dx, dy) -> int:
        return (dy + LocalMask.RADIUS) * LocalMask.STRIDE + (dx + LocalMask.RADIUS)

    @staticmethod
    def encode_bit(dx, dy) -> int:
        return 1 << LocalMask.encode_index(dx, dy)

    @classmethod
    def set_pos(cls, pos: Position) -> int:
        my_pos = Globals.ct.get_position()
        return cls.encode_bit(pos.x - my_pos.x, pos.y - my_pos.y)

    @staticmethod
    def expand8(mask: int) -> int:
        # does not handle impassibles
        wide: int = mask | (mask << 1) | (mask >> 1)
        return (wide | (wide << LocalMask.STRIDE) | (wide >> LocalMask.STRIDE)) & LocalMask.FULL

    @staticmethod
    def expand4(mask: int) -> int:
        # does not handle impassibles
        return (mask | (mask << 1) | (mask >> 1)
                | (mask << LocalMask.STRIDE) | (mask >> LocalMask.STRIDE)) & LocalMask.FULL


    @staticmethod
    def decode_index(idx: int) -> tuple[int, int]:
        dx = (idx % LocalMask.STRIDE) - LocalMask.RADIUS
        dy = (idx // LocalMask.STRIDE) - LocalMask.RADIUS
        return dx, dy



    @staticmethod
    def debug_mask(mask: int):
        center: Position = Globals.ct.get_position()
        for i in range(LocalMask.STRIDE * LocalMask.HEIGHT):
            if mask & (1 << i):
                dx, dy = LocalMask.decode_index(i)
                Debug.dot(Position(center.x + dx, center.y + dy))



    @staticmethod
    def debug_string(mask: int) -> str:
        lines = []
        for row in range(LocalMask.HEIGHT):
            data = []
            for col in range(LocalMask.WIDTH):
                idx = row * LocalMask.STRIDE + col
                data.append('#' if mask & (1 << idx) else '.')
            pad_idx = row * LocalMask.STRIDE + LocalMask.WIDTH
            pad = '#' if mask & (1 << pad_idx) else '.'
            dy = row - LocalMask.RADIUS
            lines.append(f"{''.join(data)}|{pad}  dy={dy:+d}")
        return '\n'.join(lines)


# ============================================================
# Map
# ============================================================

class Map:
    W: int = 0
    H: int = 0
    tile_info: list[list[TileInfo | None]] = []  # [x][y]

    @staticmethod
    def init():
        Map.W = Globals.ct.get_map_width()
        Map.H = Globals.ct.get_map_height()

        Profiler.start()
        Map.tile_info = [[None] * Map.H for _ in range(Map.W)]
        Profiler.end('tile_info init')

        MapMask.init()
        LocalMask.init()

    @staticmethod
    def fill_tile_info():
        round = Globals.ct.get_current_round()
        for pos in Globals.ct.get_nearby_tiles(20):
            tile_env: Environment = Globals.ct.get_tile_env(pos)

            ti: TileInfo | None = Map.tile_info[pos.x][pos.y]
            if ti is None:
                ti = TileInfo()
                Map.tile_info[pos.x][pos.y] = ti

            ti.env = tile_env
            ti.round = round
            ti.building_id = Globals.ct.get_tile_building_id(pos)
            ti.builder_bot_id = Globals.ct.get_tile_builder_bot_id(pos)

    @staticmethod
    def fill():
        mypos: Position = Globals.ct.get_position()

        # reset local masks
        LocalMask.wall = 0
        LocalMask.titanium = 0
        LocalMask.axionite = 0

        pos: Position
        for pos in Globals.ct.get_nearby_tiles(20):
            tile_env: Environment = Globals.ct.get_tile_env(pos)
            dx: int = pos.x - mypos.x
            dy: int = pos.y - mypos.y
            global_bit: int = MapMask.encode_bit(pos)
            local_bit: int = LocalMask.encode_bit(dx, dy)

            if tile_env == Environment.WALL:
                MapMask.wall |= global_bit
                LocalMask.wall |= local_bit
            elif tile_env == Environment.ORE_TITANIUM:
                MapMask.titanium |= global_bit
                LocalMask.titanium |= local_bit
            elif tile_env == Environment.ORE_AXIONITE:
                MapMask.axionite |= global_bit
                LocalMask.axionite |= local_bit
            else:
                assert tile_env == Environment.EMPTY


# ============================================================
# MapMask
# ============================================================

class MapMask:
    STRIDE: int
    FULL: int

    wall: int = 0
    titanium: int = 0
    axionite: int = 0

    @staticmethod
    def init():
        MapMask.STRIDE = Map.W + 1

        row_bits = (1 << Map.W) - 1
        MapMask.FULL = 0
        for row in range(Map.H):
            MapMask.FULL |= row_bits << (row * MapMask.STRIDE)

    @staticmethod
    def encode_index(pos: Position) -> int:
        return pos.y * MapMask.STRIDE + pos.x

    @staticmethod
    def encode_bit(pos: Position) -> int:
        return 1 << MapMask.encode_index(pos)

    @staticmethod
    def decode_index(idx: int) -> Position:
        return Position(idx % MapMask.STRIDE, idx // MapMask.STRIDE)

    @staticmethod
    def debug_mask(mask: int):
        for i in range(MapMask.STRIDE * Map.H):
            if mask & (1 << i):
                Debug.dot(MapMask.decode_index(i))

    @staticmethod
    def debug_string(mask: int) -> str:
        lines = []
        for row in range(Map.H):
            data = []
            for col in range(Map.W):
                idx = row * MapMask.STRIDE + col
                data.append('#' if mask & (1 << idx) else '.')
            pad_idx = row * MapMask.STRIDE + Map.W
            pad = '#' if mask & (1 << pad_idx) else '.'
            lines.append(f"{''.join(data)}|{pad}  y={row}")
        return '\n'.join(lines)


# ============================================================
# MoveManager
# ============================================================

class MoveManager:
    @staticmethod
    def can_move(direction: Direction) -> bool:
        if direction == Direction.CENTRE:
            return True
        return Globals.ct.can_move(direction)

    @staticmethod
    def can_fill_move(direction: Direction) -> bool:
        if MoveManager.can_move(direction):
            return True
        if Globals.ct.get_action_cooldown() != 0:
            return False

        pos: Position = Globals.ct.get_position().add(direction)
        if not Util.on_the_map(pos):
            return False
        if not Globals.ct.is_tile_empty(pos):
            return False  # no building and not wall, could check marker?
        if not Globals.ct.can_build_road(pos):
            return False
        return True


    @staticmethod
    def move(direction: Direction):
        Globals.ct.move(direction)


# ============================================================
# OmNom
# ============================================================

class OmNom:
    cur_target: Position
    cur_target = None
    bug_pos: Position
    bug_pos = None

    last_obstacle_found: Position | None = None
    rotate_right: bool | None = None
    min_dist: int = 1_000_000

    bug_path: list[Position] = []
    bug_min_dist: list[int] = []
    bug_last_obstacle_found: list[Position | None] = []

    bfs_dist: list[int] = [0] * 9

    @classmethod
    def can_move_bug(cls, pos: Position) -> bool:
        if not Util.on_the_map(pos):
            return False
        if (MapMask.encode_bit(pos) & MapMask.wall) != 0:
            return False
        return True

    @classmethod
    def move_bug(cls, pos: Position) -> None:
        cls.bug_pos = pos

        cls.bug_path.append(cls.bug_pos)
        cls.bug_min_dist.append(cls.min_dist)
        cls.bug_last_obstacle_found.append(cls.last_obstacle_found)

    @classmethod
    def restore_bug_in_vision(cls) -> None:
        while cls.bug_path and not Globals.ct.is_in_vision(cls.bug_path[-1]):
            cls.bug_path.pop()
            cls.bug_min_dist.pop()
            cls.bug_last_obstacle_found.pop()

        if cls.bug_path:
            cls.bug_pos = cls.bug_path[-1]
            cls.min_dist = cls.bug_min_dist[-1]
            cls.last_obstacle_found = cls.bug_last_obstacle_found[-1]
        else:
            cls.reset_bug()

    @classmethod
    def reset_bug(cls) -> None:
        cls.bug_pos = Globals.ct.get_position()
        cls.min_dist = 1_000_000
        cls.last_obstacle_found = None
        cls.bug_path = []                
        cls.bug_min_dist = []            
        cls.bug_last_obstacle_found = [] 
        cls.rotate_right = None


    @classmethod
    def bug_step(cls) -> bool:
        # moves bug toward cur_target, returns True if should keep stepping

        dist: int = cls.bug_pos.distance_squared(cls.cur_target)
        if dist < cls.min_dist:
            cls.min_dist = dist
            cls.last_obstacle_found = None

        dir: Direction
        if cls.last_obstacle_found is not None:
            dir = cls.bug_pos.direction_to(cls.last_obstacle_found)
        else:
            dir = cls.bug_pos.direction_to(cls.cur_target)

        new_pos: Position = cls.bug_pos.add(dir)
        if Util.on_the_map(new_pos) and not Globals.ct.is_in_vision(new_pos):
            return False

        if cls.can_move_bug(new_pos):
            # mini-reset, keep min_dist, bug path
            cls.rotate_right = None
            cls.last_obstacle_found = None
            cls.move_bug(new_pos)
            return True

        if cls.rotate_right is None:
            # TODO: do rotation check
            cls.rotate_right = True

        for _ in range(16):
            if cls.rotate_right:
                dir = dir.rotate_right()
            else:
                dir = dir.rotate_left()
            new_pos = cls.bug_pos.add(dir)

            if Util.on_the_map(new_pos) and not Globals.ct.is_in_vision(new_pos):
                return False

            if cls.can_move_bug(new_pos):
                cls.move_bug(new_pos)
                return True

            if Util.on_the_map(new_pos):
                cls.last_obstacle_found = new_pos
            else:
                cls.rotate_right ^= True

        Debug.log("fell off 16 loop")
        return False

    @classmethod
    def bug_loop(cls):
        if cls.bug_pos is None or not Globals.ct.is_in_vision(cls.bug_pos):
            cls.restore_bug_in_vision()
        for _ in range(10):
            if cls.bug_pos.distance_squared(cls.cur_target) <= 2: # adj
                break

            keep_going = cls.bug_step()
            if not keep_going:
                break

    @classmethod
    def move_to(cls, target: Position):
        if cls.cur_target is None or target != cls.cur_target:
            cls.reset_bug()
            cls.cur_target = target
            
        cls.bug_loop()
        # ... BFS + pick

    @classmethod
    def run_bfs(cls):
        pass


    @classmethod
    def debug_path(cls):
        path_len = len(cls.bug_path)
        max_len = max(1, path_len - 1)
        for i in range(path_len):
            t = i / max_len
            intensity = int(50 + 205 * t)
            Globals.ct.draw_indicator_dot(
                cls.bug_path[i], 0, intensity, intensity)
        if cls.bug_pos is not None:
            Globals.ct.draw_indicator_dot(cls.bug_pos, 0, 255, 255)


# ============================================================
# Player
# ============================================================

class Player:
    def run(self, ct):
        Entrypoint.run(ct)


# ============================================================
# Profiler
# ============================================================

class Profiler:
    _stack: list = []
    _stats: dict = {}  # desc -> [count, mean, M2, max]

    @classmethod
    def start(cls):
        cls._stack.append(time.perf_counter())

    @classmethod
    def end(cls, desc: str):
        end_time = time.perf_counter()
        if not cls._stack:
            return
        start_time = cls._stack.pop()
        elapsed = end_time - start_time
        if desc in cls._stats:
            entry = cls._stats[desc]
            entry[0] += 1
            delta = elapsed - entry[1]
            entry[1] += delta / entry[0]
            entry[2] += delta * (elapsed - entry[1])
            if elapsed > entry[3]:
                entry[3] = elapsed
        else:
            cls._stats[desc] = [1, elapsed, 0.0, elapsed]

        s = f"[P] {desc}: {cls._format_time(elapsed)}"
        print(s)

    @classmethod
    def end_now(cls, desc: str):
        end_time = time.perf_counter()
        if not cls._stack:
            return
        start_time = cls._stack.pop()
        elapsed = end_time - start_time

        s = f"[P] {desc}: {cls._format_time(elapsed)}"
        print(s)
        Debug.log(s)

    @classmethod
    def _format_time(cls, t: float) -> str:
        if t < 1e-6:
            return f"{t * 1e9:.3f}ns"
        elif t < 1e-3:
            return f"{t * 1e6:.3f}µs"
        elif t < 1:
            return f"{t * 1e3:.3f}ms"
        else:
            return f"{t:.3f}s"

    @classmethod
    def report(cls):
        if not cls._stats:
            return
        for desc, (count, mean, M2, max_time) in sorted(cls._stats.items()):
            stddev = math.sqrt(M2 / count) if count > 1 else 0.0
            s = (f"[P] {desc}: "
                 f"avg={cls._format_time(mean)}, "
                 f"stddev={cls._format_time(stddev)}, "
                 f"max={cls._format_time(max_time)}, "
                 f"count={count}")
            print(s)
            Debug.log(s)

    @classmethod
    def reset(cls):
        cls._stack.clear()
        cls._stats.clear()


# ============================================================
# TileInfo
# ============================================================

class TileInfo:
    env: Environment
    round: int
    building_id: int | None
    builder_bot_id: int | None
    easily_passable: bool  # allied core/road/conveyor


# ============================================================
# Unit
# ============================================================

class Unit:
    def __init__(self):
        pass

    def start_turn(self):
        Profiler.start()
        Map.fill()
        Profiler.end("fill")

        Profiler.start()
        Map.fill_tile_info()
        Profiler.end("fill_tile_info")

        Cache.refresh()

    def run_turn(self):
        raise Exception("did you forgot to override? (yes)")

    def end_turn(self):
        if Globals.ct.get_current_round() == 1999:
            Profiler.report()


# ============================================================
# Util
# ============================================================

class Util:
    @staticmethod
    def on_the_map(pos: Position) -> bool:
        return 0 <= pos.x < Map.W and 0 <= pos.y < Map.H

    @staticmethod
    def rand_pos() -> Position:
        return Position(random.randrange(Map.W), random.randrange(Map.H))


    @staticmethod
    def is_cardinal(dir: Direction) -> bool:
        # not great, to optimise, create polyfill for Direction
        dx, dy = dir.delta()
        return (dx == 0) ^ (dy == 0)

    @staticmethod
    def is_diagonal(dir: Direction) -> bool:
        dx, dy = dir.delta()
        return dx != 0 and dy != 0


# ============================================================
# Builder
# ============================================================

class Builder(Unit):
    explore_target: Position
    state_map: dict
    core_pos: Position

    def __init__(self):
        super().__init__()
        Explore.init()

        self.state_map = {
            BuilderState.EXPLORE: self.state_explore
        }
        self.state = BuilderState.EXPLORE

        core_id = Globals.ct.get_tile_building_id(Globals.ct.get_position())
        self.core_pos = Globals.ct.get_position(core_id)


    def start_turn(self):
        super().start_turn()
        self.explore_target = Explore.get_target()

    def run_turn(self):
        self.state_map[self.state]()

    def end_turn(self):
        super().end_turn()

    def state_explore(self):
        target = Explore.get_target()
        Debug.line(target)


        # Profiler.start()
        # dist = GlobalBitmaskBfs.dists_from_pos(target)
        # Profiler.end("GlobalBitmaskBfs")

        # Profiler.start()
        # dist = GlobalBfs.dists_from_pos(target)
        # Profiler.end("GlobalBfs")

        Profiler.start()
        dist = FlatDijkstra.dists_from_pos(target)
        Profiler.end("FlatDijkstra")

        Profiler.start()
        dist = FastDijkstra.dists_from_pos(target)
        Profiler.end("FastDijkstra")

        Profiler.start()
        dist = Dijkstra.dists_from_pos(target)
        Profiler.end("Dijkstra")


        cur_pos = Globals.ct.get_position()

        # Build harvester if possible
        for d in Constants.DIRECTIONS:
            check_pos = cur_pos.add(d)
            if Globals.ct.can_build_harvester(check_pos):
                Globals.ct.build_harvester(check_pos)
                break

        # Rank directions by dist of neighbor cell
        candidates = []
        for d in Constants.DIRECTIONS:
            np = cur_pos.add(d)
            if Util.on_the_map(np):
                candidates.append((dist[np.x][np.y], d))
        candidates.sort(key=lambda e: e[0])

        # Try moving toward lowest dist, building road if blocked
        for nd, d in candidates:
            move_pos = cur_pos.add(d)

            if Globals.ct.can_move(d):
                Globals.ct.move(d)
                break

            if Globals.ct.can_build_road(move_pos):
                Globals.ct.build_road(move_pos)

                if Globals.ct.can_move(d):
                    Globals.ct.move(d)
                    break


# ============================================================
# Core
# ============================================================

class Core(Unit):
    def __init__(self):
        super().__init__()
        self.num_spawned = 0

    def start_turn(self):
        super().start_turn()

    def run_turn(self):
        if self.num_spawned < 3:
            pos = Globals.ct.get_position().add(random.choice(Constants.DIRECTIONS))
            if Globals.ct.can_spawn(pos):
                Globals.ct.spawn_builder(pos)
                self.num_spawned += 1

    def end_turn(self):
        super().end_turn()



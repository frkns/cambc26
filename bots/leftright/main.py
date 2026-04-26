# === AUTO-GENERATED - edits are ephemeral ===

from __future__ import annotations
from cambc import *
import random
import sys

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
    ALL_DIRECTIONS: list[Direction] = [d for d in Direction]
    DIRECTIONS: list[Direction] = [d for d in Direction if d != Direction.CENTRE]


# ============================================================
# Debug
# ============================================================

class Debug:
    @staticmethod
    def line(pos_a: Position, pos_b: Position, color: tuple = Color.WHITE):
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
# Globals
# ============================================================

class Globals:
    ct: Controller

    @staticmethod
    def init(controller: Controller):
        Globals.ct = controller


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
        LocalMask.STRIDE = LocalMask.WIDTH + 1  # one extra zero-column on the right

        # FULL: 1s in every valid cell, 0s in every padding cell
        row_bits = (1 << LocalMask.WIDTH) - 1       # WIDTH ones
        LocalMask.FULL = 0
        for row in range(LocalMask.HEIGHT):
            LocalMask.FULL |= row_bits << (row * LocalMask.STRIDE)

    @staticmethod
    def encode_index(dx, dy) -> int:
        return (dy + LocalMask.RADIUS) * LocalMask.STRIDE + (dx + LocalMask.RADIUS)

    @staticmethod
    def encode_bit(dx, dy) -> int:
        return 1 << LocalMask.encode_index(dx, dy)

    @staticmethod
    def decode_index(idx: int):
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


# ============================================================
# Map
# ============================================================

class Map:
    W: int = 0
    H: int = 0

    @staticmethod
    def init():
        Map.W = Globals.ct.get_map_width()
        Map.H = Globals.ct.get_map_height()
        MapMask.init()
        LocalMask.init()

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
    STRIDE: int     # Map.W + 1 (includes padding column)
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


# ============================================================
# MoveManager
# ============================================================

class MoveManager:
    @staticmethod
    def can_move(direction: Direction):
        return Globals.ct.can_move(direction)

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
        cls.min_dist = 1_000_000
        cls.bug_pos = Globals.ct.get_position()
        cls.last_obstacle_found = None


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
        if not Globals.ct.is_in_vision(new_pos):
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
            keep_going = cls.bug_step()
            if not keep_going:
                break

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
# Unit
# ============================================================

class Unit:
    def __init__(self):
        pass

    def start_turn(self):
        Map.fill()
        Cache.refresh()

    def run_turn(self):
        raise Exception("did you forgot to override? (yes)")

    def end_turn(self):
        pass


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

    def __init__(self):
        super().__init__()
        Explore.init()

        self.state_map = {
            BuilderState.EXPLORE: self.state_explore
        }
        self.state = BuilderState.EXPLORE

    def start_turn(self):
        super().start_turn()
        self.explore_target = Explore.get_target()

    def run_turn(self):
        self.state_map[self.state]()

    def end_turn(self):
        super().end_turn()

    def state_explore(self):
        OmNom.cur_target = self.explore_target
        OmNom.bug_loop()
        OmNom.debug_path()

        for d in Direction:
            check_pos = Globals.ct.get_position().add(d)
            if Globals.ct.can_build_harvester(check_pos):
                Globals.ct.build_harvester(check_pos)
                break

            move_dir: Direction = random.choice(Constants.DIRECTIONS)
            move_pos: Position = Globals.ct.get_position().add(move_dir)

            move_pos_env: Environment | None = (Globals.ct.get_tile_env(move_pos)
                                                if Util.on_the_map(move_pos)
                                                else None)

            dir = Direction.WEST if (move_pos.x + move_pos.y) & 1 else Direction.EAST
            if (move_pos_env not in (
                    None,
                    Environment.ORE_AXIONITE,
                    Environment.ORE_TITANIUM)
                    and
                    Globals.ct.can_build_conveyor(move_pos, dir)):
                Globals.ct.build_conveyor(move_pos, dir)

            if Globals.ct.can_move(move_dir):
                Globals.ct.move(move_dir)


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




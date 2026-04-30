"""Mythos - from-scratch Battlecode bot built against live rules at battlecode.cam.

Engine contract: each unit gets its own Player instance; engine calls run(ct)
once per round per unit. Cross-unit team state lives in module-level globals.

Strategy summary
----------------
- Core: spawn builders up to a population cap that scales with round number.
- Builders: build harvesters adjacent to ore, then lay conveyors back toward
  the core to satisfy the "resources delivered to core" tiebreaker. Once the
  economy stabilizes, transition to building turrets and launchers around the
  perimeter.
- Gunners: face the cardinal direction with the most enemy targets in line;
  fire when ammo and cooldown allow.
- Sentinels: target the densest enemy cluster reachable by the cone.
- Breach: fire at enemy clusters; splash hits the 8 neighbours.
- Launchers: throw enemy bots far from our core; supportive launches throw
  ally bots toward enemy concentrations when there is profit to be had.
"""

import random
import sys
import traceback
from collections import defaultdict, deque

from cambc import (
    Controller,
    Direction,
    EntityType,
    Environment,
    GameConstants,
    Position,
    ResourceType,
    Team,
)


# --------------------------------------------------------------------------
# Direction / position helpers
# --------------------------------------------------------------------------

ALL_DIRS = list(Direction)
DIRS_8 = [d for d in Direction if d != Direction.CENTRE]
CARDINALS = (Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST)
DIAGONALS = (
    Direction.NORTHEAST,
    Direction.SOUTHEAST,
    Direction.SOUTHWEST,
    Direction.NORTHWEST,
)
DELTA_TO_DIR = {d.delta(): d for d in Direction}


def best_cardinal_toward(src: Position, dst: Position) -> Direction:
    dx = dst.x - src.x
    dy = dst.y - src.y
    if dx == 0 and dy == 0:
        return Direction.NORTH
    if abs(dx) >= abs(dy):
        return Direction.EAST if dx > 0 else Direction.WEST
    return Direction.SOUTH if dy > 0 else Direction.NORTH


def best_dir_toward(src: Position, dst: Position) -> Direction:
    dx = dst.x - src.x
    dy = dst.y - src.y
    sx = (dx > 0) - (dx < 0)
    sy = (dy > 0) - (dy < 0)
    return DELTA_TO_DIR.get((sx, sy), Direction.CENTRE)


# --------------------------------------------------------------------------
# Game constants reconciled against live docs (2026-04-30)
# --------------------------------------------------------------------------

# Starting resources / global pacing
STARTING_TI = 500
PASSIVE_TI_PER_4 = 10  # +10 Ti every 4 rounds
MAX_TURNS = 2000
MAX_UNITS = 50
RESOURCE_STACK = 10
AX_TO_TI = 4  # core convert: 1 refined ax -> 4 Ti

# Vision squared
VRSQ = {
    EntityType.CORE: 36,
    EntityType.BUILDER_BOT: 20,
    EntityType.GUNNER: 13,
    EntityType.SENTINEL: 32,
    EntityType.BREACH: 2,
    EntityType.LAUNCHER: 26,
}

# Combat numbers (live docs)
GUNNER_DMG_BASE = 10
GUNNER_DMG_AX = 25
SENTINEL_DMG = 18
SENTINEL_STUN_CD = 5
BREACH_DMG = 40
BREACH_SPLASH = 20
BREACH_ATTACK_RSQ = 24

# Costs as (titanium, axionite)
COST = {
    EntityType.BUILDER_BOT: (30, 0),
    EntityType.HARVESTER: (20, 0),
    EntityType.FOUNDRY: (40, 0),
    EntityType.GUNNER: (10, 0),
    EntityType.SENTINEL: (30, 0),
    EntityType.BREACH: (15, 10),
    EntityType.LAUNCHER: (20, 0),
    EntityType.CONVEYOR: (3, 0),
    EntityType.SPLITTER: (6, 0),
    EntityType.BRIDGE: (20, 0),
    EntityType.ARMOURED_CONVEYOR: (5, 5),
    EntityType.ROAD: (1, 0),
    EntityType.BARRIER: (3, 0),
}

# Tiles a builder can stand on
WALKABLE_BUILDINGS = frozenset(
    {
        EntityType.CONVEYOR,
        EntityType.SPLITTER,
        EntityType.ARMOURED_CONVEYOR,
        EntityType.BRIDGE,
        EntityType.ROAD,
        EntityType.CORE,
    }
)

# Buildings that produce or move resources - good neighbours for routing
RESOURCE_BUILDINGS = frozenset(
    {
        EntityType.HARVESTER,
        EntityType.CONVEYOR,
        EntityType.SPLITTER,
        EntityType.BRIDGE,
        EntityType.ARMOURED_CONVEYOR,
        EntityType.FOUNDRY,
    }
)

# Per-turn CPU budget in microseconds (2000 hard limit -> stop work at 1700)
TIME_BUDGET = 1700


# --------------------------------------------------------------------------
# Cross-unit team state
# --------------------------------------------------------------------------


class TS:
    """Team-shared state. All units in this Python process share this class."""

    initialized = False
    my_team = None
    enemy_team = None
    map_w = 0
    map_h = 0
    core_pos = None  # Position of our core
    enemy_core_guess = None  # Best symmetry guess
    builder_spawn_count = 0
    # Round we last extended a route - to throttle extension attempts
    routes_built = 0


def first_init(ct: Controller) -> None:
    if TS.initialized:
        return
    TS.my_team = ct.get_team()
    TS.enemy_team = Team.B if TS.my_team == Team.A else Team.A
    TS.map_w = ct.get_map_width()
    TS.map_h = ct.get_map_height()
    if ct.get_entity_type() == EntityType.CORE:
        TS.core_pos = ct.get_position()
        # Default enemy core guess via 180-degree rotation
        TS.enemy_core_guess = Position(
            TS.map_w - 1 - TS.core_pos.x,
            TS.map_h - 1 - TS.core_pos.y,
        )
    TS.initialized = True


def ensure_core_pos(ct: Controller) -> None:
    """For non-core units: if core_pos is None, scan vision for our core."""
    if TS.core_pos is not None:
        return
    try:
        for bid in ct.get_nearby_buildings():
            if (
                ct.get_entity_type(bid) == EntityType.CORE
                and ct.get_team(bid) == TS.my_team
            ):
                TS.core_pos = ct.get_position(bid)
                TS.enemy_core_guess = Position(
                    TS.map_w - 1 - TS.core_pos.x,
                    TS.map_h - 1 - TS.core_pos.y,
                )
                return
    except Exception:
        pass


# --------------------------------------------------------------------------
# Geometry / map predicates
# --------------------------------------------------------------------------


def in_map(x: int, y: int) -> bool:
    return 0 <= x < TS.map_w and 0 <= y < TS.map_h


def time_left(ct: Controller) -> bool:
    try:
        return ct.get_cpu_time_elapsed() < TIME_BUDGET
    except Exception:
        return True


# --------------------------------------------------------------------------
# Core
# --------------------------------------------------------------------------


def core_turn(self, ct: Controller) -> None:
    if TS.core_pos is None:
        TS.core_pos = ct.get_position()
        TS.enemy_core_guess = Position(
            TS.map_w - 1 - TS.core_pos.x,
            TS.map_h - 1 - TS.core_pos.y,
        )

    rnd = ct.get_current_round()

    # Late-game: convert refined axionite to titanium only if titanium is dry
    # AND we're not in tiebreaker territory. The tiebreaker rewards delivered
    # axionite, so we should NOT convert unless we genuinely need Ti to act.
    try:
        ti, ax = ct.get_global_resources()
    except Exception:
        ti, ax = 0, 0

    # Population planning. Empirically 4 builders works best — more pile up
    # near the core and block each other's mobility.
    if rnd < 30:
        target_pop = 4
    elif rnd < 200:
        target_pop = 4
    elif rnd < 800:
        target_pop = 5
    else:
        target_pop = 4

    if ct.get_action_cooldown() > 0:
        return

    try:
        live = ct.get_unit_count()
    except Exception:
        live = 0
    if live >= MAX_UNITS - 1:
        return

    # Use a live unit count so we replenish dead builders, but never exceed
    # target_pop (which is conservative because crowding hurts mobility).
    estimated_builders = max(0, live - 1)  # subtract core
    if estimated_builders >= target_pop:
        return

    # Try to spawn on first available adjacent tile
    my_pos = ct.get_position()
    # Prefer outward direction (toward enemy core)
    if TS.enemy_core_guess is not None:
        outward = best_dir_toward(my_pos, TS.enemy_core_guess)
        order = [outward] + [d for d in DIRS_8 if d != outward]
    else:
        order = list(DIRS_8)

    for d in order:
        cand = my_pos.add(d)
        if not in_map(cand.x, cand.y):
            continue
        try:
            if ct.can_spawn(cand):
                ct.spawn_builder(cand)
                self.spawned += 1
                return
        except Exception:
            continue


# --------------------------------------------------------------------------
# Builder
# --------------------------------------------------------------------------


def builder_init_role(self) -> None:
    if self.role is not None:
        return
    TS.builder_spawn_count += 1
    n = TS.builder_spawn_count
    # Distribute across all 8 directions for wider area coverage
    self.spoke_dir = DIRS_8[(n - 1) % 8]
    self.role = "pioneer"


def builder_turn(self, ct: Controller) -> None:
    builder_init_role(self)
    pos = ct.get_position()
    rnd = ct.get_current_round()

    # 1. Highest-priority: build harvester on any adjacent ore
    built = False
    for d in DIRS_8:
        check = pos.add(d)
        try:
            if ct.can_build_harvester(check):
                ct.build_harvester(check)
                built = True
                break
        except Exception:
            continue

    # 2. Early-game: seed cardinal-of-core conveyors so the chain has a
    #    place to terminate. Only fires while at least one slot is unbuilt.
    if not built and rnd < 50:
        if _try_seed_core_cardinal(ct, pos):
            built = True

    # 3. Random walk: lay road/conveyor and move
    d = random.choice(DIRS_8)
    nxt = pos.add(d)
    if not built:
        # Try a chain-connecting conveyor first; fall back to road
        if not _try_chain_conveyor(ct, pos, nxt):
            try:
                if ct.can_build_road(nxt):
                    ct.build_road(nxt)
            except Exception:
                pass
    try:
        if ct.can_move(d):
            ct.move(d)
    except Exception:
        pass


def _try_seed_core_cardinal(ct: Controller, pos: Position) -> bool:
    if TS.core_pos is None:
        return False
    if pos.distance_squared(TS.core_pos) > 5:
        return False
    for cdir in CARDINALS:
        cand = TS.core_pos.add(cdir)
        if not in_map(cand.x, cand.y):
            continue
        if cand == pos or cand.distance_squared(pos) > 2:
            continue
        try:
            if ct.get_tile_building_id(cand) is not None:
                continue
            if ct.get_tile_env(cand) != Environment.EMPTY:
                continue
            if ct.get_tile_builder_bot_id(cand) is not None:
                continue
        except Exception:
            continue
        out_dir = cdir.opposite()
        try:
            if ct.can_build_conveyor(cand, out_dir):
                ct.build_conveyor(cand, out_dir)
                return True
        except Exception:
            continue
    return False


def _try_chain_conveyor(
    ct: Controller, pos: Position, nxt: Position
) -> bool:
    """Build a conveyor at nxt only if it would output into the core or an
    existing owned conveyor. Otherwise the 3-Ti spend over a road is wasted."""
    if TS.core_pos is None:
        return False
    if not in_map(nxt.x, nxt.y):
        return False
    try:
        if ct.get_tile_building_id(nxt) is not None:
            return False
        if ct.get_tile_env(nxt) != Environment.EMPTY:
            return False
    except Exception:
        return False
    for c_out in CARDINALS:
        target = nxt.add(c_out)
        if not in_map(target.x, target.y):
            continue
        connects = target == TS.core_pos
        if not connects:
            try:
                bid = ct.get_tile_building_id(target)
                if bid is not None and ct.get_team(bid) == TS.my_team:
                    et = ct.get_entity_type(bid)
                    if et in (
                        EntityType.CONVEYOR,
                        EntityType.SPLITTER,
                        EntityType.BRIDGE,
                        EntityType.ARMOURED_CONVEYOR,
                        EntityType.FOUNDRY,
                    ):
                        connects = True
            except Exception:
                pass
        if not connects:
            continue
        try:
            if ct.can_build_conveyor(nxt, c_out):
                ct.build_conveyor(nxt, c_out)
                return True
        except Exception:
            continue
    return False



# --------------------------------------------------------------------------
# Turret combat helpers
# --------------------------------------------------------------------------


def enemy_units_in_vision(ct: Controller):
    """Return list of (unit_id, position) for visible enemy units (bots only)."""
    out = []
    try:
        ids = ct.get_nearby_units()
    except Exception:
        return out
    for uid in ids:
        try:
            if ct.get_team(uid) == TS.my_team:
                continue
            out.append((uid, ct.get_position(uid)))
        except Exception:
            continue
    return out


def enemy_buildings_in_vision(ct: Controller):
    out = []
    try:
        ids = ct.get_nearby_buildings()
    except Exception:
        return out
    for bid in ids:
        try:
            if ct.get_team(bid) == TS.my_team:
                continue
            out.append((bid, ct.get_position(bid), ct.get_entity_type(bid)))
        except Exception:
            continue
    return out


# --------------------------------------------------------------------------
# Gunner
# --------------------------------------------------------------------------


def gunner_turn(self, ct: Controller) -> None:
    ensure_core_pos(ct)
    if ct.get_action_cooldown() > 0:
        return
    try:
        ammo = ct.get_ammo_amount()
    except Exception:
        ammo = 0
    if ammo <= 0:
        return

    # Try the engine-provided line target first
    try:
        target = ct.get_gunner_target()
    except Exception:
        target = None

    if target is not None:
        try:
            if ct.can_fire(target):
                ct.fire(target)
                return
        except Exception:
            pass

    # Fallback: pick any visible enemy in line of facing direction
    try:
        attackable = ct.get_attackable_tiles()
    except Exception:
        attackable = []
    enemy_buildings = {p: et for _, p, et in enemy_buildings_in_vision(ct)}
    enemy_units = {p for _, p in enemy_units_in_vision(ct)}

    best_target = None
    best_score = -1
    for tile in attackable:
        score = 0
        if tile in enemy_units:
            score += 10
        if tile in enemy_buildings:
            et = enemy_buildings[tile]
            if et == EntityType.CORE:
                score += 100
            elif et in (EntityType.GUNNER, EntityType.SENTINEL, EntityType.BREACH):
                score += 8
            elif et == EntityType.HARVESTER:
                score += 6
            else:
                score += 2
        if score > best_score:
            best_score = score
            best_target = tile

    if best_target is not None and best_score > 0:
        try:
            if ct.can_fire(best_target):
                ct.fire(best_target)
        except Exception:
            pass


# --------------------------------------------------------------------------
# Sentinel
# --------------------------------------------------------------------------


def sentinel_turn(self, ct: Controller) -> None:
    ensure_core_pos(ct)
    if ct.get_action_cooldown() > 0:
        return
    try:
        ammo = ct.get_ammo_amount()
    except Exception:
        ammo = 0
    if ammo <= 0:
        return

    try:
        attackable = ct.get_attackable_tiles()
    except Exception:
        attackable = []
    enemies = {p for _, p in enemy_units_in_vision(ct)}
    enemy_b = {p: et for _, p, et in enemy_buildings_in_vision(ct)}

    best = None
    best_score = -1
    for tile in attackable:
        s = 0
        if tile in enemies:
            s += 10
        if tile in enemy_b:
            et = enemy_b[tile]
            if et == EntityType.CORE:
                s += 100
            elif et == EntityType.HARVESTER:
                s += 6
            elif et in (EntityType.GUNNER, EntityType.SENTINEL, EntityType.BREACH):
                s += 8
            else:
                s += 2
        if s > best_score:
            best_score = s
            best = tile

    if best is not None and best_score > 0:
        try:
            if ct.can_fire(best):
                ct.fire(best)
        except Exception:
            pass


# --------------------------------------------------------------------------
# Breach
# --------------------------------------------------------------------------


def breach_turn(self, ct: Controller) -> None:
    ensure_core_pos(ct)
    if ct.get_action_cooldown() > 0:
        return
    try:
        ammo = ct.get_ammo_amount()
    except Exception:
        ammo = 0
    if ammo <= 0:
        return

    try:
        attackable = ct.get_attackable_tiles()
    except Exception:
        attackable = []
    enemy_units = {p for _, p in enemy_units_in_vision(ct)}
    enemy_b = {p: et for _, p, et in enemy_buildings_in_vision(ct)}

    # Pick the tile whose splash hits the most enemy stuff
    best = None
    best_score = -1
    for tile in attackable:
        s = 0
        if tile in enemy_units:
            s += 5
        if tile in enemy_b:
            et = enemy_b[tile]
            s += 100 if et == EntityType.CORE else 5
        for d in DIRS_8:
            adj = tile.add(d)
            if adj in enemy_units:
                s += 2
            if adj in enemy_b:
                s += 2
        if s > best_score:
            best_score = s
            best = tile

    if best is not None and best_score > 0:
        try:
            if ct.can_fire(best):
                ct.fire(best)
        except Exception:
            pass


# --------------------------------------------------------------------------
# Launcher
# --------------------------------------------------------------------------


def launcher_turn(self, ct: Controller) -> None:
    ensure_core_pos(ct)
    if ct.get_action_cooldown() > 0:
        return

    my_pos = ct.get_position()
    enemy_team = TS.enemy_team

    # Find adjacent bots (within action radius squared 2)
    enemy_bot_pos = None
    ally_bot_pos = None
    try:
        for uid in ct.get_nearby_units(2):
            if ct.get_entity_type(uid) != EntityType.BUILDER_BOT:
                continue
            upos = ct.get_position(uid)
            if ct.get_team(uid) == enemy_team:
                if enemy_bot_pos is None:
                    enemy_bot_pos = upos
            else:
                if ally_bot_pos is None:
                    ally_bot_pos = upos
    except Exception:
        return

    # Hostile launch: throw enemy bot away from our core
    if enemy_bot_pos is not None:
        target = pick_throw_target(ct, my_pos, hostile=True)
        if target is not None:
            try:
                if ct.can_launch(enemy_bot_pos, target):
                    ct.launch(enemy_bot_pos, target)
                    return
            except Exception:
                pass

    # Supportive launch: throw ally bot toward enemy concentration
    if ally_bot_pos is not None:
        # Only worth it if we see enemy infrastructure near
        try:
            seen_enemy = False
            for bid in ct.get_nearby_buildings():
                if ct.get_team(bid) == enemy_team:
                    seen_enemy = True
                    break
        except Exception:
            seen_enemy = False
        if not seen_enemy:
            return
        target = pick_throw_target(ct, my_pos, hostile=False)
        if target is not None:
            try:
                if ct.can_launch(ally_bot_pos, target):
                    ct.launch(ally_bot_pos, target)
            except Exception:
                pass


def pick_throw_target(ct: Controller, my_pos: Position, hostile: bool):
    """Pick a target tile within launcher vision.
    hostile=True: throw far from core (away from us).
    hostile=False: throw toward enemy core / cluster."""
    if TS.core_pos is None:
        return None
    core = TS.core_pos
    enemy_core = TS.enemy_core_guess

    try:
        tiles = ct.get_nearby_tiles()
    except Exception:
        return None

    best = None
    best_score = -1 << 30
    deadline_check = 0
    for tile in tiles:
        deadline_check += 1
        if deadline_check & 31 == 0 and not time_left(ct):
            break
        try:
            if not ct.is_tile_passable(tile):
                continue
        except Exception:
            continue
        if hostile:
            # Far from our core; if we know enemy core, prefer tiles near it
            score = tile.distance_squared(core)
            if enemy_core is not None:
                score -= tile.distance_squared(enemy_core) // 2
        else:
            # Toward enemy infrastructure
            if enemy_core is not None:
                score = -tile.distance_squared(enemy_core)
            else:
                score = -tile.distance_squared(my_pos)

        if score > best_score:
            best_score = score
            best = tile
    return best


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


class Player:
    def __init__(self):
        self.kind = None
        self.spawn_round = -1
        self.role = None
        self.spoke_dir = None
        self.spawned = 0  # core: number we've spawned

    def run(self, ct: Controller) -> None:
        try:
            if not TS.initialized:
                first_init(ct)
            if self.spawn_round < 0:
                try:
                    self.spawn_round = ct.get_current_round()
                except Exception:
                    self.spawn_round = 0
            if self.kind is None:
                try:
                    self.kind = ct.get_entity_type()
                except Exception:
                    return

            kind = self.kind
            if kind == EntityType.CORE:
                core_turn(self, ct)
            elif kind == EntityType.BUILDER_BOT:
                builder_turn(self, ct)
            elif kind == EntityType.GUNNER:
                gunner_turn(self, ct)
            elif kind == EntityType.SENTINEL:
                sentinel_turn(self, ct)
            elif kind == EntityType.BREACH:
                breach_turn(self, ct)
            elif kind == EntityType.LAUNCHER:
                launcher_turn(self, ct)
        except Exception:
            try:
                sys.stderr.write(traceback.format_exc())
                sys.stderr.flush()
            except Exception:
                pass

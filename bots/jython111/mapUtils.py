from typing import Iterable

from cambc import Controller, Direction, EntityType, Environment, Position

from unit import Unit
from data import BARRIER_AND_WALKABLE_ENTITIES, WALKABLE_ENTITIES, DIRECTIONS

_breakBarriers = True

def enableBreakBarriers():
    global _breakBarriers
    _breakBarriers = True

def disableBreakBarriers():
    global _breakBarriers
    _breakBarriers = False

# Cached map dimensions (set once on first call to onTheMap)
_mapW = 0
_mapH = 0

def onTheMap(ct: Controller, pos) -> bool:
    global _mapW, _mapH
    if _mapW == 0:
        _mapW = ct.get_map_width()
        _mapH = ct.get_map_height()
    if pos.x < 0 or pos.y < 0 or pos.x >= _mapW or pos.y >= _mapH:
        return False
    return True

def isPassable(ct: Controller, pos: Position) -> bool:
    if not onTheMap(ct, pos):
        return False
    if not ct.is_in_vision(pos):
        return False
    botId = ct.get_tile_builder_bot_id(pos)
    if botId is not None and ct.get_team(botId) != ct.get_team():
        return False
    buildingId = ct.get_tile_building_id(pos)
    if buildingId is not None:
        if ct.get_team(buildingId) != ct.get_team() and ct.get_entity_type(buildingId) == EntityType.CORE:
            return False
    return ct.get_tile_env(pos) == Environment.EMPTY

def isPassableDirection(ct: Controller, dir: Direction) -> bool:
    return isPassable(ct, ct.get_position().add(dir))

def isPassableDirectionFrom(ct: Controller, dir: Direction, start: Position) -> bool:
    return isPassable(ct, start.add(dir))

def isMoveable(ct: Controller, pos: Position) -> bool:
    global _breakBarriers
    # Check passability first (cheap) before the expensive launcher scan
    if not onTheMap(ct, pos):
        return False
    if not ct.is_in_vision(pos):
        if pos in Unit.symmetry.walls:
            return False
        elif pos in Unit.symmetry.empties or pos in Unit.symmetry.oresA or pos in Unit.symmetry.oresT:
            return True
        return True
    if ct.get_tile_env(pos) != Environment.EMPTY:
        return False

    botId = ct.get_tile_builder_bot_id(pos)
    if botId is not None and ct.get_team(botId) == ct.get_team():
        return False

    buildingId = ct.get_tile_building_id(pos)
    if buildingId is not None:
        buildingTeam = ct.get_team(buildingId)
        buildingType = ct.get_entity_type(buildingId)
        if buildingTeam != ct.get_team() and buildingType in (EntityType.CORE, EntityType.BARRIER):
            return False
        if buildingType not in (BARRIER_AND_WALKABLE_ENTITIES if _breakBarriers else WALKABLE_ENTITIES):
            return False
    else:
        if ct.get_global_resources()[0] < ct.get_road_cost()[0]:
            return False

    # Don't move next to enemy launchers or the enemy core
    for d in DIRECTIONS:
        buildingPos = pos.add(d)

        if not onTheMap(ct, buildingPos) or not ct.is_in_vision(buildingPos):
            continue

        adjId = ct.get_tile_building_id(buildingPos)

        if adjId is not None and ct.get_team(adjId) != ct.get_team():
            if ct.get_entity_type(adjId) == EntityType.LAUNCHER:
                return False
            if ct.get_entity_type(adjId) == EntityType.CORE and ct.get_team(buildingId) == ct.get_team():
                return False

    return True

def isMoveableDirection(ct: Controller, dir: Direction) -> bool:
    return isMoveable(ct, ct.get_position().add(dir))

def chevyBetween(start: Position, target: Position) -> Direction:
    dx = target.x - start.x
    dy = target.y - start.y

    if dx == 0:
        return Direction.SOUTH if dy > 0 else Direction.NORTH
    if dy == 0:
        return Direction.EAST if dx > 0 else Direction.WEST

    if dx > 0:
        return Direction.SOUTHEAST if dy > 0 else Direction.NORTHEAST
    else:
        return Direction.SOUTHWEST if dy > 0 else Direction.NORTHWEST

def cardinalBetween(start: Position, target: Position) -> Direction:
    dx = target.x - start.x
    dy = target.y - start.y
    if abs(dx) > abs(dy):
        return Direction.EAST if dx > 0 else Direction.WEST
    else:
        return Direction.SOUTH if dy > 0 else Direction.NORTH

def cardinalBetweenCross(start: Position, target: Position) -> Direction:
    dx = target.x - start.x
    dy = target.y - start.y
    if abs(dy) > abs(dx):
        return Direction.SOUTH if dy > 0 else Direction.NORTH
    else:
        return Direction.EAST if dx > 0 else Direction.WEST

def findCardinalBetween(ct: Controller, start: Position, target: Position, invalid: callable = (lambda *x: not isPassableDirectionFrom(*x))) -> Direction:
    initialDir = cardinalBetween(start, target)

    dir = initialDir

    if invalid(ct, dir, start):
        dir = cardinalBetweenCross(start, target)
        
        if invalid(ct, dir, start):
            left = initialDir.rotate_left().rotate_left()
            right = left.opposite()

            if (start.add(left).distance_squared(target) < start.add(right).distance_squared(target)):
                dir = left

                if invalid(ct, dir, start): 
                    dir = right
            else:
                dir = right

                if invalid(ct, dir, start): 
                    dir = left

            if invalid(ct, dir, start):
                dir = initialDir.opposite()

    return dir

def chebyshevDistance(start: Position, end: Position) -> int:
    return max(abs(start.x - end.x), abs(start.y - end.y))

def manhattanDistance(start: Position, end: Position) -> int:
    return abs(start.x - end.x) + abs(start.y - end.y)

def getConveyorTarget(ct: Controller, conveyorId: int) -> Position:
    conveyorType = ct.get_entity_type(conveyorId) 
    if conveyorType in (EntityType.CONVEYOR, EntityType.ARMOURED_CONVEYOR):
        return ct.get_position(conveyorId).add(ct.get_direction(conveyorId))
    elif conveyorType == EntityType.BRIDGE:
        return ct.get_bridge_target(conveyorId)
    elif conveyorType == EntityType.SPLITTER:
        # We're just gonna make a crude assumption here that might be wrong
        return ct.get_position(conveyorId).add(ct.get_direction(conveyorId))
    return None

def sortPositions(base: Position, positions: Iterable[Position], reverse: bool = False) -> list[Position]:
    return sorted(positions, key=lambda p: base.distance_squared(p), reverse=reverse)

def sortIds(ct: Controller, base: Position, ids: Iterable[int], reverse: bool = False) -> list[Position]:
    return sorted(ids, key=lambda i: base.distance_squared(ct.get_position(i)), reverse=reverse)

def filterEnvironment(ct: Controller, env: Environment, positions: Iterable[Position]) -> list[Position]:
    return filter(lambda p: ct.get_tile_env(p) == env, positions)
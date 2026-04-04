from cambc import Controller, Direction, EntityType, Position
from enum import Enum

DEBUG = True

INF = 1_000_000

class SymmetryType(Enum):
    VERTICAL = "v"
    HORIZONTAL = "h"
    ROTATIONAL = "r"

    def apply(self, ct: Controller, p: Position):
        if self.value == "v":
            return Position(ct.get_map_width() - p.x - 1, p.y)
        elif self.value == "h":
            return Position(p.x, ct.get_map_height() - p.y - 1)
        else:
            return Position(ct.get_map_width() - p.x - 1, ct.get_map_height() - p.y - 1)
        
    def __call__(self, ct: Controller, pos: Position):
        return self.apply(ct, pos)

ALL_DIRECTIONS = (
    Direction.CENTRE,
    Direction.NORTH,
    Direction.SOUTH,
    Direction.EAST,
    Direction.WEST,
    Direction.NORTHEAST,
    Direction.SOUTHWEST,
    Direction.SOUTHEAST,
    Direction.NORTHWEST
)

DIRECTIONS = (
    Direction.NORTH,
    Direction.SOUTH,
    Direction.EAST,
    Direction.WEST,
    Direction.NORTHEAST,
    Direction.SOUTHWEST,
    Direction.SOUTHEAST,
    Direction.NORTHWEST
)

DIRECTION_CENTER = Direction.CENTRE

DIRECTION_TO_INDEX = {d: i for i, d in enumerate(DIRECTIONS)}

CARDINAL_DIRECTIONS = (
    Direction.NORTH,
    Direction.SOUTH,
    Direction.EAST,
    Direction.WEST
)

CARDINAL_AND_CENTER_DIRECTIONS = (
    Direction.NORTH,
    Direction.SOUTH,
    Direction.EAST,
    Direction.WEST,
    DIRECTION_CENTER
)

DIAGONAL_DIRECTIONS = (
    Direction.NORTHEAST,
    Direction.SOUTHWEST,
    Direction.SOUTHEAST,
    Direction.NORTHWEST
)

WALKABLE_ENTITIES = (
    EntityType.ROAD,
    EntityType.CORE,
    EntityType.CONVEYOR,
    EntityType.ARMOURED_CONVEYOR,
    EntityType.SPLITTER,
    EntityType.BRIDGE,
    EntityType.MARKER
)

BARRIER_AND_WALKABLE_ENTITIES = (
    EntityType.BARRIER,
    EntityType.ROAD,
    EntityType.CORE,
    EntityType.CONVEYOR,
    EntityType.ARMOURED_CONVEYOR,
    EntityType.SPLITTER,
    EntityType.BRIDGE,
    EntityType.MARKER
)

ENEMY_WALKABLE_ENTITIES = (
    EntityType.ROAD,
    EntityType.CONVEYOR,
    EntityType.ARMOURED_CONVEYOR,
    EntityType.SPLITTER,
    EntityType.BRIDGE,
    EntityType.MARKER
)

CONVEYOR_TYPES = (
    EntityType.CONVEYOR,
    EntityType.ARMOURED_CONVEYOR,
    EntityType.SPLITTER,
    EntityType.BRIDGE
)

SOURCE_TYPES = (
    EntityType.CONVEYOR,
    EntityType.ARMOURED_CONVEYOR,
    EntityType.SPLITTER,
    EntityType.BRIDGE,
    EntityType.HARVESTER
)

DIRECTIONAL_CONVEYOR_TYPES = (
    EntityType.CONVEYOR,
    EntityType.ARMOURED_CONVEYOR,
    EntityType.SPLITTER
)

TURRET_TYPES = (
    EntityType.GUNNER,
    EntityType.SENTINEL,
    EntityType.BREACH,
    EntityType.LAUNCHER
)

DIRECTIONAL_TURRET_TYPES = (
    EntityType.GUNNER,
    EntityType.SENTINEL,
    EntityType.BREACH
)
from cambc import *

DIRECTIONS = [
    Direction.EAST,
    Direction.NORTH,
    Direction.NORTHEAST,
    Direction.NORTHWEST,
    Direction.SOUTH,
    Direction.WEST,
    Direction.SOUTHWEST,
    Direction.SOUTHEAST,
]
CARDINAL_DIRECTIONS = (Direction.NORTH, Direction.SOUTH, Direction.EAST, Direction.WEST)
CONVEYORS = [
    EntityType.ARMOURED_CONVEYOR,
    EntityType.CONVEYOR,
    EntityType.BRIDGE,
    EntityType.SPLITTER,
]

WALKABLE = CONVEYORS + [EntityType.ROAD]
TURRETS = [
    EntityType.GUNNER,
    EntityType.SENTINEL,
    EntityType.BREACH,
    EntityType.LAUNCHER,
]

# utils/constants.py
from cambc import *

class Constants:
    DIRECTIONS = [d for d in Direction if d != Direction.CENTRE]
    CARDINALS = [Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST]
    TURRETS = [EntityType.LAUNCHER, EntityType.SENTINEL, EntityType.BREACH, EntityType.GUNNER]
    TRANSPORT_ROUTING = [EntityType.BRIDGE, EntityType.CONVEYOR, EntityType.SPLITTER,EntityType.ARMOURED_CONVEYOR]
    ROUTING = [EntityType.HARVESTER,EntityType.CORE,EntityType.FOUNDRY] + TRANSPORT_ROUTING
    ROUTE_TITANIUM_SPLITTER_CHANCE = 1
    SCOUT_MAX_TIME = 30
    maxSurrounding = 2
    CONVEYOR_PREFERENCE_CHANCE = 0.9  # % chance to prefer a conveyor step over a bridge
    GOAXIONITE = 50
    DEFENSE_BUILDING = False
    ORE_BORDER = False
    LATE_GAME_ATTACK_TICK = 1000

    class states:
        SCOUT = 0
        MAINTEINANCE = 1
        ROUTE_CONVEYOR = 2
        BUM = 3
        BUILD_FOUNDRY = 4
        ATTACK = 5
        BUILD_SPLITTER = 6
    class tiles:
        UNKNOWN = 0
        EMPTY = 1
        WALL = 2
        ORE_TITANIUM = 3
        ORE_AXIONITE = 4

    @staticmethod
    def init():
        pass
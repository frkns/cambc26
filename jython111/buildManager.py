from cambc import Controller, Direction, Position, EntityType, Environment

from destroyManager import tryDestroy
from unit import Unit
from mapUtils import onTheMap, findCardinalBetween
from data import CARDINAL_DIRECTIONS, CONVEYOR_TYPES, TURRET_TYPES

def enoughResources(g, c):
    return g[0] >= c[0] and g[1] >= c[1]

def tryPlaceMarker(ct: Controller, position:
                    Position, value: int) -> bool:
    buildingId = ct.get_tile_building_id(position)
    if buildingId is not None and ct.get_team(buildingId) == ct.get_team() and ct.get_entity_type(buildingId) == EntityType.MARKER and ct.get_marker_value(buildingId) == value:
        return False
    if ct.can_place_marker(position):
        print(f"Placed a marker at {position}")
        ct.place_marker(position, value)
        return True
    return False

def tryBuildRoad(ct: Controller, position: Position, movingInto: bool = True) -> bool:
    if ct.get_action_cooldown() > 0 or not enoughResources(ct.get_global_resources(), ct.get_road_cost()):
        return False

    if ct.get_tile_env(position) != Environment.EMPTY:
        return False

    buildingId = ct.get_tile_building_id(position)

    if buildingId is not None:
        entityType = ct.get_entity_type(buildingId)
        if entityType == EntityType.MARKER:
            buildingId = None
        else:
            if (ct.get_team(buildingId) != ct.get_team()):
                return False
            elif entityType != EntityType.BARRIER:
                return False

    # Try to repair conveyor paths
    sourceDir = None
    needsTarget = True
    hasTarget = False
    adjacentOre = False
    adjacentCore = False
    targetDir = findCardinalBetween(ct, position, Unit.corePosition)
    for d in CARDINAL_DIRECTIONS:
        sourcePosition = position.add(d)
        if not onTheMap(ct, sourcePosition) or not ct.is_in_vision(sourcePosition):
            continue

        if ct.get_tile_env(sourcePosition) in (Environment.ORE_TITANIUM, Environment.ORE_AXIONITE):
            adjacentOre = True

        if ct.get_tile_builder_bot_id(sourcePosition) is not None:
            continue

        sourcePositionId = ct.get_tile_building_id(sourcePosition)
        if (sourcePositionId is not None):
            sourceType = ct.get_entity_type(sourcePositionId)
            if sourceType in [EntityType.CONVEYOR, EntityType.ARMOURED_CONVEYOR]:
                if ct.get_direction(sourcePositionId).opposite() == d:
                    sourceDir = d
                    needsTarget = False
                else:
                    targetDir = d
                    hasTarget = True
            elif sourceType == EntityType.HARVESTER:
                sourceDir = d
            elif sourceType == EntityType.CORE and ct.get_team(sourcePositionId) != ct.get_team():
                adjacentCore = True

    if sourceDir is not None and (not needsTarget or hasTarget) and not Unit.connecting:
        return tryBuildConveyor(ct, position, targetDir)
        
    if (adjacentCore) and not movingInto:
        return tryBuildBarrier(ct, position)
    
    if buildingId is not None:
        tryDestroy(ct, position)

    if ct.can_build_road(position):
        print(f"Built a road at {position}")
        ct.build_road(position)
        return True
    return False

def tryBuildBarrier(ct: Controller, position: Position) -> bool:
    if ct.get_action_cooldown() > 0 or not enoughResources(ct.get_global_resources(), ct.get_barrier_cost()):
        return False
    if ct.get_entity_type(ct.get_tile_building_id(position)) != EntityType.BARRIER:
        tryDestroy(ct, position)
    if ct.can_build_barrier(position):
        print(f"Built a barrier at {position}")
        ct.build_barrier(position)
        return True
    return False

def tryBuildHarvester(ct: Controller, position: Position) -> bool:
    if ct.get_action_cooldown() > 0 or not enoughResources(ct.get_global_resources(), ct.get_harvester_cost()):
        return False
    if ct.get_tile_env(position) not in [Environment.ORE_TITANIUM, Environment.ORE_AXIONITE]:
        return False
    if position == ct.get_position():
        return False
    tryDestroy(ct, position)
    if ct.can_build_harvester(position):
        print(f"Built a harvester at {position}")
        ct.build_harvester(position)
        return True
    return False

def tryBuildBreach(ct: Controller, position: Position, direction: Direction) -> bool:
    if ct.get_action_cooldown() > 0 or not enoughResources(ct.get_global_resources(), ct.get_breach_cost()):
        return False
    if position == ct.get_position():
        return False
    
    if ct.get_tile_builder_bot_id(position) is not None:
        return False

    bid = ct.get_tile_building_id(position)
    btype = ct.get_entity_type(bid)
    if btype in CONVEYOR_TYPES:
        return False
    if btype == EntityType.BREACH:
        return False
    if btype == EntityType.HARVESTER:
        return False

    tryDestroy(ct, position)
    if ct.can_build_breach(position, direction):
        print(f"Built a breach at {position}")
        ct.build_breach(position, direction)
        return True
    return False

def tryBuildSentinel(ct: Controller, position: Position, direction: Direction) -> bool:
    if ct.get_action_cooldown() > 0 or not enoughResources(ct.get_global_resources(), ct.get_sentinel_cost()):
        return False
    if position == ct.get_position():
        return False
    
    if ct.get_tile_builder_bot_id(position) is not None:
        return False

    bid = ct.get_tile_building_id(position)
    btype = ct.get_entity_type(bid)
    if btype in CONVEYOR_TYPES:
        return False
    if btype == EntityType.SENTINEL:
        return False
    if btype == EntityType.HARVESTER:
        return False

    tryDestroy(ct, position)
    if ct.can_build_sentinel(position, direction):
        print(f"Built a sentinel at {position}")
        ct.build_sentinel(position, direction)
        return True
    return False

def tryBuildGunner(ct: Controller, position: Position, direction: Direction) -> bool:
    if ct.get_action_cooldown() > 0 or not enoughResources(ct.get_global_resources(), ct.get_gunner_cost()):
        return False
    if position == ct.get_position():
        return False
    
    if ct.get_tile_builder_bot_id(position) is not None:
        return False

    bid = ct.get_tile_building_id(position)
    btype = ct.get_entity_type(bid)
    if btype in CONVEYOR_TYPES and ct.get_team(bid) == ct.get_team():
        return False
    if btype in TURRET_TYPES:
        return False
    if btype == EntityType.HARVESTER:
        return False

    tryDestroy(ct, position)
    if ct.can_build_gunner(position, direction):
        print(f"Built a gunner at {position}")
        ct.build_gunner(position, direction)
        return True
    return False

def tryBuildLauncher(ct: Controller, position: Position) -> bool:
    if ct.get_action_cooldown() > 0 or not enoughResources(ct.get_global_resources(), ct.get_launcher_cost()):
        return False
    if position == ct.get_position():
        return False
    
    if ct.get_tile_builder_bot_id(position) is not None:
        return False

    bid = ct.get_tile_building_id(position)
    btype = ct.get_entity_type(bid)
    if btype in CONVEYOR_TYPES and ct.get_team(bid) == ct.get_team():
        return False
    if btype == EntityType.LAUNCHER:
        return False
    if btype == EntityType.HARVESTER:
        return False

    tryDestroy(ct, position)
    if ct.can_build_launcher(position):
        print(f"Built a launcher at {position}")
        ct.build_launcher(position)
        return True
    return False

def tryBuildConveyor(ct: Controller, position: Position, direction: Direction) -> bool:
    if ct.get_action_cooldown() > 0 or not enoughResources(ct.get_global_resources(), ct.get_conveyor_cost()) or direction not in CARDINAL_DIRECTIONS:
        return False
    # Make sure we're actually changing something when we build again
    bid = ct.get_tile_building_id(position)
    btype = ct.get_entity_type(bid)
    if btype in (EntityType.CONVEYOR, EntityType.ARMOURED_CONVEYOR, EntityType.SPLITTER) and ct.get_direction(bid) != direction:
        tryDestroy(ct, position)

    if btype in (EntityType.ROAD, EntityType.BARRIER):
        tryDestroy(ct, position)

    if ct.can_build_conveyor(position, direction):
        ct.build_conveyor(position, direction)
        print(f"Built a conveyor at {position}")
        Unit.roundsSinceBuild = 0
        return True
    return False

def tryBuildSplitter(ct: Controller, position: Position, direction: Direction) -> bool:
    if ct.get_action_cooldown() > 0 or not enoughResources(ct.get_global_resources(), ct.get_splitter_cost()) or direction not in CARDINAL_DIRECTIONS:
        return False
    # Make sure we're actually changing something when we build again
    bid = ct.get_tile_building_id(position)
    if ct.get_entity_type(bid) != EntityType.SPLITTER or ct.get_direction(bid) != direction:
        tryDestroy(ct, position)
    if ct.can_build_splitter(position, direction):
        ct.build_splitter(position, direction)
        print(f"Built a splitter at {position}")
        Unit.roundsSinceBuild = 0
        return True
    return False

def tryBuildBridge(ct: Controller, position: Position, target: Position) -> bool:
    if ct.get_action_cooldown() > 0 or not enoughResources(ct.get_global_resources(), ct.get_bridge_cost()):
        return False
    # Make sure we're actually changing something when we build again
    bid = ct.get_tile_building_id(position)
    if ct.get_entity_type(bid) != EntityType.BRIDGE or ct.get_bridge_target(bid) != target:
        tryDestroy(ct, position)
    if ct.can_build_bridge(position, target):
        print(f"Built a bridge at {position}")
        ct.build_bridge(position, target)
        Unit.roundsSinceBuild = 0
        return True
    return False

def tryBuildFoundry(ct: Controller, position: Position) -> bool:
    if ct.get_action_cooldown() > 0 or not enoughResources(ct.get_global_resources(), ct.get_foundry_cost()):
        return False
    # Make sure we're actually changing something when we build again
    bid = ct.get_tile_building_id(position)
    if ct.get_entity_type(bid) != EntityType.FOUNDRY or ct.get_team(bid) != ct.get_team():
        tryDestroy(ct, position)
    if ct.can_build_foundry(position):
        print(f"Built a foundry at {position}")
        ct.build_foundry(position)
        return True
    return False
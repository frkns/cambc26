#builder_routing.py
from cambc import *
from utils.constants import Constants


def shouldRoute(ct, tile):
    from builder import Builder
    if not Builder.nav.onMap(tile):
        return False
    if Builder.nav.getTile(tile) in [Constants.tiles.ORE_TITANIUM, Constants.tiles.ORE_AXIONITE, Constants.tiles.WALL]:
        return False
    theTileBuilding = Builder.nav.buildMap[tile.y * ct.get_map_width() + tile.x]
    if theTileBuilding != 0 and not theTileBuilding.is_passable() and theTileBuilding.entityType not in [EntityType.BARRIER,EntityType.FOUNDRY]:
        return False
    if theTileBuilding != 0 and theTileBuilding.team != ct.get_team():
        if not theTileBuilding.is_passable():
            return False
    if tile in Builder.nav.DA_SPLITTER and Builder.nearestNode != tile:
        return False
    if tile in Builder.nav.FOUNDRIES and Builder.nearestNode != tile:
        return False
    if tile in Builder.nav.NOROUTE and Builder.nearestNode != tile:
        return False
    if theTileBuilding != 0 and theTileBuilding.entityType == EntityType.LAUNCHER:
        return False
    if theTileBuilding != 0:
        if theTileBuilding.entityType == EntityType.CORE and tile != Builder.nearestNode:
            return False
        if Builder.uniqueRoute:
            if theTileBuilding.entityType == EntityType.SPLITTER and Builder.nearestNode == tile:
                return True
            if Builder.nearestNode == tile and theTileBuilding.entityType in [EntityType.CONVEYOR,EntityType.ARMOURED_CONVEYOR]:
                return True
            if theTileBuilding.entityType == EntityType.BARRIER:
                if Builder.nearestNode == tile:
                    return True
                else:
                    return False
            if theTileBuilding.entityType in Constants.ROUTING and (tile != Builder.routeFrom and tile != Builder.nearestNode):
                return False
    return True


def get_best_intermediate_pos(routeFrom, nearestNode, ct):
    from builder import Builder
    current_dist_to_node = routeFrom.distance_squared(nearestNode)

    hash_val = (routeFrom.x * 73856093 ^ routeFrom.y * 19349663 ^
                nearestNode.x * 83492791 ^ nearestNode.y * 31415927)
    pseudo_random = (hash_val & 0x7FFFFFFF) / 0x7FFFFFFF

    best_adjacent = None
    min_adj_dist = float('inf')

    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        check_pos = Position(routeFrom.x + dx, routeFrom.y + dy)
        if not shouldRoute(ct, check_pos):
            continue
        dist = check_pos.distance_squared(nearestNode)
        if dist < min_adj_dist:
            min_adj_dist = dist
            best_adjacent = check_pos

    if (best_adjacent is not None
            and min_adj_dist < current_dist_to_node
            and pseudo_random < Constants.CONVEYOR_PREFERENCE_CHANCE):
        return best_adjacent

    best_pos = routeFrom
    min_dist_to_target = float('inf')

    for dx in range(-3, 4):
        for dy in range(-3, 4):
            if dx * dx + dy * dy > 9:
                continue
            check_pos = Position(routeFrom.x + dx, routeFrom.y + dy)
            if check_pos == routeFrom:
                continue
            if not shouldRoute(ct, check_pos):
                continue
            dist_to_node = check_pos.distance_squared(nearestNode)
            if dist_to_node < min_dist_to_target:
                min_dist_to_target = dist_to_node
                best_pos = check_pos
    if ct.is_in_vision(nearestNode) and not shouldRoute(ct,nearestNode):
        print("BAADDDDD ROUTE")
        print("Yo at this tile there is",Builder.nav.getTile(Builder.routeFrom),"building",Builder.nav.getBuilding(Builder.routeFrom))
        return routeFrom

    return best_pos


def count_splitter_inputs(ct, splitter_pos):
    from builder import Builder
    count = 0

    for d in Constants.CARDINALS:
        neighbor = splitter_pos.add(d)
        if not Builder.nav.onMap(neighbor):
            continue
        building = Builder.nav.getBuilding(neighbor)
        if (building != 0
                and building.entityType in [EntityType.CONVEYOR,EntityType.ARMOURED_CONVEYOR]
                and building.direction == neighbor.direction_to(splitter_pos)):
            count += 1

    for dx in range(-3, 4):
        for dy in range(-3, 4):
            if dx * dx + dy * dy > 9:
                continue
            check_pos = Position(splitter_pos.x + dx, splitter_pos.y + dy)
            if not Builder.nav.onMap(check_pos):
                continue
            building = Builder.nav.buildMap[check_pos.y * ct.get_map_width() + check_pos.x]
            if (building != 0
                    and building.entityType == EntityType.BRIDGE
                    and building.target == splitter_pos):
                count += 1

    return count
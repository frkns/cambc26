#builder_ore.py
from cambc import *
from utils.constants import Constants
from builder_routing import shouldRoute, count_splitter_inputs

def goNearestOre(currLoc, tile, nearestOreDist, ct, building=None):
    from builder import Builder
    currentEntity = None
    if building != None:
        currentEntity = building.entityType

    _ore_dict = Builder.nav.axioniteOres if Builder.nav.getTile(tile) == Constants.tiles.ORE_AXIONITE else Builder.nav.titaniumOres
    _ore_key = (tile.x, tile.y)
    if currentEntity == EntityType.HARVESTER and building.team == ct.get_team():
        _ore_dict[_ore_key] = 'R'
    elif building is not None and building.team != ct.get_team():
        _ore_dict[_ore_key] = 'X'
    else:
        _ore_dict[_ore_key] = 'A'

    if nearestOreDist == -1: #continue
        return -1
    dist = currLoc.distance_squared(tile)
    """
    if Builder.mode == 0 and Builder.isAttackRoute == False:
        if Builder.nav.getTile(tile) == Constants.tiles.ORE_TITANIUM and ct.can_build_barrier(tile) and ct.get_global_resources()[0] > ct.get_bridge_cost()[0]*3:
            ct.build_barrier(tile)
        return nearestOreDist
    """
    if Builder.mode == 0 and Builder.isAttackRoute == False:
        return nearestOreDist
    if Builder.state in [Constants.states.ROUTE_CONVEYOR, Constants.states.MAINTEINANCE, Constants.states.BUILD_FOUNDRY,Constants.states.BUILD_SPLITTER]:
        return nearestOreDist
    if Builder.nav.getTile(tile) == Constants.tiles.ORE_AXIONITE and ct.get_current_round()<Constants.GOAXIONITE:
        return nearestOreDist
    #print("Analyzing ore at",tile,"dist:",dist,"currentclosest dist:",nearestOreDist,"currentEntity:",currentEntity,"can build harvester:",Builder.canBuildHarvester,"harvesterticks:",Builder._canBuildHarvesterTicks)
    if currentEntity != None and currentEntity == EntityType.HARVESTER and building.team == ct.get_team():
        #most likely already routed. dw
        return leave(tile,nearestOreDist,ct)
    
    if currentEntity != None and currentEntity == EntityType.HARVESTER and building.team != ct.get_team():
        if dist < nearestOreDist and dist < 9:
            available = 0
            closestAvailableDist = 999999
            closestAvailable = None
            connected = False
            hasSentinel = False
            coolTarg = None
            for d in Constants.CARDINALS:
                checkLoc = tile.add(d)
                if(not Builder.nav.onMap(checkLoc)):
                    continue
                newD = checkLoc.distance_squared(currLoc)
                #Builder.updateTile(ct,checkLoc,currLoc,None)
                newB = Builder.nav.getBuilding(checkLoc)
                print("Checking building at",checkLoc,"b",newB)
                if(newB != 0):
                    print(newB.entityType)
                if newB != 0 and newB.team != ct.get_team():
                    coolTarg = checkLoc
                if(newB != 0) and newB.team == ct.get_team():
                    if newB.entityType in Constants.TRANSPORT_ROUTING:
                        connected = True
                        #break
                    elif newB.entityType in Constants.TURRETS:
                        hasSentinel = True
                elif (newB == 0 or shouldRoute(ct, checkLoc)):
                        available += 1
                        if closestAvailable == None or (newD < closestAvailableDist):
                            closestAvailableDist = newD
                            closestAvailable = checkLoc
            if not hasSentinel and available > 0 and closestAvailable and Builder.nav.getTile(tile) == Constants.tiles.ORE_TITANIUM:
                Builder.state = Constants.states.ATTACK
                Builder.persistentTarget = closestAvailable
                Builder.sentinelTargPos = coolTarg
                print("Plan on attacking",Builder.persistentTarget,"Possible dir towards",coolTarg)
                return dist
            else:
                print("NOT going here bro")
                return leave(tile,nearestOreDist,ct)
            """
            if(connected or available == 0):
                if available == 0 and not connected:
                    _ore_dict[_ore_key] = 'X'
                return leave(tile,nearestOreDist,ct)
            doRoute(closestAvailable, tile, ct)
            """
            return nearestOreDist
        else:
            return nearestOreDist
    if building != None and building.team != ct.get_team():
        return leave(tile,nearestOreDist,ct)
    
    numBots = 0
    for d in Constants.DIRECTIONS:
        newLoc = tile.add(d)
        if Builder.nav.onMap(newLoc) and Builder.nav.getBot(newLoc) != 0:
            numBots += 1
    if numBots > Constants.maxSurrounding:
        return leave(tile,nearestOreDist,ct)

    if Builder.nav.getTile(tile) == Constants.tiles.ORE_AXIONITE:
        nearestOreDist = dist
        Builder.targLoc = tile
        if(currLoc == tile):
            currLoc = Builder.nav.moveRandomly()
            Builder.targLoc = currLoc
        elif currLoc.distance_squared(tile) <= GameConstants.ACTION_RADIUS_SQ:
            Builder.targLoc = currLoc
    elif nearestOreDist is None or dist < nearestOreDist:
        Builder.targLoc = tile
        nearestOreDist = dist
        if(currLoc == tile):
            currLoc = Builder.nav.moveRandomly()
            Builder.targLoc = currLoc
        elif currLoc.distance_squared(tile) <= GameConstants.ACTION_RADIUS_SQ:
            Builder.targLoc = currLoc

    if dist <= GameConstants.ACTION_RADIUS_SQ:
        if Builder.canBuildHarvester and currentEntity is not None and ct.can_destroy(tile):
            ct.destroy(tile)

        funnyDist = None
        for pos in Builder.nav.core:
            if funnyDist is None or tile.distance_squared(pos) < funnyDist:
                funnyDist = tile.distance_squared(pos)
        if(funnyDist == None):
            return nearestOreDist
        if Builder.canBuildHarvester and ct.can_build_harvester(tile):
            ct.build_harvester(tile)
            #we build a barrier to reserve the tile. We will build a harvester later.
            Builder.uniqueRoute = funnyDist <= Builder.maxRouteLength

            compareLoc = currLoc
            if Builder._get_core_center():
                compareLoc= Builder._get_core_center()
            sorted_dirs = sorted(Constants.CARDINALS, key=lambda d: compareLoc.distance_squared(tile.add(d)))

            for d in sorted_dirs:
                check_pos = tile.add(d)
                if shouldRoute(ct, check_pos):
                    doRoute(check_pos, tile, ct)
                    Builder.nextToHarvestor = True
                    break

    return nearestOreDist


def doRoute(check_pos, tile, ct):
    from builder import Builder
    Builder.prevFrom = None
    Builder.routeFrom = check_pos
    Builder.state = Constants.states.ROUTE_CONVEYOR
    Builder.nearestNode = None
    Builder.theHarvester = tile
    if Builder.nav.getTile(tile) == Constants.tiles.ORE_TITANIUM:
        Builder.oreType = 0
    else:
        Builder.oreType = 1
        try:
            # Prefer splitters that already have titanium inputs; fall back to nearest
            splitters_with_inputs = [
                s for s in Builder.nav.DA_SPLITTER
                if count_splitter_inputs(ct, s) > 0
            ]
            if splitters_with_inputs:
                Builder.DA_SPLITTER = min(
                    splitters_with_inputs,
                    key=lambda s: tile.distance_squared(s)
                )
                print("[doRoute] Axionite routing to splitter with titanium inputs:", Builder.DA_SPLITTER)
            else:
                Builder.DA_SPLITTER = min(
                    Builder.nav.DA_SPLITTER,
                    key=lambda s: tile.distance_squared(s)
                )
                print("[doRoute] No splitters with titanium inputs yet, routing to nearest:", Builder.DA_SPLITTER)
        except Exception:
            Builder.DA_SPLITTER = None
        Builder.uniqueRoute = True
    print("Planning a route from",check_pos,"and harvester",tile,"Splitter planned",Builder.DA_SPLITTER)

def leave(tile,nearestOreDistance,ct):
    from builder import Builder
    if(Builder.targLoc == tile):
        Builder.setScoutTarget(ct)
        print("Leaving from tile,",tile,"We setting thingity here! Now is",Builder.targLoc)
        Builder.theHarvester = None
    return nearestOreDistance
#builder.py
from cambc import *
from utils.constants import Constants
from utils.nav import Nav
from utils.building import Building
from utils.encoding import Encoding
from builder_routing import shouldRoute, get_best_intermediate_pos, count_splitter_inputs
from builder_ore import goNearestOre
import random


class Builder:
    nav = None
    targLoc = None
    state = Constants.states.SCOUT
    nearestNode = None
    routeFrom = None
    prevFrom = None
    maxRouteLength = None
    uniqueRoute = False
    triedCoreFallback = False
    oreType = 0
    DA_SPLITTER = None
    scoutTick = 0
    canBuildHarvester = False
    _canBuildHarvesterTicks = 0
    weSawCore = False
    mode = -1
    isAttackRoute = False
    attackOrePos = None
    nextToHarvestor = False
    theHarvester = None
    buildLauncher = None
    threeLocArea = [] #rotational, vertical, horizontal
    persistentTarget = None  # Stores the Position of the enemy building we found
    sentinelTargPos = None
    healFlag = False
    PREFERRED_DIR = None

    @staticmethod
    def init(ct: Controller):
        random.seed(ct.get_current_round())
        Builder.nav = Nav(ct)
        Builder.targLoc = Builder.nav.get_nearest_unknown_region_center()
        Builder.maxRouteLength = (ct.get_map_width() ** 2 + ct.get_map_height() // 2)
        if(ct.get_current_round() <=2):
            Builder.mode = 0
        else:
            Builder.mode = 1
        currLoc = ct.get_position()
        #across
        Builder.threeLocArea.append(Position(ct.get_map_width() - 1 - currLoc.x, ct.get_map_height() - 1 - currLoc.y))
        #vertical
        Builder.threeLocArea.append(Position(currLoc.x, ct.get_map_height() - 1 - currLoc.y))
        #horizontal
        Builder.threeLocArea.append(Position(ct.get_map_width() - 1 - currLoc.x, currLoc.y))


    @staticmethod
    def setScoutTarget(ct: Controller):
        Builder.scoutTick = 0
        Builder.isAttackRoute = False
        Builder.attackOrePos = None
        if(Builder.mode == 0):
            enemyCore = Builder.nav.get_enemy_core_center()
            if(enemyCore):
                Builder.targLoc = enemyCore
            elif len(Builder.threeLocArea) != 0:
                Builder.targLoc = Builder.threeLocArea[0]
            else:
                Builder.targLoc = Builder.nav.get_nearest_unknown_region_center(Builder.PREFERRED_DIR)
        else:
            Builder.targLoc = Builder.nav.get_nearest_unknown_region_center(Builder.PREFERRED_DIR)
        Builder.state = Constants.states.SCOUT

        Builder.routeFrom = None
        Builder.prevFrom = None
        Builder.nearestNode = None
        Builder.theHarvester = None

    @staticmethod
    def tick(ct: Controller) -> None:
        if Builder.nav is None:
            Builder.init(ct)
        Builder.nav.setup(ct)
        Builder.healFlag = False
        if Builder.persistentTarget == None and Builder.state == Constants.states.ATTACK:
            Builder.setScoutTarget(ct)
        """
        if(ct.get_current_round() > 450):
            ct.resign()
        """


        if ct.get_global_resources()[0] > ct.get_harvester_cost()[0]:
            Builder._canBuildHarvesterTicks += 1
        else:
            Builder._canBuildHarvesterTicks = 0
        Builder.canBuildHarvester = Builder._canBuildHarvesterTicks >= 2 #or (len(Builder.nav.FOUNDRIES) == len(Builder.nav.DA_SPLITTER) and ct.get_harvester_cost()[0] > ct.get_global_resources()[0])

        tiles = ct.get_nearby_tiles()
        nearestOreDist = 9999999999999999
        currLoc = ct.get_position()

        for tile in tiles:
            nearestOreDist = Builder.updateTile(ct,tile,currLoc,nearestOreDist,True)

        if Builder.PREFERRED_DIR == None:
            Builder.PREFERRED_DIR = currLoc.direction_to(Builder._get_core_center())

        newThreeLocs = []
        for val in Builder.threeLocArea:
            if currLoc.distance_squared(val) > GameConstants.BUILDER_BOT_VISION_RADIUS_SQ-2:
                newThreeLocs.append(val)
        Builder.threeLocArea = newThreeLocs
        currLoc = ct.get_position()
        if(Builder.buildLauncher != None):
            print("Launcher cost",ct.get_launcher_cost()[0],"planning on building",Builder.buildLauncher)
            if ct.get_launcher_cost()[0] > ct.get_global_resources()[0] and (ct.get_current_round() < Constants.GOAXIONITE):
                Builder.buildLauncher = None
            else:
                theThingThere = Builder.nav.getBuilding(Builder.buildLauncher)
                if theThingThere == 0 or (theThingThere.team == ct.get_team() and (theThingThere.entityType not in Constants.ROUTING + [EntityType.BARRIER] or theThingThere.entityType == EntityType.BARRIER and Builder.buildLauncher in Builder.nav.NOROUTE)):
                    if(currLoc.distance_squared(Builder.buildLauncher) > GameConstants.ACTION_RADIUS_SQ):
                        Builder.nav.moveTo(Builder.buildLauncher)
                    elif(currLoc == Builder.buildLauncher):
                        currLoc = Builder.nav.moveRandomly()
                    if(ct.get_launcher_cost()[0]<ct.get_global_resources()[0] and ct.can_destroy(Builder.buildLauncher)):
                        ct.destroy(Builder.buildLauncher)
                    if(ct.can_build_launcher(Builder.buildLauncher)):
                        ct.build_launcher(Builder.buildLauncher)
                        Builder.updateTile(ct,Builder.buildLauncher,currLoc,None,False)
                        Builder.buildLauncher = None
                else:
                    Builder.buildLauncher = None
        else:
            Builder.buildLauncher = None
        print("Yummy",ct.get_cpu_time_elapsed())
        if ct.get_current_round() >= 1995:
            print("Round 1995. Breach building for funny")
            for d in Constants.DIRECTIONS:
                checkPos = ct.get_position().add(d)
                buildThere = Builder.nav.getBuilding(checkPos)
                if buildThere != 0 and buildThere.team == ct.get_team() and buildThere.entityType == EntityType.BREACH:
                    continue
                if ct.can_destroy(checkPos):
                    ct.destroy(checkPos)
                if ct.can_build_breach(checkPos,Direction.NORTH):
                    ct.build_breach(checkPos,Direction.NORTH)
        core = Builder.nav.getBuilding(Builder._nearest_core(currLoc))
        if(core != 0 and core.hp < GameConstants.CORE_MAX_HP-10):
            if(ct.can_heal(currLoc)):
                ct.heal(currLoc)
            Builder.nav.moveTo(Builder._nearest_core(currLoc))
            print("healing core!")
            return
        currLoc = ct.get_position()
        for d in Constants.DIRECTIONS:
            newLoc = currLoc.add(d)
            if not Builder.nav.onMap(newLoc):
                continue
            if(ct.can_heal(newLoc)):
                ct.heal(newLoc)
                print("healing at",newLoc)
            if Builder.state not in [Constants.states.ROUTE_CONVEYOR,Constants.states.BUILD_SPLITTER]:
                buildingThere = Builder.nav.getBuilding(newLoc)
                if buildingThere == 0 or buildingThere.entityType not in [EntityType.BARRIER, EntityType.FOUNDRY, EntityType.LAUNCHER]:
                    if (newLoc in Builder.nav.FOUNDRIES or newLoc in Builder.nav.NOROUTE) and currLoc != newLoc:
                        if buildingThere != 0 and buildingThere.entityType == EntityType.ROAD and ct.get_barrier_cost()[0] < ct.get_global_resources()[0] and ct.can_destroy(newLoc):
                            ct.destroy(newLoc)
                        if ct.can_build_barrier(newLoc):
                            ct.build_barrier(newLoc)
                            Builder.updateTile(ct,newLoc,currLoc,None)
                if buildingThere == 0 or buildingThere.entityType not in [EntityType.BARRIER, EntityType.SPLITTER]:
                    if newLoc in Builder.nav.DA_SPLITTER:
                        dirToCore = newLoc.direction_to(Builder._get_core_center())
                        if buildingThere != 0 and buildingThere.entityType == EntityType.ROAD and ct.get_splitter_cost()[0] < ct.get_global_resources()[0] and ct.can_destroy(newLoc):
                            ct.destroy(newLoc)
                        if ct.can_build_splitter(newLoc,dirToCore):
                            ct.build_splitter(newLoc,dirToCore)
                            Builder.updateTile(ct,newLoc,currLoc,None)             

        if (ct.get_global_resources()[0] >= 1000 or Builder.weSawCore or Builder.mode == 0) and (Builder.nav.get_enemy_core_center() is not None) and Builder.state not in [Constants.states.ATTACK, Constants.states.ROUTE_CONVEYOR,Constants.states.BUILD_SPLITTER]:
            # 1. Look for a new target if we don't have one or if we are close enough to see the old one
            visible_thingy = Builder.nav.get_highest_enemy_thing_near_core(GameConstants.SENTINEL_VISION_RADIUS_SQ)
            
            # Update persistent target if we see something high priority
            if visible_thingy:
                Builder.persistentTarget = visible_thingy
            
            # 2. If we have a persistent target, verify if it's still valid
            if Builder.persistentTarget:
                # If we are close enough to see the spot, check if the building is actually gone
                if currLoc.distance_squared(Builder.persistentTarget) <= GameConstants.BUILDER_BOT_VISION_RADIUS_SQ:
                    b = Builder.nav.getBuilding(Builder.persistentTarget)
                    # If it's now our team's building, the target is cleared
                    if b != 0 and (not b.is_passable() or b.entityType in Constants.TURRETS):
                        Builder.persistentTarget = None

            # 3. Execution Logic
            enemy_core = Builder.nav.get_enemy_core_center()
            if Builder.persistentTarget:
                Builder._handle_attack(ct,Builder.persistentTarget.direction_to(enemy_core), True)
                return # Exit tick to stay focused on the target

            # 4. Fallback: No persistent target, but we are near the core
            elif Builder.targLoc.distance_squared(currLoc) <= GameConstants.SENTINEL_VISION_RADIUS_SQ:
                if not Builder.isAttackRoute:
                    Builder._setup_attack_route(ct, currLoc)
                    return
        elif Builder.healFlag:
            if Builder.targLoc.distance_squared(currLoc) > GameConstants.ACTION_RADIUS_SQ:
                Builder.nav.moveTo(Builder.targLoc)
                return

        currLoc = ct.get_position()

        if Builder.state == Constants.states.SCOUT:
            Builder._handle_scout(ct, currLoc)

        if Builder.nav.core and not Builder.nav.DA_SPLITTER:
            Builder._seed_splitter_positions()

        # ── Ensure attack route harvester is built BEFORE doing conveyor routing ──
        if Builder.isAttackRoute and Builder.attackOrePos is not None:
            ore_pos = Builder.attackOrePos
            ore_building = Builder.nav.getBuilding(ore_pos)
            if ore_building == 0 or ore_building.entityType != EntityType.HARVESTER:
                if currLoc.distance_squared(ore_pos) <= GameConstants.ACTION_RADIUS_SQ:
                    if ore_building != 0:
                        if ct.can_destroy(ore_pos):
                            ct.destroy(ore_pos)
                        return
                    elif ct.can_build_harvester(ore_pos):
                        ct.build_harvester(ore_pos)
                        Builder.updateTile(ct,ore_pos,currLoc,None)
                        print("[Builder] Built attack-route harvester at", ore_pos)
                        return
                    else:
                        # Return to block routing logic while we wait for resources
                        return 
                else:
                    Builder.nav.moveTo(ore_pos)
                    return

        currLoc = ct.get_position()

        if Builder.healFlag:
            Builder.nav.moveTo(Builder.targLoc)
        elif Builder.state == Constants.states.BUILD_FOUNDRY:
            Builder._handle_build_foundry(ct, currLoc)
        elif Builder.state == Constants.states.BUILD_SPLITTER:
            Builder._handle_build_splitter(ct, currLoc)
        elif Builder.state == Constants.states.ROUTE_CONVEYOR:
            Builder._handle_route_conveyor(ct, currLoc)
        elif Builder.state == Constants.states.ATTACK:
            """"""
            # If we are close enough to see the spot, check if the building is actually gone
            if currLoc.distance_squared(Builder.persistentTarget) <= GameConstants.BUILDER_BOT_VISION_RADIUS_SQ:
                b = Builder.nav.getBuilding(Builder.persistentTarget)
                # If it's empty or now our team's building, the target is cleared
                if b != 0 and (not b.is_passable() or b.entityType in Constants.TURRETS):
                    Builder.persistentTarget = None
                    Builder.setScoutTarget(ct)

            # 3. Execution Logic
            if Builder.persistentTarget:
                targ = Builder.nav.get_enemy_core_center()
                if targ == None:
                    targ = Builder.sentinelTargPos
                    if targ == None:
                        targ = Position(-1,-1)
                dir = Builder.persistentTarget.direction_to(targ)
                Builder._handle_attack(ct,dir)
        else:
            if(Builder.theHarvester == None or Builder.theHarvester.distance_squared(currLoc) > GameConstants.ACTION_RADIUS_SQ):
                Builder.nav.moveTo(Builder.targLoc)

        if Builder.targLoc is not None and Builder.state == Constants.states.SCOUT:
            ct.draw_indicator_line(ct.get_position(), Builder.targLoc, 0, 0, 255)
        print("Finished bot tick for round:", ct.get_current_round(), "state:", Builder.state, "Enemy Core Location:", Builder.nav.get_enemy_core_center(),"did we see core:",Builder.weSawCore,"Mode",Builder.mode,"Targloc",Builder.targLoc,"Healing",Builder.healFlag)

    @staticmethod
    def _handle_attack(ct,dirToBuild,coreGun = False):
        currLoc = ct.get_position()
        Builder.targLoc = Builder.persistentTarget
        
        # Draw a line to the "remembered" target so you can debug
        ct.draw_indicator_line(currLoc, Builder.persistentTarget, 255, 165, 0) # Orange for locked target
        
        dist_to_enemy_core = Builder.nav.dist_sq_to_nearest_enemy_core(Builder.persistentTarget)

        daBuilding = Builder.nav.getBuilding(Builder.persistentTarget)
        if daBuilding == 0 or daBuilding.team == ct.get_team():
            # Move to the remembered location
            if currLoc == Builder.persistentTarget:
                Builder.nav.moveRandomly()
            
            if ct.can_destroy(Builder.persistentTarget):
                ct.destroy(Builder.persistentTarget)
        else:
            # Enemy building is visible and active
            if Builder.persistentTarget == currLoc:
                if ct.can_fire(currLoc):
                    ct.fire(currLoc)
                newId = ct.get_tile_building_id(currLoc)
                if newId == None:
                    currLoc = Builder.nav.moveRandomly()
            else:
                Builder.nav.moveTo(Builder.persistentTarget)
                currLoc = ct.get_position()
                if Builder.persistentTarget == currLoc:
                    if ct.can_fire(currLoc):
                        ct.fire(currLoc)

        if coreGun and dist_to_enemy_core <= 2:
            if ct.can_build_gunner(Builder.persistentTarget, dirToBuild):
                ct.build_gunner(Builder.persistentTarget, dirToBuild)
                Builder.updateTile(ct,Builder.persistentTarget,currLoc,None)
            else:
                Builder.nav.moveTo(Builder.persistentTarget)
        else:
            if ct.can_build_sentinel(Builder.persistentTarget, dirToBuild):
                ct.build_sentinel(Builder.persistentTarget, dirToBuild)
                Builder.updateTile(ct,Builder.persistentTarget,currLoc,None)
            elif currLoc.distance_squared(Builder.persistentTarget) > GameConstants.ACTION_RADIUS_SQ:
                Builder.nav.moveTo(Builder.persistentTarget)

    @staticmethod
    def _handle_scout(ct, currLoc):
        Builder.scoutTick += 1
        if Builder.mode != 0:
            nearest_ore = Builder._nearest_available_ore(ct)
            if nearest_ore is not None:
                Builder.targLoc = nearest_ore
                return
        if Builder.scoutTick >= Constants.SCOUT_MAX_TIME:
            Builder.setScoutTarget(ct)

    @staticmethod
    def _nearest_available_ore(ct):
        best = None
        best_dist = float('inf')
        coreLoc = Builder._get_core_center()
        if coreLoc == None:
            return Position(0,0)
        for key, status in Builder.nav.titaniumOres.items():
            if status != 'A':
                continue
            pos = Position(key[0], key[1])
            d = coreLoc.distance_squared(pos)
            if d < best_dist:
                best_dist = d
                best = pos
        if ct.get_current_round() >= Constants.GOAXIONITE:
            for key, status in Builder.nav.axioniteOres.items():
                if status != 'A':
                    continue
                pos = Position(key[0], key[1])
                d = coreLoc.distance_squared(pos)
                if d < best_dist:
                    best_dist = d
                    best = pos
        return best

    @staticmethod
    def _handle_build_foundry(ct, currLoc):
        nodeToBuild = Builder.nearestNode
        print("Trying to build foundry:", nodeToBuild, "Cost:", ct.get_foundry_cost()[0])

        daBuilding = Builder.nav.getBuilding(nodeToBuild)
        if daBuilding == 0 or daBuilding.entityType != EntityType.FOUNDRY:
            if ct.get_foundry_cost()[0] < ct.get_global_resources()[0] and ct.can_destroy(nodeToBuild):
                ct.destroy(nodeToBuild)
            if ct.can_build_foundry(nodeToBuild):
                ct.build_foundry(nodeToBuild)
                Builder.DA_SPLITTER = None
                Builder.setScoutTarget(ct)
                Builder.nearestNode = None
                Builder.updateTile(ct,nodeToBuild,currLoc,None)
            else:
                if currLoc == nodeToBuild:
                    currLoc = Builder.nav.moveRandomly()
                elif currLoc.distance_squared(nodeToBuild) > GameConstants.ACTION_RADIUS_SQ:
                    Builder.nav.moveTo(nodeToBuild)
        else:
            Builder.setScoutTarget(ct)
            Builder.DA_SPLITTER = None

    @staticmethod
    def _get_core_center():
        if not Builder.nav.core:
            return None
        return Position(
            sum(p.x for p in Builder.nav.core) // len(Builder.nav.core),
            sum(p.y for p in Builder.nav.core) // len(Builder.nav.core),
        )

    @staticmethod
    def _handle_build_splitter(ct, currLoc):
        if Builder.isAttackRoute:
            Builder._handle_build_attack_sentinel(ct, currLoc)
            return

        nodeToBuild = Builder.nearestNode
        print("Trying to build splitter:", nodeToBuild)

        core_center = Builder._get_core_center()
        dir_to_core = (
            nodeToBuild.direction_to(core_center)
            if core_center is not None
            else Direction.NORTH
        )

        daBuilding = Builder.nav.getBuilding(nodeToBuild)
        if daBuilding == 0 or daBuilding.entityType != EntityType.SPLITTER:
            if ct.can_destroy(nodeToBuild):
                ct.destroy(nodeToBuild)
            if ct.can_build_splitter(nodeToBuild, dir_to_core):
                ct.build_splitter(nodeToBuild, dir_to_core)
                Builder.updateTile(ct,nodeToBuild,currLoc,None)
                Builder.DA_SPLITTER = None
                Builder.setScoutTarget(ct)
                Builder.nearestNode = None
                if Constants.DEFENSE_BUILDING:
                    theThingy = nodeToBuild.add(dir_to_core.rotate_left().rotate_left())
                    Builder.buildLauncher = theThingy
            else:
                if currLoc == nodeToBuild:
                    currLoc = Builder.nav.moveRandomly()
                elif currLoc.distance_squared(nodeToBuild) > GameConstants.ACTION_RADIUS_SQ:
                    Builder.nav.moveTo(nodeToBuild)
        else:
            # Splitter already exists — still schedule the launcher if it was never built
            theThingy = nodeToBuild.add(dir_to_core.rotate_left().rotate_left())
            existing = Builder.nav.getBuilding(theThingy)
            if existing == 0 or (existing.team == ct.get_team()
                    and existing.entityType != EntityType.LAUNCHER):
                Builder.buildLauncher = theThingy
            Builder.setScoutTarget(ct)
            Builder.DA_SPLITTER = None

    @staticmethod
    def _seed_splitter_positions():
        """
        Pre-register the four expected splitter positions around the core
        without physically building anything.  Routing will build them on arrival.
        """
        center = Builder._get_core_center()
        if center is None:
            return
        cx, cy = center.x, center.y
        for dx, dy in[(0, -2), (0, 2), (-2, 0), (2, 0)]:
            pos = Position(cx + dx, cy + dy)
            if not Builder.nav.onMap(pos):
                continue
            if Builder.nav.getTile(pos) in [Constants.tiles.ORE_AXIONITE, Constants.tiles.ORE_TITANIUM,Constants.tiles.WALL]:
                continue
            if Builder.nav.onMap(pos) and pos not in Builder.nav.DA_SPLITTER:
                Builder.nav.DA_SPLITTER.append(pos)
                Builder.nav.nodeToSplitter.append(0)
        for dx, dy in[(-1, -2), (1, 2), (-2, 1), (2, -1)]:
            pos = Position(cx + dx, cy + dy)
            if not Builder.nav.onMap(pos):
                continue
            if Builder.nav.getTile(pos) in [Constants.tiles.ORE_AXIONITE, Constants.tiles.ORE_TITANIUM,Constants.tiles.WALL]:
                continue
            if pos not in Builder.nav.FOUNDRIES:
                Builder.nav.FOUNDRIES.append(pos)
        for dx, dy in[(1, -2), (-1, 2), (-2, -1), (2, 1)]:
            pos = Position(cx + dx, cy + dy)
            if not Builder.nav.onMap(pos):
                continue
            if Builder.nav.getTile(pos) in [Constants.tiles.ORE_AXIONITE, Constants.tiles.ORE_TITANIUM,Constants.tiles.WALL]:
                continue
            if Builder.nav.onMap(pos) and pos not in Builder.nav.NOROUTE:
                Builder.nav.NOROUTE.append(pos)
        print("[Builder] Seeded splitter positions:", Builder.nav.DA_SPLITTER)
        print("[Builder] Seeded foundry positions:", Builder.nav.FOUNDRIES)
        print("[Builder] Seeded jumper positions:", Builder.nav.NOROUTE)
        

    @staticmethod
    def _handle_maintenance(ct, currLoc):
        if currLoc == Builder.targLoc:
            currLoc = Builder.nav.moveRandomly()
        elif currLoc.distance_squared(Builder.targLoc) > GameConstants.ACTION_RADIUS_SQ:
            Builder.nav.moveTo(Builder.targLoc)

    @staticmethod
    def _handle_route_conveyor(ct, currLoc):
        if Builder.nearestNode is None and not Builder.isAttackRoute:
            Builder._pick_route_target(ct, currLoc)
        if Builder.nearestNode is None:  # ADD THIS
            Builder.setScoutTarget(ct)
            return

        print("Thinking from", Builder.routeFrom,"Harvester",Builder.theHarvester)
        if(Builder.nextToHarvestor):
            print("Thinking next to harvester")
            if Constants.ORE_BORDER:
                for d in Constants.CARDINALS:
                    checkLoc = Builder.theHarvester.add(d)
                    if(not Builder.nav.onMap(checkLoc)):
                        continue
                    if(Builder.routeFrom == checkLoc):
                        continue
                    env = Builder.nav.getTile(checkLoc)
                    if(env in [Constants.tiles.WALL]):
                        continue
                    buildingOnTile = Builder.nav.getBuilding(checkLoc)
                    if buildingOnTile != 0:
                        if buildingOnTile.team != ct.get_team():
                            continue
                        elif buildingOnTile.entityType in (Constants.ROUTING + Constants.TURRETS):
                            continue
                        if(buildingOnTile.entityType != EntityType.BARRIER):
                            print("Trying to build barrier",checkLoc)
                            if(ct.can_destroy(checkLoc)):
                                ct.destroy(checkLoc)
                            if(ct.get_position() == checkLoc):
                                Builder.nav.moveTo(Builder.routeFrom)
                            if(ct.can_build_barrier(checkLoc)):
                                ct.build_barrier(checkLoc)
                                Builder.updateTile(ct,checkLoc,currLoc,None)
                            elif currLoc.distance_squared(checkLoc) > GameConstants.ACTION_RADIUS_SQ:
                                Builder.nav.moveTo(checkLoc)
                            return
                    else:
                        if(ct.can_build_barrier(checkLoc)):
                            ct.build_barrier(checkLoc)
                            Builder.updateTile(ct,checkLoc,currLoc,None)
                        elif (ct.get_position() == checkLoc):
                                Builder.nav.moveTo(Builder.routeFrom)
                        elif currLoc.distance_squared(checkLoc) > GameConstants.ACTION_RADIUS_SQ:
                            Builder.nav.moveTo(checkLoc)
                        return
                else:
                    Builder.nextToHarvestor = False

        if Builder.theHarvester != None:
            buildingOnOre = Builder.nav.getBuilding(Builder.theHarvester)
            if buildingOnOre == 0 or (buildingOnOre.entityType != EntityType.HARVESTER and buildingOnOre.team == ct.get_team()):
                if currLoc == Builder.theHarvester:
                    currLoc = Builder.nav.moveRandomly()
                elif currLoc.distance_squared(Builder.theHarvester) > GameConstants.ACTION_RADIUS_SQ:
                    Builder.nav.moveTo(Builder.theHarvester)

                if ct.can_destroy(Builder.theHarvester) and ct.get_action_cooldown() == 0 and ct.get_global_resources()[0]>ct.get_harvester_cost()[0]:
                    ct.destroy(Builder.theHarvester)
                if ct.can_build_harvester(Builder.theHarvester):
                    ct.build_harvester(Builder.theHarvester)
                    Builder.updateTile(ct,Builder.theHarvester,currLoc,None)
            

        if (Builder.DA_SPLITTER is not None
                and Builder.oreType == 0
                and Builder.nearestNode == Builder.DA_SPLITTER
                and currLoc.distance_squared(Builder.DA_SPLITTER) <= 9):
            current_count = count_splitter_inputs(ct, Builder.DA_SPLITTER)
            print("Re-evaluating splitter", Builder.DA_SPLITTER, "inputs:", current_count)
            if current_count >= 4:
                print("Splitter full on recheck, redirecting to core")
                Builder.DA_SPLITTER = None
                Builder.uniqueRoute = True
                Builder.nearestNode = Builder._nearest_core(currLoc)

        if not shouldRoute(ct, Builder.routeFrom):
            print("GAHH Somebody stole my route! Recalculating...")
            Builder.routeFrom = Builder.prevFrom
            if Builder.routeFrom is None or not shouldRoute(ct, Builder.routeFrom):
                print("GAHH No valid route!")
                if Builder.oreType == 0 and not Builder.triedCoreFallback:
                    print("Titanium — rerouting direct to core")
                    Builder.DA_SPLITTER = None
                    Builder.uniqueRoute = True
                    Builder.triedCoreFallback = True
                    Builder.nearestNode = Builder._nearest_core(currLoc)
                    Builder.routeFrom = currLoc  
                    return
                print("No valid route at all, going to scout mode...")
                Builder.triedCoreFallback = False
                Builder.setScoutTarget(ct)
                return

        toBuildTo = get_best_intermediate_pos(Builder.routeFrom, Builder.nearestNode, ct)
        print("Routing from:", Builder.routeFrom, "to:", Builder.nearestNode, "via:", toBuildTo, "SetSplitter:", Builder.DA_SPLITTER)

        if toBuildTo == Builder.routeFrom:
            if toBuildTo in Builder.nav.DA_SPLITTER:
                Builder._handle_build_splitter(ct,currLoc)
                return
            else:
                print("GAHH No valid route!")
                if Builder.oreType == 0 and not Builder.triedCoreFallback:
                    print("Titanium — rerouting direct to core")
                    Builder.DA_SPLITTER = None
                    Builder.uniqueRoute = True
                    Builder.triedCoreFallback = True
                    Builder.nearestNode = Builder._nearest_core(currLoc)
                    Builder.routeFrom = currLoc 
                    return
                print("No valid route at all, going to scout mode...")
                Builder.triedCoreFallback = False
                Builder.setScoutTarget(ct)
                return
        ct.draw_indicator_line(Builder.routeFrom, toBuildTo, 0, 255, 0)

        routeFrom_building = Builder.nav.getBuilding(Builder.routeFrom)
        if (routeFrom_building != 0
                and routeFrom_building.team != ct.get_team()
                and routeFrom_building.is_passable()):
            if currLoc != Builder.routeFrom:
                Builder.nav.moveTo(Builder.routeFrom)
            elif ct.can_fire(currLoc):
                ct.fire(currLoc)
            return  # stall here until the enemy building is gone
        
        buildConv = Builder.routeFrom.distance_squared(toBuildTo) <= 1

        if buildConv and Builder.buildLauncher is None and Constants.DEFENSE_BUILDING:
            # ── COVERAGE CHECK ──
            # Before placing a conveyor/bridge on routeFrom, ensure routeFrom is covered.
            if not Builder.is_tile_covered_by_launcher(ct, Builder.routeFrom):
                print(f"[Builder] Coverage Gap detected at {Builder.routeFrom}. Finding launcher spot...")
                
                # Find a spot ADJACENT to routeFrom that isn't the path we're walking
                launcher_spot = None
                hasAwesome = False
                for d in Constants.DIRECTIONS:
                    candidate = Builder.routeFrom.add(d)
                    if not Builder.nav.onMap(candidate): continue
                    if candidate == toBuildTo: continue
                    tile_env = Builder.nav.getTile(candidate)
                    if tile_env in [Constants.tiles.WALL, Constants.tiles.ORE_AXIONITE, Constants.tiles.ORE_TITANIUM]:
                        continue
                    existing = Builder.nav.getBuilding(candidate)
                    if existing == 0 or existing.entityType == EntityType.ROAD:
                        if not hasAwesome:
                            launcher_spot = candidate
                            if candidate.distance_squared(toBuildTo) <= 2:
                                hasAwesome = True
                                break
                
                if launcher_spot:
                    if Builder.nav.hasSupplyToCore:
                        Builder.buildLauncher = launcher_spot
                        return

        if ct.can_destroy(Builder.routeFrom) and ct.get_action_cooldown() == 0 and Builder.buildLauncher is None:
            if buildConv:
                if ct.get_global_resources()[0]>ct.get_conveyor_cost()[0]:
                    ct.destroy(Builder.routeFrom)
            else:
                if ct.get_global_resources()[0]>ct.get_bridge_cost()[0]:
                    ct.destroy(Builder.routeFrom)
        """
        if ct.can_destroy(toBuildTo) and toBuildTo != Builder.routeFrom and toBuildTo != Builder.nearestNode:
            ct.destroy(toBuildTo)
        """

        didBuild = False
        if (buildConv
                and ct.can_build_conveyor(Builder.routeFrom, Builder.routeFrom.direction_to(toBuildTo))):
            if ct.can_build_armoured_conveyor(Builder.routeFrom, Builder.routeFrom.direction_to(toBuildTo)):
                print("Building armoured conveyor from:", Builder.routeFrom, "to:", toBuildTo)
                ct.build_armoured_conveyor(Builder.routeFrom, Builder.routeFrom.direction_to(toBuildTo))        
            else:
                print("Building conveyor from:", Builder.routeFrom, "to:", toBuildTo)
                ct.build_conveyor(Builder.routeFrom, Builder.routeFrom.direction_to(toBuildTo))
            Builder.updateTile(ct,Builder.routeFrom,currLoc,None)
            didBuild = True
        elif ct.can_build_bridge(Builder.routeFrom, toBuildTo):
            # Before building the bridge, ensure a launcher is placed adjacent to it first.
            if Builder.buildLauncher is None and Constants.DEFENSE_BUILDING:
                pending_launcher = None
                hasAwesome = False
                freeLoc = 0
                for d in Constants.DIRECTIONS:
                    newLoc = Builder.routeFrom.add(d)
                    if not Builder.nav.onMap(newLoc):
                        continue
                    tileThere = Builder.nav.getTile(newLoc)
                    if tileThere in [Constants.tiles.WALL, Constants.tiles.ORE_AXIONITE, Constants.tiles.ORE_TITANIUM]:
                        continue
                    if newLoc in Builder.nav.DA_SPLITTER or newLoc in Builder.nav.FOUNDRIES:
                        continue
                    daBuildingthere = Builder.nav.getBuilding(newLoc)
                    if daBuildingthere != 0 and daBuildingthere.team == ct.get_team() and daBuildingthere.entityType == EntityType.LAUNCHER:
                        # Launcher already present — no need to wait
                        pending_launcher = None
                        break
                    if (daBuildingthere == 0 or (daBuildingthere.team == ct.get_team() and daBuildingthere.entityType not in Constants.ROUTING + [EntityType.BARRIER])):
                        freeLoc += 1
                        if not hasAwesome:
                            pending_launcher = newLoc
                            if newLoc.distance_squared(toBuildTo) <= 2:
                                hasAwesome = True
                if pending_launcher is not None and freeLoc >=2:
                    if Builder.nav.hasSupplyToCore:
                        print("[Builder] Queuing launcher at", pending_launcher, "before building bridge", Builder.routeFrom, "->", toBuildTo)
                        Builder.buildLauncher = pending_launcher
                        return
            # Launcher is either built or not needed — now lay the bridge
            print("Building bridge from:", Builder.routeFrom, "to:", toBuildTo)
            ct.build_bridge(Builder.routeFrom, toBuildTo)
            Builder.updateTile(ct,Builder.routeFrom,currLoc,None)
            didBuild = True
        elif currLoc != Builder.routeFrom:
            Builder.nav.moveTo(Builder.routeFrom)

        if didBuild:
            print("Yay we build!")
            Builder.triedCoreFallback = False
            Builder.prevFrom = Builder.routeFrom
            Builder.routeFrom = toBuildTo
            if toBuildTo == Builder.nearestNode:
                Builder.state = Constants.states.SCOUT
                Builder.routeFrom = None
                Builder.prevFrom = None
                Builder.nextToHarvestor = False
                Builder.theHarvester = None
                if Builder.oreType == 1:
                    # Axionite — need a foundry at the endpoint
                    daBuilding = Builder.nav.getBuilding(toBuildTo)
                    if daBuilding == 0 or daBuilding.entityType != EntityType.FOUNDRY:
                        Builder.state = Constants.states.BUILD_FOUNDRY
                    else:
                        Builder.setScoutTarget(ct)
                        Builder.nearestNode = None
                else:
                    # Titanium — need a splitter at the endpoint.
                    if(Builder.DA_SPLITTER):
                        Builder.state = Constants.states.BUILD_SPLITTER
                    if Builder.isAttackRoute:
                        daBuilding = Builder.nav.getBuilding(toBuildTo)
                        if daBuilding == 0 or daBuilding.entityType != EntityType.SENTINEL:
                            # _handle_build_splitter will redirect via isAttackRoute flag
                            Builder.state = Constants.states.BUILD_SPLITTER
                        else:
                            print("[Builder] Attack sentinel already present — done")
                            Builder.isAttackRoute = False
                            Builder.setScoutTarget(ct)
                            Builder.nearestNode = None

    @staticmethod
    def _pick_route_target(ct, currLoc):
        if Builder.isAttackRoute:
            return
        if Builder.DA_SPLITTER is not None and Builder.oreType == 1:
            if Builder.DA_SPLITTER not in Builder.nav.DA_SPLITTER:
                Builder.DA_SPLITTER = min(Builder.nav.DA_SPLITTER, key=lambda s: currLoc.distance_squared(s))

            splitter = Builder.nav.getBuilding(Builder.DA_SPLITTER)
            if splitter != 0 and splitter.entityType == EntityType.SPLITTER:
                # Already built — use its facing direction to find foundry spot
                out_dir = splitter.direction.rotate_right().rotate_right()
            else:
                # Not built yet — derive outward direction from core center
                core_center = Builder._get_core_center()
                out_dir = (core_center.direction_to(Builder.DA_SPLITTER)
                        if core_center is not None else Direction.NORTH)

            Builder.nearestNode = Builder.DA_SPLITTER.add(out_dir)

        elif random.random() < Constants.ROUTE_TITANIUM_SPLITTER_CHANCE and Builder.oreType == 0:
            available_splitters =[s for s in Builder.nav.DA_SPLITTER if count_splitter_inputs(ct, s) < 4]
            if available_splitters:
                print(len(available_splitters), "available splitters")
                Builder.nearestNode = min(available_splitters, key=lambda s: currLoc.distance_squared(s))
                Builder.DA_SPLITTER = Builder.nearestNode
            else:
                print("All splitters full, routing titanium direct to core")
                Builder.DA_SPLITTER = None
                Builder.uniqueRoute = True
                Builder.nearestNode = Builder._nearest_core(currLoc)

        elif Builder.uniqueRoute:
            Builder.nearestNode = Builder._nearest_core(currLoc)

        else:
            nearestDist = None
            for pos in Builder.nav.nodes:
                dist = currLoc.distance_squared(pos)
                if nearestDist is None or dist < nearestDist:
                    nearestDist = dist
                    Builder.nearestNode = pos

    @staticmethod
    def _nearest_core(currLoc):
        nearest = None
        nearestDist = None
        for pos in Builder.nav.core:
            dist = currLoc.distance_squared(pos)
            if nearestDist is None or dist < nearestDist:
                nearestDist = dist
                nearest = pos
        return nearest

    @staticmethod
    def _setup_attack_route(ct, currLoc):
        enemy_core = Builder.nav.get_enemy_core_center()
        if enemy_core is None:
            Builder.nav.moveTo(Builder.targLoc)
            return

        vision_r = int(GameConstants.SENTINEL_VISION_RADIUS_SQ ** 0.5) + 1

        # ── Step 1: pick best attack/sentinel landing position ────────────────
        attack_pos = None
        best_attack_dist = float('inf')
        for dx in range(-vision_r, vision_r + 1):
            for dy in range(-vision_r, vision_r + 1):
                if dx * dx + dy * dy > GameConstants.SENTINEL_VISION_RADIUS_SQ:
                    continue
                candidate = Position(enemy_core.x + dx, enemy_core.y + dy)
                if not Builder.nav.onMap(candidate):
                    continue
                b = Builder.nav.getBuilding(candidate)
                if b != 0 and not b.is_passable():
                    continue
                if b!= 0 and b.team != ct.get_team():
                    continue
                d = currLoc.distance_squared(candidate)
                if d < best_attack_dist:
                    best_attack_dist = d
                    attack_pos = candidate

        if attack_pos is None:
            print("[Builder] No valid attack position within sentinel vision of enemy core")
            Builder.nav.moveTo(Builder.targLoc)
            return

        # ── Step 2: find nearest known titanium ore to the attack position ────
        ore_pos = None
        ore_dist = float('inf')
        for idx, tile_type in enumerate(Builder.nav.envMap):
            if tile_type == Constants.tiles.ORE_TITANIUM:
                x = idx % Builder.nav.width
                y = idx // Builder.nav.width
                pos = Position(x, y)
                d = attack_pos.distance_squared(pos)
                if d < ore_dist:
                    ore_dist = d
                    ore_pos = pos

        if ore_pos is None:
            print("[Builder] No titanium ore visible for attack route — moving to scout")
            Builder.nav.moveTo(Builder.targLoc)
            return

        # ── Step 3: save the ore position for harvester placement ─────────────
        Builder.attackOrePos = ore_pos

        # ── Step 3.5: check if sentinel can be placed directly adjacent to the harvester ──
        direct_sentinel_pos = None
        best_direct_dist = float('inf')
        for d in Constants.CARDINALS:
            adj = ore_pos.add(d)
            if not Builder.nav.onMap(adj):
                continue
            if Builder.nav.getTile(adj) in [Constants.tiles.WALL]:
                continue
            dist_to_core = adj.distance_squared(enemy_core)
            if dist_to_core <= GameConstants.SENTINEL_VISION_RADIUS_SQ:
                b = Builder.nav.getBuilding(adj)
                if b != 0 and not b.is_passable():
                    continue
                if dist_to_core < best_direct_dist:
                    best_direct_dist = dist_to_core
                    direct_sentinel_pos = adj

        if direct_sentinel_pos is not None:
            print("[Builder] Sentinel can be placed directly adjacent to harvester at", direct_sentinel_pos)
            Builder.nearestNode     = direct_sentinel_pos
            Builder.isAttackRoute   = True
            Builder.state           = Constants.states.BUILD_SPLITTER
            Builder.DA_SPLITTER     = None
            Builder.routeFrom       = None
            return

        # ── Step 4: pick the best adjacent tile as the conveyor route start ───
        route_start = None
        best_route_dist = float('inf')
        for d in Constants.CARDINALS:
            check = ore_pos.add(d)
            if shouldRoute(ct, check):
                dist_to_attack = check.distance_squared(attack_pos)
                if dist_to_attack < best_route_dist:
                    best_route_dist = dist_to_attack
                    route_start = check

        if route_start is None:
            print("[Builder] No valid route-start adjacent to ore at", ore_pos)
            Builder.nav.moveTo(Builder.targLoc)
            return

        # ── Step 5: commit routing state ──────────────────────────────────────
        print("[Builder] Attack route: from", route_start, "→", attack_pos,
              "(ore at", ore_pos, ")")
        Builder.routeFrom       = route_start
        Builder.nearestNode     = attack_pos
        Builder.oreType         = 0          # titanium
        Builder.uniqueRoute     = True
        Builder.DA_SPLITTER     = None
        Builder.triedCoreFallback = False
        Builder.isAttackRoute   = True
        Builder.state           = Constants.states.ROUTE_CONVEYOR

    @staticmethod
    def _handle_build_attack_sentinel(ct, currLoc):
        pos = Builder.nearestNode
        if pos is None:
            Builder.isAttackRoute = False
            Builder.setScoutTarget(ct)
            return

        enemy_core = Builder.nav.get_enemy_core_center()
        face_dir = (pos.direction_to(enemy_core)
                    if enemy_core is not None else Direction.NORTH)

        daBuilding = Builder.nav.getBuilding(pos)
        if daBuilding != 0 and daBuilding.entityType == EntityType.SENTINEL:
            print("[Builder] Attack sentinel already standing at", pos)
            Builder.isAttackRoute = False
            Builder.setScoutTarget(ct)
            Builder.nearestNode = None
            return

        if ct.can_destroy(pos):
            ct.destroy(pos)

        if ct.can_build_sentinel(pos, face_dir):
            ct.build_sentinel(pos, face_dir)
            Builder.updateTile(ct,pos,currLoc,None)
            print("[Builder] Attack sentinel placed at", pos, "facing", face_dir)
            Builder.isAttackRoute = False
            Builder.setScoutTarget(ct)
            Builder.nearestNode = None
        else:
            if currLoc == pos:
                currLoc = Builder.nav.moveRandomly()
            elif currLoc.distance_squared(pos) > GameConstants.ACTION_RADIUS_SQ:
                Builder.nav.moveTo(pos)

    @staticmethod
    def is_tile_covered_by_launcher(ct, pos):
        for d in Constants.DIRECTIONS:
            checkLoc = pos.add(d)
            if not Builder.nav.onMap(checkLoc): continue
            b = Builder.nav.getBuilding(checkLoc)
            if b != 0 and b.team == ct.get_team() and b.entityType == EntityType.LAUNCHER:
                return True
        return False

    @staticmethod
    def updateTile(ct, tile, currLoc, nearestOreDist, logic = False):
        if not Builder.nav.onMap(tile):
            return nearestOreDist
        if not ct.is_in_vision(tile):
            return nearestOreDist
        i = -1
        env = Environment(ct.get_tile_env(tile))
        isOre = False
        match env:
            case Environment.EMPTY:
                i = Constants.tiles.EMPTY
            case Environment.WALL:
                i = Constants.tiles.WALL
            case Environment.ORE_TITANIUM:
                i = Constants.tiles.ORE_TITANIUM
                isOre = True
            case Environment.ORE_AXIONITE:
                i = Constants.tiles.ORE_AXIONITE
                isOre = True
            case _:
                i = Constants.tiles.UNKNOWN

        if (Builder.nav.encodeTile(tile, i)
                and Builder.state not in[Constants.states.ROUTE_CONVEYOR, Constants.states.BUILD_FOUNDRY,Constants.states.BUILD_SPLITTER]) and logic and not Builder.healFlag:
            Builder.setScoutTarget(ct)

        buildingID = ct.get_tile_building_id(tile)
        if buildingID is not None:
            building = Building(ct, buildingID, tile)
            Builder.nav.encodeBuilding(tile, building)
            if logic:
                if(building.entityType == EntityType.CORE and building.team != ct.get_team()):
                    Builder.weSawCore = True
                if isOre and not Builder.healFlag:
                    nearestOreDist = goNearestOre(currLoc, tile, nearestOreDist, ct, building)
                if building.team == ct.get_team() and building.entityType in Constants.ROUTING + Constants.TURRETS and building.hp < building.max_hp and not Builder.healFlag:
                    Builder.healFlag = True
                    Builder.targLoc = building.position
                    print("WE NEED HEAL")
        else:
            Builder.nav.encodeBuilding(tile, 0)
            if logic and isOre and not Builder.healFlag:
                nearestOreDist = goNearestOre(currLoc, tile, nearestOreDist, ct)

        bot = ct.get_tile_builder_bot_id(tile)
        if bot is not None and bot != ct.get_id():
            Builder.nav.botsMap[tile.y * ct.get_map_width() + tile.x] = bot
            Builder.nav.bots.append(bot)
        return nearestOreDist
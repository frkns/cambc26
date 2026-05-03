from cambc import Team, EntityType, Direction, Position, ResourceType, Environment, GameConstants, GameError, Controller
import random
import heapq
import array
import time
import math
import sys
from collections import deque, defaultdict
from typing import NamedTuple
from enum import Enum
import traceback
from itertools import chain
from Awubot import *
from Generated import *

class Builder(Unit):

    state: str
    mode: int = 0
    role: int = 0
    min_dist_to_a_core: int

    is_routing_active: bool = False
    route_from_pos: Position

    should_fire: bool

    @classmethod
    def init(cls):
        Unit.init()
        Explore.init()
        DarkForest.init()
        BfsBureau.enclosed_init()
        cls.state = 'Explore'

        # if Globals.round == 5:
        #     cls.role = 1

    @classmethod
    def start_turn(cls):
        Unit.start_turn()

        my_pos = Globals.my_pos
        cls.min_dist_to_a_core = min(my_pos.distance_squared(Unit.core_pos), my_pos.distance_squared(Symmetry.enemy_core_pos))

        
        DarkForest.fcompute()
        

        
        FoundryInputTracker.compute()
        

        
        BfsBureau.update()
        

        Symmetry.run_sym_check()

        if cls.mode == 0:
            """
            if Globals.round in [4,5]:
                cls.mode = 2
                Explore.target = Explore.new_target()
            """

            if Globals.round in [3]:
                cls.mode = 3
                Explore.target = Explore.new_target()
            else:
                cls.mode = 1
        if cls.mode != 2 and cls.mode != 3 and (Globals.my_id % 3 == 0 and BuildManager.can_afford_sentinel() and MarketMaker.est_income >= 40 and Globals.round > 100):
            cls.mode = 2
            Explore.target = Explore.new_target()
        if cls.mode == 3 and Globals.round >= Constants.HEAL_OVER:
            cls.mode = 1
            Explore.target = Explore.new_target()
        print("Mode:", cls.mode)


        
        BfsBureau.bfs20()
        

        
        BfsBureau.update_enclosed_regions()
        


        
        OreExecutive.fill()
        

        
        VisionTracker.fill()
        

        
        SitterTakedown.fill()
        

        
        HarvesterAdjacent.fill()
        

        
        HealTargeter.fill()
        

        cls.is_routing_active = False

        if RouteToCore.is_active:
            cls.is_routing_active = True
            cls.route_from_pos = RouteToCore.from_pos
        if RouteToBreach.is_active:
            cls.is_routing_active = True
            cls.route_from_pos = RouteToBreach.from_pos
        if RouteToFoundry.is_active:
            cls.is_routing_active = True
            cls.route_from_pos = RouteToFoundry.from_pos

        cls.should_fire = Attacker.should_fire(Globals.my_pos)



    @classmethod
    def run_turn(cls):
        cls.state, *args = cls.determine_state()


        
        globals()[f'State{cls.state}'].run(*args)
        


    @classmethod
    def end_turn(cls):
        Unit.end_turn()

        
        HealExecutor.execute_heal_attempt()
        

        
        Marker.attempt_mark()
        


        # BfsBureau.debug_bfs20_dist_adj()
        # BfsBureau.debug_enemy_launcher_zone()
        # BfsBureau.debug_ally_launcher_zone()

        # if Globals.round & 1:
        #     BfsBureau.debug_now_passable_int_impassable()
        # else:
        #     BfsBureau.debug_now_weight_inf()

        # my_pos = Globals.my_pos
        # if Globals.ct.can_fire(my_pos) and Attacker.should_fire(my_pos) and Map.num_enemies == 0:
        #     Globals.ct.fire(my_pos)

        RoadspamExecutor.execute_roadspam_attempt()




    @classmethod
    def determine_state(cls):
        my_pos = Globals.my_pos
        ct = Globals.ct

        healinfo = HealTargeter.get_best_target_info()
        healpos = None
        if healinfo is not None:
            if healinfo.entity_type == EntityType.CORE:
                healpos = Unit.core_pos
            else:
                healpos = healinfo.position

        takedowninfo = HarvesterAdjacent.get_best_turret_takedown_info()
        takedownpos = None if takedowninfo is None else takedowninfo.position

        misinfo: TransporterInfo = VisionTracker.get_best_misrouted_target()

        # now changed to sentinel/gunner pos near enemy?
        sentinelpos = HarvesterAdjacent.get_best_sentinel_position()

        destroypos = VisionTracker.get_best_destroy_position()

        if destroypos is not None:
            return 'Destroy', destroypos


        if (
             HealExecutor.last_healed is not None
             and HealExecutor.last_healed.is_turret
             and (Globals.round - HealExecutor.last_healed_round) <= 5
             # and misinfo is None  already fixed by healpos check
        ):
            if healpos is not None:  # redundant, OK
                return 'MoveTo', healpos, '[lrh: move to heal]'

        if takedownpos is not None:
            Debug.dot(takedownpos, Color.PURPLE)
            return 'BuildGunner', takedownpos, None

        sitterpos = SitterTakedown.get_best_launcher_position()
        if sitterpos is not None:
            Debug.dot(sitterpos, Color.PURPLE)
            return 'BuildLauncher', sitterpos

        if healpos is not None and misinfo is None:
            return 'MoveTo', healpos, 'Heal'

        if misinfo is not None: # and not ((RouteToCore.backTracking or RouteToFoundry.backTracking) and not RouteToCore.is_active and not RouteToFoundry.is_active):
            if misinfo.on_ally_side:
                return 'Reroute', misinfo.position
            else:
                return 'Reroute', misinfo.position  # same


        buildingFirstConveyor = (RouteToCore.is_active and len(RouteToCore.prevRoute) == 0) or (RouteToFoundryInput.is_active and len(RouteToFoundryInput.prevRoute) == 0)

        if not buildingFirstConveyor and sentinelpos is None:
            shieldpos = HarvesterAdjacent.get_best_shield_position()
            if shieldpos is not None:
                return 'BuildShield', shieldpos


        attackpos = Attacker.get_target()
        secondaryattackpos = Attacker.get_secondary_target()

        # preroute here
        if cls.is_routing_active and secondaryattackpos == cls.route_from_pos:
            return 'Attack', secondaryattackpos, 'Preroute'

        if RouteToBreach.is_active:
            return ('RouteBreach',)

        if RouteToFoundry.is_active:
            return ('RouteFoundry',)

        if RouteToFoundryInput.is_active:
            return ('RouteFoundryInput',)

        if RouteToCore.is_active:
            return ('Route',)



        trans: TransporterInfo = ConnectManager.get_connect_target_info()
        if trans is not None:
            tpos = trans.target

            if Util.dist_sq(tpos, Symmetry.enemy_core_pos) \
                    < Util.dist_sq(tpos, Unit.core_pos) or not trans.ti.is_building_ally:
                return 'BuildTurret', tpos

            if tpos not in RouteToCore.killed:
                RouteToCore.set_pos(tpos)
                return 'MoveTo', tpos, 'InitRoute'

        route_pos = HarvesterAdjacent.get_best_route_position()
        if route_pos is not None and cls.mode != 2:
            if Util.dist_sq(route_pos, Symmetry.enemy_core_pos) \
                    < Util.dist_sq(route_pos, Unit.core_pos):

                # if sentinelpos is not None:
                #     return 'BuildTurret', sentinelpos, None
                pass

            elif route_pos not in RouteToCore.killed:
                
                RouteToCore.set_pos(route_pos)
                return 'MoveTo', route_pos, 'InitRoute'


        if sentinelpos is not None:
            Debug.dot(sentinelpos, Color.PURPLE)
            return 'BuildTurret', sentinelpos, None

        if cls.should_fire:
            return 'Attack', Globals.my_pos, 'ShouldFire'

        if buildingFirstConveyor:
            shieldpos = HarvesterAdjacent.get_best_shield_position()
            if shieldpos is not None:
                return 'BuildShield', shieldpos


        breach_target = BreachBuild._pick_target()
        if breach_target is not None:
            return 'BreachBuild', breach_target

        foundry_target = FoundryBuild._pick_target()
        if foundry_target is not None:
            return 'FoundryBuild', foundry_target

        if attackpos is not None:
            return 'Attack', attackpos, 'Primary'

        # Attack if position is next to route
        if secondaryattackpos is not None:
            # Compare position to tip of route
            close_to_tip = False
            if RouteToCore.is_active:
                if len(RouteToCore.prevRoute) > 0:
                    close_to_tip = RouteToCore.prevRoute[-1].distance_squared(secondaryattackpos) < 2
            elif RouteToFoundry.is_active:
                if len(RouteToFoundry.prevRoute) > 0:
                    close_to_tip = RouteToFoundry.prevRoute[-1].distance_squared(secondaryattackpos) < 2
            elif RouteToBreach.is_active:
                if len(RouteToBreach.prevRoute) > 0:
                    close_to_tip = RouteToBreach.prevRoute[-1].distance_squared(secondaryattackpos) < 2

            # Attack if close to tip
            if close_to_tip:
                return 'Attack', secondaryattackpos, 'Secondary'

        ax_target = OreExecutive.get_axionite_target()
        ti_target = OreExecutive.get_titanium_target()
        stalk_target = StalkTargeter.get_best_target()

        dist_ti = 1000000 if ti_target is None else my_pos.distance_squared(ti_target)
        dist_ax = 1000000 if ax_target is None else my_pos.distance_squared(ax_target)
        dist_stalk = 1000000 if stalk_target is None else my_pos.distance_squared(stalk_target)

        if my_pos.distance_squared(Symmetry.enemy_core_pos) > my_pos.distance_squared(Unit.core_pos) or (attackpos is None and cls.mode != 2):
            if (dist_stalk <= 4 or (dist_stalk < dist_ti and dist_stalk < dist_ax)):
                return 'MoveTo', stalk_target, 'Stalk'

        if ax_target is not None and MarketMaker.ax == 0 and cls.mode != 2:
            return 'BuildHarvesterAx', ax_target

        if ti_target is not None and cls.mode != 2:
            return 'BuildHarvester', ti_target

        if ax_target is not None and cls.mode != 2:
            return 'BuildHarvesterAx', ax_target

        if my_pos.distance_squared(Symmetry.enemy_core_pos) > my_pos.distance_squared(Unit.core_pos) or (attackpos is None and cls.mode != 2):
            if stalk_target is not None:
                return 'MoveTo', stalk_target, 'Stalk'

        if secondaryattackpos is not None:
            return 'Attack', secondaryattackpos, 'secondary'

        rushTarget = RushTargeter.get_best_target()
        if rushTarget is not None:
            return 'Rush', rushTarget

        if ct.get_unit_count() < 15 or Globals.my_id % 3 == 1:
            patrolTarget = PatrolTargeter.get_best_target()
            if patrolTarget is not None:
                return 'MoveTo', patrolTarget, 'Patrol'

        return 'MoveTo', Explore.get_target(), 'Explore'
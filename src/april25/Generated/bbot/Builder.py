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

    @classmethod
    def init(cls):
        Unit.init()
        Explore.init()
        DarkForest.init()
        BfsBureau.enclosed_init()
        cls.state = 'Explore'
        if Globals.round == 5:
            cls.role = 1

    @classmethod
    def start_turn(cls):
        Unit.start_turn()

        Profiler.start()
        DarkForest.fcompute()
        Profiler.end(f"""DarkForest.fcompute""")

        Profiler.start()
        BfsBureau.update()
        Profiler.end(f"""BfsBureau.update""")

        Symmetry.run_sym_check()

        if cls.mode == 0:
            if Globals.round in [2,3]:
                cls.mode = 2
                Explore.target = Explore.new_target()
            elif Globals.round in [3]:
                cls.mode = 3
                Explore.target = Explore.new_target()
            else:
                cls.mode = 1
        if Globals.round >= Constants.RUSH_OVER:
            cls.mode = 1
            Explore.target = Explore.new_target()
        """
        if (cls.mode == 2 and Symmetry.is_sym_known and Globals.my_pos.distance_squared(Symmetry.enemy_core_pos) <= 36):
            cls.mode = 1
            Explore.target = Explore.new_target()
        """
        print("Mode:", cls.mode)


        Profiler.start()
        BfsBureau.bfs20()
        Profiler.end(f"""BfsBureau.bfs20""")

        Profiler.start()
        BfsBureau.update_enclosed_regions()
        Profiler.end(f"""BfsBureau.update_enclosed_regions""")


        Profiler.start()
        OreExecutive.fill()
        Profiler.end(f"""OreExecutive.fill""")

        Profiler.start()
        VisionTracker.fill()
        Profiler.end(f"""VisionTracker.fill""")

        Profiler.start()
        SitterTakedown.fill()
        Profiler.end(f"""SitterTakedown.fill""")

        Profiler.start()
        HarvesterAdjacent.fill()
        Profiler.end(f"""HarvesterAdjacent.fill""")

        Profiler.start()
        HealTargeter.fill()
        Profiler.end(f"""HealTargeter.fill""")



    @classmethod
    def run_turn(cls):
        cls.state, *args = cls.determine_state()

        print(f'running: {cls.state}  @', *args, sep=' ')

        Profiler.start()
        globals()[f'State{cls.state}'].run(*args)
        Profiler.end(f"""State{cls.state}""")


    @classmethod
    def end_turn(cls):
        Unit.end_turn()

        Profiler.start()
        HealExecutor.execute_heal_attempt()
        Profiler.end(f"""HealExecutor.execute_heal_attempt""")

        Profiler.start()
        Marker.attempt_mark()
        Profiler.end(f"""Marker.attempt_mark""")

        if cls.mode == 3:
            RoadspamExecutor.execute_roadspam_attempt()

        # BfsBureau.debug_bfs20_dist_adj()
        # BfsBureau.debug_enemy_launcher_zone()
        # if Globals.round & 1:
        #     BfsBureau.debug_now_passable_int_impassable()
        # else:
        #     BfsBureau.debug_now_weight_inf()

        my_pos = Globals.my_pos
        if Globals.ct.can_fire(my_pos) and Attacker.should_fire(my_pos) and Map.num_enemies == 0:
            Globals.ct.fire(my_pos)
        
        if my_pos.distance_squared(Symmetry.enemy_core_pos) < my_pos.distance_squared(Unit.core_pos) and Map.num_enemies > 0:
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
        
        if RouteToBreach.is_active:
            return ('RouteBreach',)

        if takedownpos is not None:
            Debug.dot(takedownpos, Color.PURPLE)
            return 'BuildGunner', takedownpos, None


        sitterpos = SitterTakedown.get_best_launcher_position()
        if sitterpos is not None:
            Debug.dot(sitterpos, Color.PURPLE)
            return 'BuildLauncher', sitterpos


        if healpos is not None:
            return 'MoveTo', healpos, 'Heal'

        if (
             HealExecutor.last_healed is not None 
             and HealExecutor.last_healed.is_turret
             and (Globals.round - HealExecutor.last_healed_round) <= 5
        ):
            if healpos is not None:  # redundant, OK
                return 'MoveTo', healpos, '[lrh: move to heal]'
            return 'MoveTo', HealExecutor.last_healed.position, '[lrh: wait for heal]'

        if cls.role == 1:
            return 'MoveTo', Unit.core_pos, '[core healer]'
            
        buildingFirstConveyor = RouteToCore.is_active and len(RouteToCore.prevRoute) == 0
            
        if not buildingFirstConveyor:
            shieldpos = HarvesterAdjacent.get_best_shield_position()
            if shieldpos is not None:
                return 'BuildShield', shieldpos
                
        attackpos = Attacker.get_target()
        secondaryattackpos = Attacker.get_secondary_target()
        
        if secondaryattackpos is not None and (RouteToCore.is_active or RouteToFoundry.is_active or RouteToBreach.is_active):
            if Globals.my_pos.distance_squared(secondaryattackpos) <= 2:
                return 'Attack', secondaryattackpos

        if RouteToFoundry.is_active:
            return ('RouteFoundry',)

        if RouteToCore.is_active:
            return ('Route',)

        if misinfo is not None and not (RouteToCore.backTracking or RouteToFoundry.backTracking and not RouteToCore.is_active and not RouteToFoundry.is_active):
            if misinfo.on_ally_side:
                return 'Reroute', misinfo.position
            else:
                return 'Reroute', misinfo.position  # same

        if sentinelpos is not None:
            Debug.dot(sentinelpos, Color.PURPLE)
            return 'BuildTurret', sentinelpos, None
            
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

        trans: TransporterInfo = ConnectManager.get_connect_target_info()
        if trans is not None:
            tpos = trans.target

            if Util.dist_sq(tpos, Symmetry.enemy_core_pos) \
                    < Util.dist_sq(tpos, Unit.core_pos) \
                    and BfsBureau.bfs20_dist_adj[(((tpos.x) + 3) * 56 + ((tpos.y) + 3))] < 100:
                return 'BuildTurret', tpos 

            if tpos not in RouteToCore.killed:
                RouteToCore.set_pos(tpos)
                return 'MoveTo', tpos, 'InitRoute'
        
        if attackpos is not None:
            return 'Attack', attackpos
                
        ax_target = OreExecutive.get_axionite_target()
        ti_target = OreExecutive.get_titanium_target()
        stalk_target = StalkTargeter.get_best_target()

        dist_ti = 1000000 if ti_target is None else my_pos.distance_squared(ti_target)
        dist_ax = 1000000 if ax_target is None else my_pos.distance_squared(ax_target)
        dist_stalk = 1000000 if stalk_target is None else my_pos.distance_squared(stalk_target)

        if (dist_stalk <= 4 or (dist_stalk < dist_ti and dist_stalk < dist_ax)) and cls.mode != 2:
            return 'MoveTo', stalk_target, 'Stalk'

        if ax_target is not None and MarketMaker.ax == 0 and cls.mode != 2:
            return 'BuildHarvesterAx', ax_target

        if ti_target is not None and cls.mode != 2:
            return 'BuildHarvester', ti_target

        if ax_target is not None and cls.mode != 2:
            return 'BuildHarvesterAx', ax_target

        route_pos = HarvesterAdjacent.get_best_route_position()
        if route_pos is not None and cls.mode != 2:
            RouteToCore.set_pos(route_pos)
            if RouteToCore.is_active:
                print("""[HarvesterAdjacent found route]""")
                return ('Route',)

        if stalk_target is not None and cls.mode != 2:
            return 'MoveTo', stalk_target, 'Stalk'

        if secondaryattackpos is not None:
            return 'Attack', secondaryattackpos
            
        rushTarget = RushTargeter.get_best_target()
        if rushTarget is not None:
            return 'Rush', rushTarget

        if ct.get_unit_count() < 15 or Globals.my_id % 3 == 0:
            patrolTarget = PatrolTargeter.get_best_target()
            if patrolTarget is not None:
                return 'MoveTo', patrolTarget, 'Patrol'

        return 'MoveTo', Explore.get_target(), 'Explore'
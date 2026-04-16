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

    @classmethod
    def init(cls):
        Unit.init()
        Explore.init()
        DarkForest.init()
        cls.state = 'Explore'


    @classmethod
    def start_turn(cls):
        Unit.start_turn()

        
        DarkForest.fcompute()
        

        
        BfsBureau.update()
        

        Symmetry.run_sym_check()

        if cls.mode == 0:
            if Globals.round in [4,5]:
                cls.mode = 2
                Explore.target = Explore.new_target()
            else:
                cls.mode = 1
        if Globals.round >= Constants.RUSH_OVER:
            cls.mode = 1
            Explore.target = Explore.new_target()
        if (cls.mode == 2 and Symmetry.is_sym_known and Globals.my_pos.distance_squared(Symmetry.enemy_core_pos) <= 36):
            cls.mode = 1
            Explore.target = Explore.new_target()
        print("Mode:", cls.mode)


        
        BfsBureau.bfs20()
        

        
        OreExecutive.fill()
        

        
        VisionTracker.fill()
        

        
        SitterTakedown.fill()
        

        
        HarvesterAdjacent.fill()
        

        
        HealTargeter.fill()
        



    @classmethod
    def run_turn(cls):
        cls.state, *args = cls.determine_state()


        globals()[f'State{cls.state}'].run(*args)


    @classmethod
    def end_turn(cls):
        Unit.end_turn()

        
        HealExecutor.execute_heal_attempt()
        

        
        Marker.attempt_mark()
        



    @classmethod
    def determine_state(cls):
        my_pos = Globals.my_pos

        healinfo = HealTargeter.get_best_target_info()
        healpos = None if healinfo is None else healinfo.position

        takedowninfo = HarvesterAdjacent.get_best_turret_takedown_info()
        takedownpos = None if takedowninfo is None else takedowninfo.position
        
        """
        if RouteToBreach.is_active:
            return ('RouteBreach',)
        """

        if takedownpos is not None:
            Debug.dot(takedownpos, Color.PURPLE)
            return 'BuildGunner', takedownpos, None
            

        sentinelpos = HarvesterAdjacent.get_best_sentinel_position()
        if sentinelpos is not None:
            Debug.dot(sentinelpos, Color.PURPLE)
            return 'BuildSentinel', sentinelpos, None

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
            
        buildingFirstConveyor = RouteToCore.is_active and len(RouteToCore.prevRoute) == 0
            
        if not buildingFirstConveyor:
            shieldpos = HarvesterAdjacent.get_best_shield_position()
            if shieldpos is not None:
                return 'BuildShield', shieldpos

        if RouteToFoundry.is_active:
            return ('RouteFoundry',)

        if RouteToCore.is_active:
            return ('Route',)
            
        if buildingFirstConveyor:
            shieldpos = HarvesterAdjacent.get_best_shield_position()
            if shieldpos is not None:
                return 'BuildShield', shieldpos

        """
        breach_target = BreachBuild._pick_target()
        if breach_target is not None:
            return 'BreachBuild', breach_target
        """
        
        foundry_target = FoundryBuild._pick_target()
        if foundry_target is not None:
            return 'FoundryBuild', foundry_target


        trans: TransporterInfo = ConnectManager.get_connect_target_info()
        if trans is not None:
            tpos = trans.target

            if Util.dist_sq(tpos, Symmetry.enemy_core_pos) \
                    < Util.dist_sq(tpos, Unit.core_pos) \
                    and BfsBureau.bfs20_dist[(((tpos.x) + 3) * 56 + ((tpos.y) + 3))] < 100:
                return 'BuildSentinel', tpos 

            if tpos not in RouteToCore.killed:
                RouteToCore.set_pos(tpos)
                return 'MoveTo', tpos, 'InitRoute'

        apos = Attacker.get_target()
        if apos is not None:
            return 'Attack', apos

        ax_target = OreExecutive.get_axionite_target()
        ti_target = OreExecutive.get_titanium_target()
        stalk_target = StalkTargeter.get_best_target()

        dist_ti = 1000000 if ti_target is None else my_pos.distance_squared(ti_target)
        dist_ax = 1000000 if ax_target is None else my_pos.distance_squared(ax_target)
        dist_stalk = 1000000 if stalk_target is None else my_pos.distance_squared(stalk_target)

        if dist_stalk <= 4 or (dist_stalk < dist_ti and dist_stalk < dist_ax):
            return 'MoveTo', stalk_target, 'Stalk'

        if ti_target is not None and cls.mode != 2:
            return 'BuildHarvester', ti_target

        if ax_target is not None and cls.mode != 2:
            return 'BuildHarvesterAx', ax_target

        route_pos = HarvesterAdjacent.get_best_route_position()
        if route_pos is not None and cls.mode != 2:
            RouteToCore.set_pos(route_pos)
            return ('Route',)

        if stalk_target is not None:
            return 'MoveTo', stalk_target, 'Stalk'

        rushTarget = RushTargeter.get_best_target()
        if rushTarget is not None:
            return 'MoveTo', rushTarget, 'Rush'

        patrolTarget = PatrolTargeter.get_best_target()
        if patrolTarget is not None:
            return 'MoveTo', patrolTarget, 'Patrol'

        return 'MoveTo', Explore.get_target(), 'Explore'
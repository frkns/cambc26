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

    @classmethod
    def init(cls):
        Unit.init()
        Explore.init()
        DarkForest.init()
        cls.state = 'Explore'


    @classmethod
    def start_turn(cls):
        Unit.start_turn()

        Profiler.start()
        DarkForest.fcompute()
        Profiler.end("""DarkForest.fcompute""")

        Profiler.start()
        BfsBureau.update()
        Profiler.end("""BfsBureau.update""")

        Symmetry.run_sym_check()

        DarkForest.debug_kind()

        Profiler.start()
        BfsBureau.bfs20()
        Profiler.end("""BfsBureau.bfs20""")

        Profiler.start()
        OreExecutive.fill()
        Profiler.end("""OreExecutive.fill""")

        Profiler.start()
        VisionTracker.fill()
        Profiler.end("""VisionTracker.fill""")

        Profiler.start()
        TurretTakedown.fill()
        Profiler.end("""TurretTakedown.fill""")

        Profiler.start()
        SitterTakedown.fill()
        Profiler.end("""SitterTakedown.fill""")

        Profiler.start()
        HarvesterAdjacent.fill()
        Profiler.end("""HarvesterAdjacent.fill""")

        Profiler.start()
        HealTargeter.fill()
        Profiler.end("""HealTargeter.fill""")

        Profiler.start()
        ShieldTargeter.fill()
        Profiler.end("""ShieldTargeter.fill""")

        Symmetry.debug()



    @classmethod
    def run_turn(cls):
        cls.state, *args = cls.determine_state()

        print(f'running: {cls.state}  @', *args, sep=' ')

        globals()[f'State{cls.state}'].run(*args)


    @classmethod
    def end_turn(cls):
        Unit.end_turn()

        Profiler.start()
        HealExecutor.execute_heal_attempt()
        Profiler.end("""HealExecutor.execute_heal_attempt""")

        Profiler.start()
        Marker.attempt_mark()
        Profiler.end("""Marker.attempt_mark""")



    @classmethod
    def determine_state(cls):
        my_pos = Globals.my_pos

        """
        if RouteToBreach.is_active:
            return ('RouteBreach',)
        """
        if RouteToFoundry.is_active:
            return ('RouteFoundry',)

        if RouteToCore.is_active:
            return ('Route',)

        takedownpos = TurretTakedown.get_best_hijack_position()
        if takedownpos is not None:
            Debug.dot(takedownpos, Color.PURPLE)
            return 'BuildGunner', takedownpos, None
            
        sitterpos = SitterTakedown.get_best_hijack_position()
        if sitterpos is not None:
            Debug.dot(sitterpos, Color.PURPLE)
            return 'BuildLauncherAround', sitterpos

        hpos = HarvesterAdjacent.get_best_hijack_position()
        if hpos is not None:
            Debug.dot(hpos, Color.PURPLE)
            return 'BuildTurret', hpos, None

        healpos = HealTargeter.get_best_target()
        if healpos is not None:
            return 'MoveTo', healpos, 'Heal'
        """
        breach_target = BreachBuild._pick_target()
        if breach_target is not None:
            return 'BreachBuild', breach_target
        """
        foundry_target = FoundryBuild._pick_target()
        if foundry_target is not None:
            return 'FoundryBuild', foundry_target

        # shieldpos = ShieldTargeter.get_best_target()
        # if shieldpos is not None:
        #     return 'BuildBarrier', shieldpos, None

        trans: TransporterInfo = ConnectManager.get_connect_target_info()
        if trans is not None:
            tpos = trans.target

            if Util.dist_sq(tpos, Symmetry.enemy_core_pos) \
                    < Util.dist_sq(tpos, Unit.core_pos) \
                    and BfsBureau.bfs20_dist[(((tpos.x) + 3) * 56 + ((tpos.y) + 3))] < 100:
                return 'BuildTurret', tpos, None if trans.is_bridge else trans.target.direction_to(tpos)

            if tpos not in RouteToCore.killed:
                RouteToCore.set_pos(tpos)
                return 'MoveTo', tpos, 'InitRoute'

        apos = Attacker.get_trans_target()
        if apos is not None:
            return 'AttackTransporter', apos

        ax_target = OreExecutive.get_axionite_target()
        ti_target = OreExecutive.get_titanium_target()
        stalk_target = StalkTargeter.get_best_target()

        dist_stalk = 1000000 if stalk_target is None else my_pos.distance_squared(stalk_target)
        dist_ti = 1000000 if ti_target is None else my_pos.distance_squared(ti_target)
        dist_ax = 1000000 if ax_target is None else my_pos.distance_squared(ax_target)

        if dist_stalk < dist_ti and dist_stalk < dist_ax:
            return 'MoveTo', stalk_target, 'Stalk'

        if ax_target is not None:
            return 'BuildHarvesterAx', ax_target

        if ti_target is not None:
            return 'BuildHarvester', ti_target

        if stalk_target is not None:
            return 'MoveTo', stalk_target, 'Stalk'

        rushTarget = RushTargeter.get_best_target()
        if rushTarget is not None:
            return 'MoveTo', rushTarget, 'Rush'

        patrolTarget = PatrolTargeter.get_best_target()
        if patrolTarget is not None:
            return 'MoveTo', patrolTarget, 'Patrol'

        return 'MoveTo', Explore.get_target(), 'Explore'

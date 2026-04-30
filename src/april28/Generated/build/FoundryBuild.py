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

class FoundryBuild:
    @classmethod
    def register_foundry(cls, pos: Position):
        encoded = (((pos.x) + 3) * 56 + ((pos.y) + 3))
        if encoded in DarkForest.foundry_positions:
            return  # idempotent — already registered

        print("New foundry at", pos, "— registering in DarkForest")

        # Persist so fcompute can build refined_ax_line every tick.
        DarkForest.foundry_positions.add(encoded)

        # Root this arm of the tree at the foundry (ALLY_CONSUMER sink),
        # so titanium/axionite flow stops here.
        DarkForest.register_sink(encoded, 3)

        # Block RouteToFoundry from routing another bot to the same leaf.
        RouteToFoundry.planned_foundry_positions.add(encoded)

    @classmethod
    def build_foundry(cls, pos):
        encoded = (((pos.x) + 3) * 56 + ((pos.y) + 3))  # fixed: was missing
        print("Trying to build foundry at", pos)
        print("Foundry cost:", Globals.ct.get_foundry_cost()[0])

        ti = Map.tile_info[pos.x][pos.y]
        if not ti.is_building_ally or ti.entity_type == EntityType.FOUNDRY:    
            RouteToFoundry._foundry_target = None
            return

        Pathfinder.move_to(pos, ban_target_pos=True)

        # if Globals.ct.get_global_resources()[0] > Globals.ct.get_foundry_cost()[0] \
        #         and Globals.ct.can_destroy(pos) \
        #         and Globals.ct.get_action_cooldown() == 0:
        #     BuildManager.destroy(pos)
        # if Globals.ct.can_build_foundry(pos):

        if BuildManager.can_dbuild_foundry(pos):
            BuildManager.dbuild_foundry(pos)

            cls.register_foundry(pos)          # fixed: was register_foundry(encoded)

            RouteToFoundry._foundry_target = None
            """
            cand: OrePositionPicker.Candidate = OrePositionPicker.pick_best_candidate(pos)
            if cand is not None and cand.ti.entity_type not in Constants.TRANSPORTERS_SET:
                RouteToBreach.set_pos(cand.position)
            """
            return True
        return False

    @classmethod
    def _pick_target(cls):
        if RouteToFoundry._foundry_target is None:
            return None
        t = ((RouteToFoundry._foundry_target) // 56 - 3), ((RouteToFoundry._foundry_target) % 56 - 3)
        return Position(t[0], t[1])
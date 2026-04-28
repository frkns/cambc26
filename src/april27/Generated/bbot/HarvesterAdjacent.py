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

# for choosing build position

class AdjacentInfo:
    __slots__ = (
        'position', 'bfs_dist', 'bfs_dist_adj', 'is_harvester_ally', 'ti',
        'consider_route', 'dist_to_ally_core', 'has_ally_transporter',
        'easily_buildable', 'is_canonical_ally_harvester', 'is_working_shield',
        'harvester_ally_turrets_adjacent', 'harvester_enemy_turrets_adjacent',
        'enemy_turrets_adjacent', 'ally_turrets_adjacent',
        'sentinel_dir_info',
        'h_outward_adj',
    )


    @staticmethod
    def is_better_than_shield(a: AdjacentInfo, b: AdjacentInfo):
        ati = a.ti
        bti = b.ti

        if a.is_working_shield != b.is_working_shield:
            return a.is_working_shield < b.is_working_shield

        if bool(a.h_outward_adj) != bool(b.h_outward_adj):
            if a.is_harvester_ally and b.is_harvester_ally:
                return a.h_outward_adj > b.h_outward_adj

        if a.bfs_dist_adj >= 100: return False        
        if b.bfs_dist_adj >= 100: return True
        
        if a.is_canonical_ally_harvester != b.is_canonical_ally_harvester:
            return a.is_canonical_ally_harvester > b.is_canonical_ally_harvester

        if ati.harvester_adjacent != bti.harvester_adjacent:
            return ati.harvester_adjacent > bti.harvester_adjacent

        if a.enemy_turrets_adjacent != b.enemy_turrets_adjacent:
            return a.enemy_turrets_adjacent < b.enemy_turrets_adjacent # Less enemy turrets is better for shield

        return a.bfs_dist_adj < b.bfs_dist_adj



    @staticmethod
    def is_better_than_sentinel(a: AdjacentInfo, b: AdjacentInfo):
        # now is better

        if not a.easily_buildable: return False
        if not b.easily_buildable: return True
            
        if a.bfs_dist_adj >= 100: return False        
        if b.bfs_dist_adj >= 100: return True

        asi: SentinelDirectionInfo = a.sentinel_dir_info
        bsi: SentinelDirectionInfo = b.sentinel_dir_info

        if asi.banned: return False
        if bsi.banned: return True
        
        if asi.enemy_building_hp != bsi.enemy_building_hp:
            return asi.enemy_building_hp > bsi.enemy_building_hp

        if a.is_harvester_ally and (not b.is_harvester_ally): return False
        if (not a.is_harvester_ally) and b.is_harvester_ally: return True

        if asi.enemy_bot_hp != bsi.enemy_bot_hp:
            return asi.enemy_bot_hp > bsi.enemy_bot_hp
        
        ati = a.ti
        bti = b.ti
        
        if ati.has_bot != bti.has_bot:
            return ati.has_bot < bti.has_bot

        return a.bfs_dist_adj < b.bfs_dist_adj


    @staticmethod
    def is_better_than_route(a: AdjacentInfo, b: AdjacentInfo):
        if a.bfs_dist >= 100: return False
        if b.bfs_dist >= 100: return True

        if not a.consider_route: return False
        if not b.consider_route: return True
        
        if a.harvester_ally_turrets_adjacent != b.harvester_ally_turrets_adjacent:
            return a.harvester_ally_turrets_adjacent > b.harvester_ally_turrets_adjacent

        return a.bfs_dist < b.bfs_dist


    @staticmethod
    def is_better_than_turret_takedown(a: AdjacentInfo, b: AdjacentInfo):
        if a.bfs_dist_adj >= 100: return False
        if b.bfs_dist_adj >= 100: return True

        if not a.easily_buildable: return False
        if not b.easily_buildable: return True

        if a.enemy_turrets_adjacent == 0: return False
        if b.enemy_turrets_adjacent == 0: return True
        
        ati = a.ti
        bti = b.ti
        
        if ati.has_bot != bti.has_bot:
            return ati.has_bot < bti.has_bot

        if a.enemy_turrets_adjacent != b.enemy_turrets_adjacent:
            return a.enemy_turrets_adjacent > b.enemy_turrets_adjacent

        if a.has_ally_transporter != b.has_ally_transporter:
            return a.has_ally_transporter < b.has_ally_transporter

        return a.bfs_dist_adj < b.bfs_dist_adj




class HarvesterAdjacent:
    infos: list[AdjacentInfo] = []  # adjacent candidate build positions


    @classmethod
    def get_best_sentinel_position(cls) -> Position | None:

        if not cls.infos:
            return None

        best = cls.infos[0]
        for c in cls.infos[1:]:
            if AdjacentInfo.is_better_than_sentinel(c, best):
                best = c

        # Debug.tee(best.__dict__)

        if not best.easily_buildable:
            return None
        
        if best.bfs_dist_adj >= 100:
            return None

        if best.ti.has_bot:
            return None

        si: SentinelDirectionInfo = best.sentinel_dir_info
        if si.banned:
            return None
        
        ok = (si.enemy_building_hp > 20 and si.enemy_bot_hp > 20) or (si.enemy_building_hp > 40)
        if not ok:
            return None

        if not VisionTracker.me_is_canonical_ally(best.position):
            return None

        return best.position


    @classmethod
    def get_best_turret_takedown_info(cls) -> AdjacentInfo | None:
        if not BuildManager.can_afford_gunner():
            return None

        if not cls.infos:
            return None

        best = cls.infos[0]
        for c in cls.infos[1:]:
            if AdjacentInfo.is_better_than_turret_takedown(c, best):
                best = c

        if not best.easily_buildable:
            return None

        if best.bfs_dist_adj >= 100:
            return None

        if best.enemy_turrets_adjacent == 0:
            return None
        
        if best.ti.has_bot:
            return None
        
        # If we already have turrets, don't break transporters
        if best.ally_turrets_adjacent > 0 and best.has_ally_transporter:
            return None

        if not VisionTracker.me_is_canonical_ally(best.position):
            return None

        return best



    @classmethod
    def get_best_route_position(cls) -> Position | None:
        if not cls.infos:
            return None

        best = cls.infos[0]
        for c in cls.infos[1:]:
            if AdjacentInfo.is_better_than_route(c, best):
                best = c

        if best.consider_route is False:
            return None

        if best.bfs_dist >= 100:
            return None

        if not best.is_canonical_ally_harvester:
            return None

        return best.position


    @classmethod
    def get_best_shield_position(cls) -> Position | None:
        if not cls.infos:
            return None

        best = cls.infos[0]
        for c in cls.infos[1:]:
            if AdjacentInfo.is_better_than_shield(c, best):
                best = c

        if best.is_working_shield: # if there's already a shield at the target
            return None

        if best.is_harvester_ally and best.h_outward_adj == 0:
            return None

        if best.bfs_dist_adj >= 100:
            return None
        
        if best.enemy_turrets_adjacent > 0:
            return None
        
        if not best.is_canonical_ally_harvester:
            return None

        if not VisionTracker.me_is_canonical_ally(best.position):
            return None

        return best.position


    @classmethod
    def fill(cls):
        infos = cls.infos
        infos.clear()

        tile_info = Map.tile_info
        my_pos = Globals.my_pos

        for spos, sx, sy, _, hti in Map.proc_nearby_tiles:
            if hti.entity_type != EntityType.HARVESTER or hti.env == Environment.ORE_AXIONITE:
                continue

            is_harvester_ally = hti.is_building_ally
            consider_route = hti.ally_outward_transporters_adjacent == 0 \
                and hti.enemy_transporters_adjacent == 0 \
                and hti.enemy_turrets_adjacent == 0 \
                and my_pos.distance_squared(spos) <= 15  # can see all adjacent
            dist_to_ally_core = spos.distance_squared(Unit.core_pos)
            is_canonical_ally_harvester = VisionTracker.me_is_canonical_ally(spos)
            

            x, y = sx , sy -1
            ti = tile_info[x][y]
            if ti is not None:
                valid = True
                
                if ti.env == Environment.WALL:
                    valid = False
                elif ti.has_building:
                    if not ti.is_building_ally:
                        valid = False
                    elif ti.entity_type != EntityType.ROAD:
                        if ti.entity_type not in Constants.TRANSPORTERS_SET:
                            valid = False

                if valid:
                    pos = Position(x, y)
                    idx = (((x) + 3) * 56 + ((y) + 3))

                    info = AdjacentInfo()
                    info.position = pos
                    info.bfs_dist_adj = BfsBureau.bfs20_dist_adj[idx]
                    info.bfs_dist = BfsBureau.bfs20_dist[idx]
                    info.is_harvester_ally = is_harvester_ally
                    info.ti = ti
                    info.easily_buildable = (
                        not ti.has_building or
                        (
                            ti.is_building_ally and 
                            (
                                ti.entity_type == EntityType.ROAD 
                                or ti.entity_type == EntityType.BARRIER
                                or ti.entity_type == EntityType.LAUNCHER
                                or (ti.entity_type in Constants.TRANSPORTERS_SET and ti.target == spos)
                            )
                        )
                    ) and not ti.has_bot
                    info.consider_route = consider_route
                    info.dist_to_ally_core = dist_to_ally_core
                    info.is_canonical_ally_harvester = is_canonical_ally_harvester
                    info.is_working_shield = ti.has_building and ti.is_building_ally and (ti.entity_type != EntityType.ROAD or not is_harvester_ally)
                    info.harvester_ally_turrets_adjacent = hti.ally_turrets_adjacent
                    info.harvester_enemy_turrets_adjacent = hti.enemy_turrets_adjacent

                    info.has_ally_transporter = (
                        ti.has_building 
                        and ti.is_building_ally 
                        and ti.entity_type in Constants.TRANSPORTERS_SET
                        and ti.target != spos # not pointing back into the harvester
                    )
                    
                    # if info.has_ally_transporter:
                    #     Debug.dot(pos, Color.LIME)

                    # count nearby turrets in all 8 directions
                    info.enemy_turrets_adjacent = 0
                    info.ally_turrets_adjacent = 0
                    nti = tile_info[x ][y -1]
                    if nti is not None:
                        if nti.has_turret:
                            if nti.is_building_ally:
                                info.ally_turrets_adjacent += 1
                            else:
                                info.enemy_turrets_adjacent += 1
                        # Count enemy launchers as turrets
                        elif nti.has_building and not nti.is_building_ally and nti.entity_type == EntityType.LAUNCHER:
                            info.enemy_turrets_adjacent += 1
                    nti = tile_info[x +1][y -1]
                    if nti is not None:
                        if nti.has_turret:
                            if nti.is_building_ally:
                                info.ally_turrets_adjacent += 1
                            else:
                                info.enemy_turrets_adjacent += 1
                        # Count enemy launchers as turrets
                        elif nti.has_building and not nti.is_building_ally and nti.entity_type == EntityType.LAUNCHER:
                            info.enemy_turrets_adjacent += 1
                    nti = tile_info[x +1][y ]
                    if nti is not None:
                        if nti.has_turret:
                            if nti.is_building_ally:
                                info.ally_turrets_adjacent += 1
                            else:
                                info.enemy_turrets_adjacent += 1
                        # Count enemy launchers as turrets
                        elif nti.has_building and not nti.is_building_ally and nti.entity_type == EntityType.LAUNCHER:
                            info.enemy_turrets_adjacent += 1
                    nti = tile_info[x +1][y +1]
                    if nti is not None:
                        if nti.has_turret:
                            if nti.is_building_ally:
                                info.ally_turrets_adjacent += 1
                            else:
                                info.enemy_turrets_adjacent += 1
                        # Count enemy launchers as turrets
                        elif nti.has_building and not nti.is_building_ally and nti.entity_type == EntityType.LAUNCHER:
                            info.enemy_turrets_adjacent += 1
                    nti = tile_info[x ][y +1]
                    if nti is not None:
                        if nti.has_turret:
                            if nti.is_building_ally:
                                info.ally_turrets_adjacent += 1
                            else:
                                info.enemy_turrets_adjacent += 1
                        # Count enemy launchers as turrets
                        elif nti.has_building and not nti.is_building_ally and nti.entity_type == EntityType.LAUNCHER:
                            info.enemy_turrets_adjacent += 1
                    nti = tile_info[x -1][y +1]
                    if nti is not None:
                        if nti.has_turret:
                            if nti.is_building_ally:
                                info.ally_turrets_adjacent += 1
                            else:
                                info.enemy_turrets_adjacent += 1
                        # Count enemy launchers as turrets
                        elif nti.has_building and not nti.is_building_ally and nti.entity_type == EntityType.LAUNCHER:
                            info.enemy_turrets_adjacent += 1
                    nti = tile_info[x -1][y ]
                    if nti is not None:
                        if nti.has_turret:
                            if nti.is_building_ally:
                                info.ally_turrets_adjacent += 1
                            else:
                                info.enemy_turrets_adjacent += 1
                        # Count enemy launchers as turrets
                        elif nti.has_building and not nti.is_building_ally and nti.entity_type == EntityType.LAUNCHER:
                            info.enemy_turrets_adjacent += 1
                    nti = tile_info[x -1][y -1]
                    if nti is not None:
                        if nti.has_turret:
                            if nti.is_building_ally:
                                info.ally_turrets_adjacent += 1
                            else:
                                info.enemy_turrets_adjacent += 1
                        # Count enemy launchers as turrets
                        elif nti.has_building and not nti.is_building_ally and nti.entity_type == EntityType.LAUNCHER:
                            info.enemy_turrets_adjacent += 1

                    info.sentinel_dir_info = ZHolder.banned_sentinel_dir_info
                    info.h_outward_adj = hti.ally_outward_transporters_adjacent
                    infos.append(info)

            x, y = sx +1, sy 
            ti = tile_info[x][y]
            if ti is not None:
                valid = True
                
                if ti.env == Environment.WALL:
                    valid = False
                elif ti.has_building:
                    if not ti.is_building_ally:
                        valid = False
                    elif ti.entity_type != EntityType.ROAD:
                        if ti.entity_type not in Constants.TRANSPORTERS_SET:
                            valid = False

                if valid:
                    pos = Position(x, y)
                    idx = (((x) + 3) * 56 + ((y) + 3))

                    info = AdjacentInfo()
                    info.position = pos
                    info.bfs_dist_adj = BfsBureau.bfs20_dist_adj[idx]
                    info.bfs_dist = BfsBureau.bfs20_dist[idx]
                    info.is_harvester_ally = is_harvester_ally
                    info.ti = ti
                    info.easily_buildable = (
                        not ti.has_building or
                        (
                            ti.is_building_ally and 
                            (
                                ti.entity_type == EntityType.ROAD 
                                or ti.entity_type == EntityType.BARRIER
                                or ti.entity_type == EntityType.LAUNCHER
                                or (ti.entity_type in Constants.TRANSPORTERS_SET and ti.target == spos)
                            )
                        )
                    ) and not ti.has_bot
                    info.consider_route = consider_route
                    info.dist_to_ally_core = dist_to_ally_core
                    info.is_canonical_ally_harvester = is_canonical_ally_harvester
                    info.is_working_shield = ti.has_building and ti.is_building_ally and (ti.entity_type != EntityType.ROAD or not is_harvester_ally)
                    info.harvester_ally_turrets_adjacent = hti.ally_turrets_adjacent
                    info.harvester_enemy_turrets_adjacent = hti.enemy_turrets_adjacent

                    info.has_ally_transporter = (
                        ti.has_building 
                        and ti.is_building_ally 
                        and ti.entity_type in Constants.TRANSPORTERS_SET
                        and ti.target != spos # not pointing back into the harvester
                    )
                    
                    # if info.has_ally_transporter:
                    #     Debug.dot(pos, Color.LIME)

                    # count nearby turrets in all 8 directions
                    info.enemy_turrets_adjacent = 0
                    info.ally_turrets_adjacent = 0
                    nti = tile_info[x ][y -1]
                    if nti is not None:
                        if nti.has_turret:
                            if nti.is_building_ally:
                                info.ally_turrets_adjacent += 1
                            else:
                                info.enemy_turrets_adjacent += 1
                        # Count enemy launchers as turrets
                        elif nti.has_building and not nti.is_building_ally and nti.entity_type == EntityType.LAUNCHER:
                            info.enemy_turrets_adjacent += 1
                    nti = tile_info[x +1][y -1]
                    if nti is not None:
                        if nti.has_turret:
                            if nti.is_building_ally:
                                info.ally_turrets_adjacent += 1
                            else:
                                info.enemy_turrets_adjacent += 1
                        # Count enemy launchers as turrets
                        elif nti.has_building and not nti.is_building_ally and nti.entity_type == EntityType.LAUNCHER:
                            info.enemy_turrets_adjacent += 1
                    nti = tile_info[x +1][y ]
                    if nti is not None:
                        if nti.has_turret:
                            if nti.is_building_ally:
                                info.ally_turrets_adjacent += 1
                            else:
                                info.enemy_turrets_adjacent += 1
                        # Count enemy launchers as turrets
                        elif nti.has_building and not nti.is_building_ally and nti.entity_type == EntityType.LAUNCHER:
                            info.enemy_turrets_adjacent += 1
                    nti = tile_info[x +1][y +1]
                    if nti is not None:
                        if nti.has_turret:
                            if nti.is_building_ally:
                                info.ally_turrets_adjacent += 1
                            else:
                                info.enemy_turrets_adjacent += 1
                        # Count enemy launchers as turrets
                        elif nti.has_building and not nti.is_building_ally and nti.entity_type == EntityType.LAUNCHER:
                            info.enemy_turrets_adjacent += 1
                    nti = tile_info[x ][y +1]
                    if nti is not None:
                        if nti.has_turret:
                            if nti.is_building_ally:
                                info.ally_turrets_adjacent += 1
                            else:
                                info.enemy_turrets_adjacent += 1
                        # Count enemy launchers as turrets
                        elif nti.has_building and not nti.is_building_ally and nti.entity_type == EntityType.LAUNCHER:
                            info.enemy_turrets_adjacent += 1
                    nti = tile_info[x -1][y +1]
                    if nti is not None:
                        if nti.has_turret:
                            if nti.is_building_ally:
                                info.ally_turrets_adjacent += 1
                            else:
                                info.enemy_turrets_adjacent += 1
                        # Count enemy launchers as turrets
                        elif nti.has_building and not nti.is_building_ally and nti.entity_type == EntityType.LAUNCHER:
                            info.enemy_turrets_adjacent += 1
                    nti = tile_info[x -1][y ]
                    if nti is not None:
                        if nti.has_turret:
                            if nti.is_building_ally:
                                info.ally_turrets_adjacent += 1
                            else:
                                info.enemy_turrets_adjacent += 1
                        # Count enemy launchers as turrets
                        elif nti.has_building and not nti.is_building_ally and nti.entity_type == EntityType.LAUNCHER:
                            info.enemy_turrets_adjacent += 1
                    nti = tile_info[x -1][y -1]
                    if nti is not None:
                        if nti.has_turret:
                            if nti.is_building_ally:
                                info.ally_turrets_adjacent += 1
                            else:
                                info.enemy_turrets_adjacent += 1
                        # Count enemy launchers as turrets
                        elif nti.has_building and not nti.is_building_ally and nti.entity_type == EntityType.LAUNCHER:
                            info.enemy_turrets_adjacent += 1

                    info.sentinel_dir_info = ZHolder.banned_sentinel_dir_info
                    info.h_outward_adj = hti.ally_outward_transporters_adjacent
                    infos.append(info)

            x, y = sx , sy +1
            ti = tile_info[x][y]
            if ti is not None:
                valid = True
                
                if ti.env == Environment.WALL:
                    valid = False
                elif ti.has_building:
                    if not ti.is_building_ally:
                        valid = False
                    elif ti.entity_type != EntityType.ROAD:
                        if ti.entity_type not in Constants.TRANSPORTERS_SET:
                            valid = False

                if valid:
                    pos = Position(x, y)
                    idx = (((x) + 3) * 56 + ((y) + 3))

                    info = AdjacentInfo()
                    info.position = pos
                    info.bfs_dist_adj = BfsBureau.bfs20_dist_adj[idx]
                    info.bfs_dist = BfsBureau.bfs20_dist[idx]
                    info.is_harvester_ally = is_harvester_ally
                    info.ti = ti
                    info.easily_buildable = (
                        not ti.has_building or
                        (
                            ti.is_building_ally and 
                            (
                                ti.entity_type == EntityType.ROAD 
                                or ti.entity_type == EntityType.BARRIER
                                or ti.entity_type == EntityType.LAUNCHER
                                or (ti.entity_type in Constants.TRANSPORTERS_SET and ti.target == spos)
                            )
                        )
                    ) and not ti.has_bot
                    info.consider_route = consider_route
                    info.dist_to_ally_core = dist_to_ally_core
                    info.is_canonical_ally_harvester = is_canonical_ally_harvester
                    info.is_working_shield = ti.has_building and ti.is_building_ally and (ti.entity_type != EntityType.ROAD or not is_harvester_ally)
                    info.harvester_ally_turrets_adjacent = hti.ally_turrets_adjacent
                    info.harvester_enemy_turrets_adjacent = hti.enemy_turrets_adjacent

                    info.has_ally_transporter = (
                        ti.has_building 
                        and ti.is_building_ally 
                        and ti.entity_type in Constants.TRANSPORTERS_SET
                        and ti.target != spos # not pointing back into the harvester
                    )
                    
                    # if info.has_ally_transporter:
                    #     Debug.dot(pos, Color.LIME)

                    # count nearby turrets in all 8 directions
                    info.enemy_turrets_adjacent = 0
                    info.ally_turrets_adjacent = 0
                    nti = tile_info[x ][y -1]
                    if nti is not None:
                        if nti.has_turret:
                            if nti.is_building_ally:
                                info.ally_turrets_adjacent += 1
                            else:
                                info.enemy_turrets_adjacent += 1
                        # Count enemy launchers as turrets
                        elif nti.has_building and not nti.is_building_ally and nti.entity_type == EntityType.LAUNCHER:
                            info.enemy_turrets_adjacent += 1
                    nti = tile_info[x +1][y -1]
                    if nti is not None:
                        if nti.has_turret:
                            if nti.is_building_ally:
                                info.ally_turrets_adjacent += 1
                            else:
                                info.enemy_turrets_adjacent += 1
                        # Count enemy launchers as turrets
                        elif nti.has_building and not nti.is_building_ally and nti.entity_type == EntityType.LAUNCHER:
                            info.enemy_turrets_adjacent += 1
                    nti = tile_info[x +1][y ]
                    if nti is not None:
                        if nti.has_turret:
                            if nti.is_building_ally:
                                info.ally_turrets_adjacent += 1
                            else:
                                info.enemy_turrets_adjacent += 1
                        # Count enemy launchers as turrets
                        elif nti.has_building and not nti.is_building_ally and nti.entity_type == EntityType.LAUNCHER:
                            info.enemy_turrets_adjacent += 1
                    nti = tile_info[x +1][y +1]
                    if nti is not None:
                        if nti.has_turret:
                            if nti.is_building_ally:
                                info.ally_turrets_adjacent += 1
                            else:
                                info.enemy_turrets_adjacent += 1
                        # Count enemy launchers as turrets
                        elif nti.has_building and not nti.is_building_ally and nti.entity_type == EntityType.LAUNCHER:
                            info.enemy_turrets_adjacent += 1
                    nti = tile_info[x ][y +1]
                    if nti is not None:
                        if nti.has_turret:
                            if nti.is_building_ally:
                                info.ally_turrets_adjacent += 1
                            else:
                                info.enemy_turrets_adjacent += 1
                        # Count enemy launchers as turrets
                        elif nti.has_building and not nti.is_building_ally and nti.entity_type == EntityType.LAUNCHER:
                            info.enemy_turrets_adjacent += 1
                    nti = tile_info[x -1][y +1]
                    if nti is not None:
                        if nti.has_turret:
                            if nti.is_building_ally:
                                info.ally_turrets_adjacent += 1
                            else:
                                info.enemy_turrets_adjacent += 1
                        # Count enemy launchers as turrets
                        elif nti.has_building and not nti.is_building_ally and nti.entity_type == EntityType.LAUNCHER:
                            info.enemy_turrets_adjacent += 1
                    nti = tile_info[x -1][y ]
                    if nti is not None:
                        if nti.has_turret:
                            if nti.is_building_ally:
                                info.ally_turrets_adjacent += 1
                            else:
                                info.enemy_turrets_adjacent += 1
                        # Count enemy launchers as turrets
                        elif nti.has_building and not nti.is_building_ally and nti.entity_type == EntityType.LAUNCHER:
                            info.enemy_turrets_adjacent += 1
                    nti = tile_info[x -1][y -1]
                    if nti is not None:
                        if nti.has_turret:
                            if nti.is_building_ally:
                                info.ally_turrets_adjacent += 1
                            else:
                                info.enemy_turrets_adjacent += 1
                        # Count enemy launchers as turrets
                        elif nti.has_building and not nti.is_building_ally and nti.entity_type == EntityType.LAUNCHER:
                            info.enemy_turrets_adjacent += 1

                    info.sentinel_dir_info = ZHolder.banned_sentinel_dir_info
                    info.h_outward_adj = hti.ally_outward_transporters_adjacent
                    infos.append(info)

            x, y = sx -1, sy 
            ti = tile_info[x][y]
            if ti is not None:
                valid = True
                
                if ti.env == Environment.WALL:
                    valid = False
                elif ti.has_building:
                    if not ti.is_building_ally:
                        valid = False
                    elif ti.entity_type != EntityType.ROAD:
                        if ti.entity_type not in Constants.TRANSPORTERS_SET:
                            valid = False

                if valid:
                    pos = Position(x, y)
                    idx = (((x) + 3) * 56 + ((y) + 3))

                    info = AdjacentInfo()
                    info.position = pos
                    info.bfs_dist_adj = BfsBureau.bfs20_dist_adj[idx]
                    info.bfs_dist = BfsBureau.bfs20_dist[idx]
                    info.is_harvester_ally = is_harvester_ally
                    info.ti = ti
                    info.easily_buildable = (
                        not ti.has_building or
                        (
                            ti.is_building_ally and 
                            (
                                ti.entity_type == EntityType.ROAD 
                                or ti.entity_type == EntityType.BARRIER
                                or ti.entity_type == EntityType.LAUNCHER
                                or (ti.entity_type in Constants.TRANSPORTERS_SET and ti.target == spos)
                            )
                        )
                    ) and not ti.has_bot
                    info.consider_route = consider_route
                    info.dist_to_ally_core = dist_to_ally_core
                    info.is_canonical_ally_harvester = is_canonical_ally_harvester
                    info.is_working_shield = ti.has_building and ti.is_building_ally and (ti.entity_type != EntityType.ROAD or not is_harvester_ally)
                    info.harvester_ally_turrets_adjacent = hti.ally_turrets_adjacent
                    info.harvester_enemy_turrets_adjacent = hti.enemy_turrets_adjacent

                    info.has_ally_transporter = (
                        ti.has_building 
                        and ti.is_building_ally 
                        and ti.entity_type in Constants.TRANSPORTERS_SET
                        and ti.target != spos # not pointing back into the harvester
                    )
                    
                    # if info.has_ally_transporter:
                    #     Debug.dot(pos, Color.LIME)

                    # count nearby turrets in all 8 directions
                    info.enemy_turrets_adjacent = 0
                    info.ally_turrets_adjacent = 0
                    nti = tile_info[x ][y -1]
                    if nti is not None:
                        if nti.has_turret:
                            if nti.is_building_ally:
                                info.ally_turrets_adjacent += 1
                            else:
                                info.enemy_turrets_adjacent += 1
                        # Count enemy launchers as turrets
                        elif nti.has_building and not nti.is_building_ally and nti.entity_type == EntityType.LAUNCHER:
                            info.enemy_turrets_adjacent += 1
                    nti = tile_info[x +1][y -1]
                    if nti is not None:
                        if nti.has_turret:
                            if nti.is_building_ally:
                                info.ally_turrets_adjacent += 1
                            else:
                                info.enemy_turrets_adjacent += 1
                        # Count enemy launchers as turrets
                        elif nti.has_building and not nti.is_building_ally and nti.entity_type == EntityType.LAUNCHER:
                            info.enemy_turrets_adjacent += 1
                    nti = tile_info[x +1][y ]
                    if nti is not None:
                        if nti.has_turret:
                            if nti.is_building_ally:
                                info.ally_turrets_adjacent += 1
                            else:
                                info.enemy_turrets_adjacent += 1
                        # Count enemy launchers as turrets
                        elif nti.has_building and not nti.is_building_ally and nti.entity_type == EntityType.LAUNCHER:
                            info.enemy_turrets_adjacent += 1
                    nti = tile_info[x +1][y +1]
                    if nti is not None:
                        if nti.has_turret:
                            if nti.is_building_ally:
                                info.ally_turrets_adjacent += 1
                            else:
                                info.enemy_turrets_adjacent += 1
                        # Count enemy launchers as turrets
                        elif nti.has_building and not nti.is_building_ally and nti.entity_type == EntityType.LAUNCHER:
                            info.enemy_turrets_adjacent += 1
                    nti = tile_info[x ][y +1]
                    if nti is not None:
                        if nti.has_turret:
                            if nti.is_building_ally:
                                info.ally_turrets_adjacent += 1
                            else:
                                info.enemy_turrets_adjacent += 1
                        # Count enemy launchers as turrets
                        elif nti.has_building and not nti.is_building_ally and nti.entity_type == EntityType.LAUNCHER:
                            info.enemy_turrets_adjacent += 1
                    nti = tile_info[x -1][y +1]
                    if nti is not None:
                        if nti.has_turret:
                            if nti.is_building_ally:
                                info.ally_turrets_adjacent += 1
                            else:
                                info.enemy_turrets_adjacent += 1
                        # Count enemy launchers as turrets
                        elif nti.has_building and not nti.is_building_ally and nti.entity_type == EntityType.LAUNCHER:
                            info.enemy_turrets_adjacent += 1
                    nti = tile_info[x -1][y ]
                    if nti is not None:
                        if nti.has_turret:
                            if nti.is_building_ally:
                                info.ally_turrets_adjacent += 1
                            else:
                                info.enemy_turrets_adjacent += 1
                        # Count enemy launchers as turrets
                        elif nti.has_building and not nti.is_building_ally and nti.entity_type == EntityType.LAUNCHER:
                            info.enemy_turrets_adjacent += 1
                    nti = tile_info[x -1][y -1]
                    if nti is not None:
                        if nti.has_turret:
                            if nti.is_building_ally:
                                info.ally_turrets_adjacent += 1
                            else:
                                info.enemy_turrets_adjacent += 1
                        # Count enemy launchers as turrets
                        elif nti.has_building and not nti.is_building_ally and nti.entity_type == EntityType.LAUNCHER:
                            info.enemy_turrets_adjacent += 1

                    info.sentinel_dir_info = ZHolder.banned_sentinel_dir_info
                    info.h_outward_adj = hti.ally_outward_transporters_adjacent
                    infos.append(info)

        
        Profiler.start(f"""SentinelDirectionPicker.get_best_info (x5)""")
        sample = random.sample(infos, min(5, len(infos)))
        for info in sample:
            info.sentinel_dir_info = SentinelDirectionPicker.get_best_info(info.position)
        Profiler.end(f"""SentinelDirectionPicker.get_best_info (x5)""")
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

class GunnerTargetInfo:
    __slots__ = (
        'position',         # may be first road
        'target_position', 
        'directly_reachable',
        'has_ally_bot', 'has_enemy_bot', 'has_building',
        'has_turret', 'has_launcher', 'can_shoot_me', 'is_road', 'is_core',
        'bot_hp', 'building_hp', 'iscore', 'ally_connected',
        'current_dir', 'rand_key', 'entity_type',
        'is_harvester_feeding_ally', 'harvester_adjacent',
    )


    @staticmethod
    def is_better_than(a: GunnerTargetInfo, b: GunnerTargetInfo):

        if a.has_ally_bot: return False
        if b.has_ally_bot: return True

        if a.is_harvester_feeding_ally: return False
        if b.is_harvester_feeding_ally: return True

        if a.has_turret and (not b.has_turret): return True
        if (not a.has_turret) and b.has_turret: return False

        if a.has_turret and b.has_turret:
            if a.can_shoot_me and (not b.can_shoot_me): return True
            if (not a.can_shoot_me) and b.can_shoot_me: return False

            a_is_gunner = a.entity_type == EntityType.GUNNER
            b_is_gunner = b.entity_type == EntityType.GUNNER
            if a_is_gunner and (not b_is_gunner): return True
            if (not a_is_gunner) and b_is_gunner: return False


        if a.ally_connected and (not b.ally_connected): return False  # don't target allied routes
        if (not a.ally_connected) and b.ally_connected: return True

        if a.has_building and (not b.has_building): return True
        if (not a.has_building) and b.has_building: return False

        if a.directly_reachable and (not b.directly_reachable): return True
        if (not a.directly_reachable) and b.directly_reachable: return False

        if a.harvester_adjacent and (not b.harvester_adjacent): return True
        if (not a.harvester_adjacent) and b.harvester_adjacent: return False

        # prefer the direction we're currently facing
        if a.current_dir != b.current_dir:
            return a.current_dir > b.current_dir

        if a.is_road and (not b.is_road): return False  # prefer non-roads
        if (not a.is_road) and b.is_road: return True

        if a.has_building and b.has_building:
            if a.building_hp != b.building_hp:
                return a.building_hp < b.building_hp

        # if there is a bot on top of the tile, nothing underneath gets hit
        if a.current_dir == b.current_dir:
            if a.has_enemy_bot and (not b.has_enemy_bot): return True
            if (not a.has_enemy_bot) and b.has_enemy_bot: return False

        if a.has_enemy_bot and b.has_enemy_bot:
            if a.bot_hp != b.bot_hp:
                return a.bot_hp < b.bot_hp
            

        return a.rand_key < b.rand_key



class GunnerSupervisor:
    targets: list[GunnerTargetInfo]

# ---===

    importance_score: dict[EntityType, int] = {
        None: 0,
        EntityType.BUILDER_BOT: 
            0,
        EntityType.CORE: 
            96,
        EntityType.GUNNER: 
            0,
        EntityType.SENTINEL: 
            0,
        EntityType.BREACH: 
            0,
        EntityType.LAUNCHER: 
            0,
        EntityType.CONVEYOR: 
            97,
        EntityType.SPLITTER: 
            100,
        EntityType.ARMOURED_CONVEYOR: 
            95,
        EntityType.BRIDGE: 
            98,
        EntityType.HARVESTER: 
            0,
        EntityType.FOUNDRY: 
            99,
        EntityType.ROAD: 
            0,
        EntityType.BARRIER: 
            0,
        EntityType.MARKER: 
            0,
    }
# ===---

    @classmethod
    def try_fire(cls):
        pos = cls.get_best_target()

        if pos is None or pos == Globals.my_pos:
            print(f'[try_fire] early return since get_best_target is {pos}')
            return

        print(f'[try_fire] OK get_best_target is {pos}')
        Debug.line(pos, Color.TEAL)
        
        ct = Globals.ct
        dirToPos = Globals.my_pos.direction_to(pos)

        if not ct.can_fire_from(Globals.my_pos, dirToPos, EntityType.GUNNER, pos):
            print(f'[try_fire] can_fire_from me to {pos} is False')
            return

        in_coma = not TurretSuicide.has_feeder and not any(TurretSuicide.has_ammo_history)

        if dirToPos != ct.get_direction(): # Rotate if the target isn't in our current direction
            if not in_coma and ct.can_rotate(dirToPos):
                ct.rotate(dirToPos)
        else:
            if ct.can_fire(pos):
                ct.fire(pos)


    @classmethod
    def get_best_target(cls) -> Position | None:
        targets = cls.targets

        if not targets:
            print(f'[get_best_target] (-> None) because there are no targets')
            return None

        best = targets[0]
        for target in targets[1:]:
            if GunnerTargetInfo.is_better_than(target, best):
                best = target

        print(f'[get_best_target] best is {best.position}')

        if best.has_ally_bot:
            return None

        if not best.has_enemy_bot and not best.has_building:
            return None

        if not best.has_enemy_bot and best.ally_connected:
            return None
        

        if best.is_harvester_feeding_ally:
            return None

        return best.position



    @classmethod
    def can_fire_from_through_roads(cls, dir: Direction, target_pos: Position):
        my_pos = Globals.my_pos
        pt = my_pos.add(dir)

        while pt.distance_squared(my_pos) < 13:
            if pt == target_pos: break

            x, y = pt.x, pt.y
            ti = Map.tile_info[x][y]

            if ti is None: break
            if ti.env != Environment.EMPTY: break
            if ti.has_building and not ti.entity_type == EntityType.ROAD: break
            if ti.has_bot: break  # ally and enemy

            pt = pt.add(dir)

        return pt == target_pos


    @classmethod
    def first_road(cls, dir: Direction, target_pos: Position) -> Position:
        my_pos = Globals.my_pos
        pt = my_pos.add(dir)

        while pt.distance_squared(my_pos) < 13:
            if pt == target_pos: break

            x, y = pt.x, pt.y
            ti = Map.tile_info[x][y]

            if ti is None: break
            if ti.env != Environment.EMPTY: break
            if ti.has_building and ti.entity_type == EntityType.ROAD: return pt

            pt = pt.add(dir)

        assert False



    @classmethod
    def fill(cls):
        ct = Globals.ct
        cls.targets = []
        tile_info = Map.tile_info
        my_pos = Globals.my_pos
        
        current_dir = ct.get_direction()

        has_feeder = [False] * 8
        nadj_feeders = 0

        mx, my = my_pos.x, my_pos.y

        ti = tile_info[mx ][my -1]
        if ti is not None:
            if (ti.entity_type == EntityType.HARVESTER and ti.env == Environment.ORE_TITANIUM) or ti.target == my_pos:
                has_feeder[0] = True
                nadj_feeders += 1
        ti = tile_info[mx +1][my ]
        if ti is not None:
            if (ti.entity_type == EntityType.HARVESTER and ti.env == Environment.ORE_TITANIUM) or ti.target == my_pos:
                has_feeder[2] = True
                nadj_feeders += 1
        ti = tile_info[mx ][my +1]
        if ti is not None:
            if (ti.entity_type == EntityType.HARVESTER and ti.env == Environment.ORE_TITANIUM) or ti.target == my_pos:
                has_feeder[4] = True
                nadj_feeders += 1
        ti = tile_info[mx -1][my ]
        if ti is not None:
            if (ti.entity_type == EntityType.HARVESTER and ti.env == Environment.ORE_TITANIUM) or ti.target == my_pos:
                has_feeder[6] = True
                nadj_feeders += 1



        skip = nadj_feeders == 1 and has_feeder[0] and current_dir == Direction.NORTH

        if not skip:
            for pos in ct.get_attackable_tiles_from(my_pos, Direction.NORTH, EntityType.GUNNER):
                if not cls.can_fire_from_through_roads(Direction.NORTH, pos):
                    continue

                # Debug.dot(pos, Color.BLUE if (my_pos.x ^ my_pos.y) & 1 else Color.RED)

                x, y = pos.x, pos.y
                ti = tile_info[x][y]

                if ti is None:
                    continue
                if not ti.has_building:
                    continue
                if ti.is_building_ally:
                    continue


                idx = (((x) + 3) * 56 + ((y) + 3))
                
                info = GunnerTargetInfo()
                info.directly_reachable = ct.can_fire_from(my_pos, Direction.NORTH, EntityType.GUNNER, pos)
                info.position = pos if info.directly_reachable else cls.first_road(Direction.NORTH, pos)
                info.target_position = pos
                info.has_ally_bot = False
                info.has_enemy_bot = False
                info.has_turret = False
                info.has_building = False
                info.has_launcher = False
                info.can_shoot_me = False
                info.iscore = cls.importance_score[ti.entity_type]
                info.entity_type = ti.entity_type
                info.is_road = ti.entity_type == EntityType.ROAD
                info.is_core = ti.entity_type == EntityType.CORE
                info.current_dir = current_dir == Direction.NORTH
                info.rand_key = random.random()
                info.ally_connected = DarkForest.node_kind[idx] in \
                    (1, 3)

                info.is_harvester_feeding_ally = False
                info.harvester_adjacent = ti.harvester_adjacent

                if ti.entity_type == EntityType.HARVESTER:
                    nidx = idx -1
                    if DarkForest.node_kind[nidx] in (1, 3):
                        info.is_harvester_feeding_ally = True
                    nidx = idx +1
                    if DarkForest.node_kind[nidx] in (1, 3):
                        info.is_harvester_feeding_ally = True
                    nidx = idx -56
                    if DarkForest.node_kind[nidx] in (1, 3):
                        info.is_harvester_feeding_ally = True
                    nidx = idx +56
                    if DarkForest.node_kind[nidx] in (1, 3):
                        info.is_harvester_feeding_ally = True

                if ti.has_bot:
                    if ti.is_bot_ally:
                        info.has_ally_bot = True
                    else:
                        info.has_enemy_bot = True
                        info.bot_hp = ti.bot_hp

                if ti.has_building and not ti.is_building_ally:
                    info.has_building = True
                    info.building_hp = ti.building_hp
                    if ti.has_turret:
                        info.has_turret = True
                        info.can_shoot_me = ct.can_fire_from(
                            pos, 
                            ti.turret_direction, 
                            ti.entity_type,
                            Globals.my_pos
                        )

                    elif info.entity_type == EntityType.LAUNCHER:
                        info.has_launcher = True

                cls.targets.append(info)
            

        skip = nadj_feeders == 1 and has_feeder[1] and current_dir == Direction.NORTHEAST

        if not skip:
            for pos in ct.get_attackable_tiles_from(my_pos, Direction.NORTHEAST, EntityType.GUNNER):
                if not cls.can_fire_from_through_roads(Direction.NORTHEAST, pos):
                    continue

                # Debug.dot(pos, Color.BLUE if (my_pos.x ^ my_pos.y) & 1 else Color.RED)

                x, y = pos.x, pos.y
                ti = tile_info[x][y]

                if ti is None:
                    continue
                if not ti.has_building:
                    continue
                if ti.is_building_ally:
                    continue


                idx = (((x) + 3) * 56 + ((y) + 3))
                
                info = GunnerTargetInfo()
                info.directly_reachable = ct.can_fire_from(my_pos, Direction.NORTHEAST, EntityType.GUNNER, pos)
                info.position = pos if info.directly_reachable else cls.first_road(Direction.NORTHEAST, pos)
                info.target_position = pos
                info.has_ally_bot = False
                info.has_enemy_bot = False
                info.has_turret = False
                info.has_building = False
                info.has_launcher = False
                info.can_shoot_me = False
                info.iscore = cls.importance_score[ti.entity_type]
                info.entity_type = ti.entity_type
                info.is_road = ti.entity_type == EntityType.ROAD
                info.is_core = ti.entity_type == EntityType.CORE
                info.current_dir = current_dir == Direction.NORTHEAST
                info.rand_key = random.random()
                info.ally_connected = DarkForest.node_kind[idx] in \
                    (1, 3)

                info.is_harvester_feeding_ally = False
                info.harvester_adjacent = ti.harvester_adjacent

                if ti.entity_type == EntityType.HARVESTER:
                    nidx = idx -1
                    if DarkForest.node_kind[nidx] in (1, 3):
                        info.is_harvester_feeding_ally = True
                    nidx = idx +1
                    if DarkForest.node_kind[nidx] in (1, 3):
                        info.is_harvester_feeding_ally = True
                    nidx = idx -56
                    if DarkForest.node_kind[nidx] in (1, 3):
                        info.is_harvester_feeding_ally = True
                    nidx = idx +56
                    if DarkForest.node_kind[nidx] in (1, 3):
                        info.is_harvester_feeding_ally = True

                if ti.has_bot:
                    if ti.is_bot_ally:
                        info.has_ally_bot = True
                    else:
                        info.has_enemy_bot = True
                        info.bot_hp = ti.bot_hp

                if ti.has_building and not ti.is_building_ally:
                    info.has_building = True
                    info.building_hp = ti.building_hp
                    if ti.has_turret:
                        info.has_turret = True
                        info.can_shoot_me = ct.can_fire_from(
                            pos, 
                            ti.turret_direction, 
                            ti.entity_type,
                            Globals.my_pos
                        )

                    elif info.entity_type == EntityType.LAUNCHER:
                        info.has_launcher = True

                cls.targets.append(info)
            

        skip = nadj_feeders == 1 and has_feeder[2] and current_dir == Direction.EAST

        if not skip:
            for pos in ct.get_attackable_tiles_from(my_pos, Direction.EAST, EntityType.GUNNER):
                if not cls.can_fire_from_through_roads(Direction.EAST, pos):
                    continue

                # Debug.dot(pos, Color.BLUE if (my_pos.x ^ my_pos.y) & 1 else Color.RED)

                x, y = pos.x, pos.y
                ti = tile_info[x][y]

                if ti is None:
                    continue
                if not ti.has_building:
                    continue
                if ti.is_building_ally:
                    continue


                idx = (((x) + 3) * 56 + ((y) + 3))
                
                info = GunnerTargetInfo()
                info.directly_reachable = ct.can_fire_from(my_pos, Direction.EAST, EntityType.GUNNER, pos)
                info.position = pos if info.directly_reachable else cls.first_road(Direction.EAST, pos)
                info.target_position = pos
                info.has_ally_bot = False
                info.has_enemy_bot = False
                info.has_turret = False
                info.has_building = False
                info.has_launcher = False
                info.can_shoot_me = False
                info.iscore = cls.importance_score[ti.entity_type]
                info.entity_type = ti.entity_type
                info.is_road = ti.entity_type == EntityType.ROAD
                info.is_core = ti.entity_type == EntityType.CORE
                info.current_dir = current_dir == Direction.EAST
                info.rand_key = random.random()
                info.ally_connected = DarkForest.node_kind[idx] in \
                    (1, 3)

                info.is_harvester_feeding_ally = False
                info.harvester_adjacent = ti.harvester_adjacent

                if ti.entity_type == EntityType.HARVESTER:
                    nidx = idx -1
                    if DarkForest.node_kind[nidx] in (1, 3):
                        info.is_harvester_feeding_ally = True
                    nidx = idx +1
                    if DarkForest.node_kind[nidx] in (1, 3):
                        info.is_harvester_feeding_ally = True
                    nidx = idx -56
                    if DarkForest.node_kind[nidx] in (1, 3):
                        info.is_harvester_feeding_ally = True
                    nidx = idx +56
                    if DarkForest.node_kind[nidx] in (1, 3):
                        info.is_harvester_feeding_ally = True

                if ti.has_bot:
                    if ti.is_bot_ally:
                        info.has_ally_bot = True
                    else:
                        info.has_enemy_bot = True
                        info.bot_hp = ti.bot_hp

                if ti.has_building and not ti.is_building_ally:
                    info.has_building = True
                    info.building_hp = ti.building_hp
                    if ti.has_turret:
                        info.has_turret = True
                        info.can_shoot_me = ct.can_fire_from(
                            pos, 
                            ti.turret_direction, 
                            ti.entity_type,
                            Globals.my_pos
                        )

                    elif info.entity_type == EntityType.LAUNCHER:
                        info.has_launcher = True

                cls.targets.append(info)
            

        skip = nadj_feeders == 1 and has_feeder[3] and current_dir == Direction.SOUTHEAST

        if not skip:
            for pos in ct.get_attackable_tiles_from(my_pos, Direction.SOUTHEAST, EntityType.GUNNER):
                if not cls.can_fire_from_through_roads(Direction.SOUTHEAST, pos):
                    continue

                # Debug.dot(pos, Color.BLUE if (my_pos.x ^ my_pos.y) & 1 else Color.RED)

                x, y = pos.x, pos.y
                ti = tile_info[x][y]

                if ti is None:
                    continue
                if not ti.has_building:
                    continue
                if ti.is_building_ally:
                    continue


                idx = (((x) + 3) * 56 + ((y) + 3))
                
                info = GunnerTargetInfo()
                info.directly_reachable = ct.can_fire_from(my_pos, Direction.SOUTHEAST, EntityType.GUNNER, pos)
                info.position = pos if info.directly_reachable else cls.first_road(Direction.SOUTHEAST, pos)
                info.target_position = pos
                info.has_ally_bot = False
                info.has_enemy_bot = False
                info.has_turret = False
                info.has_building = False
                info.has_launcher = False
                info.can_shoot_me = False
                info.iscore = cls.importance_score[ti.entity_type]
                info.entity_type = ti.entity_type
                info.is_road = ti.entity_type == EntityType.ROAD
                info.is_core = ti.entity_type == EntityType.CORE
                info.current_dir = current_dir == Direction.SOUTHEAST
                info.rand_key = random.random()
                info.ally_connected = DarkForest.node_kind[idx] in \
                    (1, 3)

                info.is_harvester_feeding_ally = False
                info.harvester_adjacent = ti.harvester_adjacent

                if ti.entity_type == EntityType.HARVESTER:
                    nidx = idx -1
                    if DarkForest.node_kind[nidx] in (1, 3):
                        info.is_harvester_feeding_ally = True
                    nidx = idx +1
                    if DarkForest.node_kind[nidx] in (1, 3):
                        info.is_harvester_feeding_ally = True
                    nidx = idx -56
                    if DarkForest.node_kind[nidx] in (1, 3):
                        info.is_harvester_feeding_ally = True
                    nidx = idx +56
                    if DarkForest.node_kind[nidx] in (1, 3):
                        info.is_harvester_feeding_ally = True

                if ti.has_bot:
                    if ti.is_bot_ally:
                        info.has_ally_bot = True
                    else:
                        info.has_enemy_bot = True
                        info.bot_hp = ti.bot_hp

                if ti.has_building and not ti.is_building_ally:
                    info.has_building = True
                    info.building_hp = ti.building_hp
                    if ti.has_turret:
                        info.has_turret = True
                        info.can_shoot_me = ct.can_fire_from(
                            pos, 
                            ti.turret_direction, 
                            ti.entity_type,
                            Globals.my_pos
                        )

                    elif info.entity_type == EntityType.LAUNCHER:
                        info.has_launcher = True

                cls.targets.append(info)
            

        skip = nadj_feeders == 1 and has_feeder[4] and current_dir == Direction.SOUTH

        if not skip:
            for pos in ct.get_attackable_tiles_from(my_pos, Direction.SOUTH, EntityType.GUNNER):
                if not cls.can_fire_from_through_roads(Direction.SOUTH, pos):
                    continue

                # Debug.dot(pos, Color.BLUE if (my_pos.x ^ my_pos.y) & 1 else Color.RED)

                x, y = pos.x, pos.y
                ti = tile_info[x][y]

                if ti is None:
                    continue
                if not ti.has_building:
                    continue
                if ti.is_building_ally:
                    continue


                idx = (((x) + 3) * 56 + ((y) + 3))
                
                info = GunnerTargetInfo()
                info.directly_reachable = ct.can_fire_from(my_pos, Direction.SOUTH, EntityType.GUNNER, pos)
                info.position = pos if info.directly_reachable else cls.first_road(Direction.SOUTH, pos)
                info.target_position = pos
                info.has_ally_bot = False
                info.has_enemy_bot = False
                info.has_turret = False
                info.has_building = False
                info.has_launcher = False
                info.can_shoot_me = False
                info.iscore = cls.importance_score[ti.entity_type]
                info.entity_type = ti.entity_type
                info.is_road = ti.entity_type == EntityType.ROAD
                info.is_core = ti.entity_type == EntityType.CORE
                info.current_dir = current_dir == Direction.SOUTH
                info.rand_key = random.random()
                info.ally_connected = DarkForest.node_kind[idx] in \
                    (1, 3)

                info.is_harvester_feeding_ally = False
                info.harvester_adjacent = ti.harvester_adjacent

                if ti.entity_type == EntityType.HARVESTER:
                    nidx = idx -1
                    if DarkForest.node_kind[nidx] in (1, 3):
                        info.is_harvester_feeding_ally = True
                    nidx = idx +1
                    if DarkForest.node_kind[nidx] in (1, 3):
                        info.is_harvester_feeding_ally = True
                    nidx = idx -56
                    if DarkForest.node_kind[nidx] in (1, 3):
                        info.is_harvester_feeding_ally = True
                    nidx = idx +56
                    if DarkForest.node_kind[nidx] in (1, 3):
                        info.is_harvester_feeding_ally = True

                if ti.has_bot:
                    if ti.is_bot_ally:
                        info.has_ally_bot = True
                    else:
                        info.has_enemy_bot = True
                        info.bot_hp = ti.bot_hp

                if ti.has_building and not ti.is_building_ally:
                    info.has_building = True
                    info.building_hp = ti.building_hp
                    if ti.has_turret:
                        info.has_turret = True
                        info.can_shoot_me = ct.can_fire_from(
                            pos, 
                            ti.turret_direction, 
                            ti.entity_type,
                            Globals.my_pos
                        )

                    elif info.entity_type == EntityType.LAUNCHER:
                        info.has_launcher = True

                cls.targets.append(info)
            

        skip = nadj_feeders == 1 and has_feeder[5] and current_dir == Direction.SOUTHWEST

        if not skip:
            for pos in ct.get_attackable_tiles_from(my_pos, Direction.SOUTHWEST, EntityType.GUNNER):
                if not cls.can_fire_from_through_roads(Direction.SOUTHWEST, pos):
                    continue

                # Debug.dot(pos, Color.BLUE if (my_pos.x ^ my_pos.y) & 1 else Color.RED)

                x, y = pos.x, pos.y
                ti = tile_info[x][y]

                if ti is None:
                    continue
                if not ti.has_building:
                    continue
                if ti.is_building_ally:
                    continue


                idx = (((x) + 3) * 56 + ((y) + 3))
                
                info = GunnerTargetInfo()
                info.directly_reachable = ct.can_fire_from(my_pos, Direction.SOUTHWEST, EntityType.GUNNER, pos)
                info.position = pos if info.directly_reachable else cls.first_road(Direction.SOUTHWEST, pos)
                info.target_position = pos
                info.has_ally_bot = False
                info.has_enemy_bot = False
                info.has_turret = False
                info.has_building = False
                info.has_launcher = False
                info.can_shoot_me = False
                info.iscore = cls.importance_score[ti.entity_type]
                info.entity_type = ti.entity_type
                info.is_road = ti.entity_type == EntityType.ROAD
                info.is_core = ti.entity_type == EntityType.CORE
                info.current_dir = current_dir == Direction.SOUTHWEST
                info.rand_key = random.random()
                info.ally_connected = DarkForest.node_kind[idx] in \
                    (1, 3)

                info.is_harvester_feeding_ally = False
                info.harvester_adjacent = ti.harvester_adjacent

                if ti.entity_type == EntityType.HARVESTER:
                    nidx = idx -1
                    if DarkForest.node_kind[nidx] in (1, 3):
                        info.is_harvester_feeding_ally = True
                    nidx = idx +1
                    if DarkForest.node_kind[nidx] in (1, 3):
                        info.is_harvester_feeding_ally = True
                    nidx = idx -56
                    if DarkForest.node_kind[nidx] in (1, 3):
                        info.is_harvester_feeding_ally = True
                    nidx = idx +56
                    if DarkForest.node_kind[nidx] in (1, 3):
                        info.is_harvester_feeding_ally = True

                if ti.has_bot:
                    if ti.is_bot_ally:
                        info.has_ally_bot = True
                    else:
                        info.has_enemy_bot = True
                        info.bot_hp = ti.bot_hp

                if ti.has_building and not ti.is_building_ally:
                    info.has_building = True
                    info.building_hp = ti.building_hp
                    if ti.has_turret:
                        info.has_turret = True
                        info.can_shoot_me = ct.can_fire_from(
                            pos, 
                            ti.turret_direction, 
                            ti.entity_type,
                            Globals.my_pos
                        )

                    elif info.entity_type == EntityType.LAUNCHER:
                        info.has_launcher = True

                cls.targets.append(info)
            

        skip = nadj_feeders == 1 and has_feeder[6] and current_dir == Direction.WEST

        if not skip:
            for pos in ct.get_attackable_tiles_from(my_pos, Direction.WEST, EntityType.GUNNER):
                if not cls.can_fire_from_through_roads(Direction.WEST, pos):
                    continue

                # Debug.dot(pos, Color.BLUE if (my_pos.x ^ my_pos.y) & 1 else Color.RED)

                x, y = pos.x, pos.y
                ti = tile_info[x][y]

                if ti is None:
                    continue
                if not ti.has_building:
                    continue
                if ti.is_building_ally:
                    continue


                idx = (((x) + 3) * 56 + ((y) + 3))
                
                info = GunnerTargetInfo()
                info.directly_reachable = ct.can_fire_from(my_pos, Direction.WEST, EntityType.GUNNER, pos)
                info.position = pos if info.directly_reachable else cls.first_road(Direction.WEST, pos)
                info.target_position = pos
                info.has_ally_bot = False
                info.has_enemy_bot = False
                info.has_turret = False
                info.has_building = False
                info.has_launcher = False
                info.can_shoot_me = False
                info.iscore = cls.importance_score[ti.entity_type]
                info.entity_type = ti.entity_type
                info.is_road = ti.entity_type == EntityType.ROAD
                info.is_core = ti.entity_type == EntityType.CORE
                info.current_dir = current_dir == Direction.WEST
                info.rand_key = random.random()
                info.ally_connected = DarkForest.node_kind[idx] in \
                    (1, 3)

                info.is_harvester_feeding_ally = False
                info.harvester_adjacent = ti.harvester_adjacent

                if ti.entity_type == EntityType.HARVESTER:
                    nidx = idx -1
                    if DarkForest.node_kind[nidx] in (1, 3):
                        info.is_harvester_feeding_ally = True
                    nidx = idx +1
                    if DarkForest.node_kind[nidx] in (1, 3):
                        info.is_harvester_feeding_ally = True
                    nidx = idx -56
                    if DarkForest.node_kind[nidx] in (1, 3):
                        info.is_harvester_feeding_ally = True
                    nidx = idx +56
                    if DarkForest.node_kind[nidx] in (1, 3):
                        info.is_harvester_feeding_ally = True

                if ti.has_bot:
                    if ti.is_bot_ally:
                        info.has_ally_bot = True
                    else:
                        info.has_enemy_bot = True
                        info.bot_hp = ti.bot_hp

                if ti.has_building and not ti.is_building_ally:
                    info.has_building = True
                    info.building_hp = ti.building_hp
                    if ti.has_turret:
                        info.has_turret = True
                        info.can_shoot_me = ct.can_fire_from(
                            pos, 
                            ti.turret_direction, 
                            ti.entity_type,
                            Globals.my_pos
                        )

                    elif info.entity_type == EntityType.LAUNCHER:
                        info.has_launcher = True

                cls.targets.append(info)
            

        skip = nadj_feeders == 1 and has_feeder[7] and current_dir == Direction.NORTHWEST

        if not skip:
            for pos in ct.get_attackable_tiles_from(my_pos, Direction.NORTHWEST, EntityType.GUNNER):
                if not cls.can_fire_from_through_roads(Direction.NORTHWEST, pos):
                    continue

                # Debug.dot(pos, Color.BLUE if (my_pos.x ^ my_pos.y) & 1 else Color.RED)

                x, y = pos.x, pos.y
                ti = tile_info[x][y]

                if ti is None:
                    continue
                if not ti.has_building:
                    continue
                if ti.is_building_ally:
                    continue


                idx = (((x) + 3) * 56 + ((y) + 3))
                
                info = GunnerTargetInfo()
                info.directly_reachable = ct.can_fire_from(my_pos, Direction.NORTHWEST, EntityType.GUNNER, pos)
                info.position = pos if info.directly_reachable else cls.first_road(Direction.NORTHWEST, pos)
                info.target_position = pos
                info.has_ally_bot = False
                info.has_enemy_bot = False
                info.has_turret = False
                info.has_building = False
                info.has_launcher = False
                info.can_shoot_me = False
                info.iscore = cls.importance_score[ti.entity_type]
                info.entity_type = ti.entity_type
                info.is_road = ti.entity_type == EntityType.ROAD
                info.is_core = ti.entity_type == EntityType.CORE
                info.current_dir = current_dir == Direction.NORTHWEST
                info.rand_key = random.random()
                info.ally_connected = DarkForest.node_kind[idx] in \
                    (1, 3)

                info.is_harvester_feeding_ally = False
                info.harvester_adjacent = ti.harvester_adjacent

                if ti.entity_type == EntityType.HARVESTER:
                    nidx = idx -1
                    if DarkForest.node_kind[nidx] in (1, 3):
                        info.is_harvester_feeding_ally = True
                    nidx = idx +1
                    if DarkForest.node_kind[nidx] in (1, 3):
                        info.is_harvester_feeding_ally = True
                    nidx = idx -56
                    if DarkForest.node_kind[nidx] in (1, 3):
                        info.is_harvester_feeding_ally = True
                    nidx = idx +56
                    if DarkForest.node_kind[nidx] in (1, 3):
                        info.is_harvester_feeding_ally = True

                if ti.has_bot:
                    if ti.is_bot_ally:
                        info.has_ally_bot = True
                    else:
                        info.has_enemy_bot = True
                        info.bot_hp = ti.bot_hp

                if ti.has_building and not ti.is_building_ally:
                    info.has_building = True
                    info.building_hp = ti.building_hp
                    if ti.has_turret:
                        info.has_turret = True
                        info.can_shoot_me = ct.can_fire_from(
                            pos, 
                            ti.turret_direction, 
                            ti.entity_type,
                            Globals.my_pos
                        )

                    elif info.entity_type == EntityType.LAUNCHER:
                        info.has_launcher = True

                cls.targets.append(info)
            

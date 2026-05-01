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

class BuildManager:

    @staticmethod
    def scale(cost: int) -> int:
        return int(cost * MarketMaker.scale_ratio)

    @staticmethod
    def is_buildable(pos: Position):
        dsq = Globals.my_pos.distance_squared(pos)
        if dsq > 2 or dsq == 0:
            return False

        ti = Map.tile_info[pos.x][pos.y]
        return (
            ti.env != Environment.WALL 
            and not ti.has_building
            and not ti.has_bot
        )

    @staticmethod
    def is_dbuildable(pos: Position):
        dsq = Globals.my_pos.distance_squared(pos)
        if dsq > 2 or dsq == 0:
            return False

        ti = Map.tile_info[pos.x][pos.y]

        if Globals.ct.can_destroy(pos) and not ti.has_bot:
            return True

        return (
            ti.env != Environment.WALL
            and (not ti.has_building or (ti.is_building_ally and ti.entity_type != EntityType.CORE))
        )



    @staticmethod
    def build_builder_bot(*a):
        Globals.ct.build_builder_bot(*a)

    @staticmethod
    def dbuild_builder_bot(pos, *a):
        if Globals.ct.can_destroy(pos):
            BuildManager.destroy(pos)
        Globals.ct.build_builder_bot(pos, *a)


    @staticmethod
    def can_mbuild_builder_bot() -> bool:
        # assert EntityType.BUILDER_BOT in Constants.PASSABLE_SET  remove because changed
        pos = Globals.my_pos

        ct = Globals.ct

        return (
            (ct.can_destroy(pos) or Map.tile_info[pos.x][pos.y].entity_type is None) and
            ct.get_unit_count() < 50 and
            ct.get_action_cooldown() == 0 and
            ct.get_move_cooldown() == 0 and
            BuildManager.can_afford_builder_bot(pos)
        )


    @staticmethod
    def can_smartbuild_builder_bot(pos) -> bool:
        if pos == Globals.my_pos:
            return BuildManager.can_mbuild_builder_bot()
        return BuildManager.can_dbuild_builder_bot(pos)

    @staticmethod
    def smartbuild_builder_bot(pos, *a):
        if pos == Globals.my_pos:
            BuildManager.mbuild_builder_bot(*a)
            return 
        BuildManager.dbuild_builder_bot(pos, *a)


    @staticmethod
    def mbuild_builder_bot(*a):
        pos = Globals.my_pos
        if Globals.ct.can_destroy(pos):
            BuildManager.destroy(pos)

        success = Pathfinder.move_off()
        if not success:
            Debug.tee('failed move off')
            Debug.diamond(Color.YELLOW)

        if BuildManager.can_build_builder_bot(pos, *a):
            Globals.ct.build_builder_bot(pos, *a)


    @staticmethod
    def can_dbuild_builder_bot(pos) -> bool:
            
        return (
            Globals.ct.get_unit_count() < 50 and
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            not Map.tile_info[pos.x][pos.y].has_bot and
            BuildManager.can_afford_builder_bot(pos)
        )

    @staticmethod
    def can_build_builder_bot(*a) -> bool:
        return Globals.ct.can_build_builder_bot(*a)

    @staticmethod
    def can_afford_builder_bot(pos=None) -> bool:

        ti_cost, ax_cost = Globals.ct.get_builder_bot_cost()
        

        leftover_unscaled_ti = 0

        leftover_unscaled_ti += 40

        
        return (MarketMaker.ti - ti_cost) >= int(leftover_unscaled_ti * MarketMaker.scale_ratio) \
            and MarketMaker.ax >= ax_cost




    @staticmethod
    def build_gunner(*a):
        Globals.ct.build_gunner(*a)

    @staticmethod
    def dbuild_gunner(pos, *a):
        if Globals.ct.can_destroy(pos):
            BuildManager.destroy(pos)
        Globals.ct.build_gunner(pos, *a)


    @staticmethod
    def can_mbuild_gunner() -> bool:
        # assert EntityType.GUNNER in Constants.PASSABLE_SET  remove because changed
        pos = Globals.my_pos

        ct = Globals.ct

        return (
            (ct.can_destroy(pos) or Map.tile_info[pos.x][pos.y].entity_type is None) and
            ct.get_unit_count() < 50 and
            ct.get_action_cooldown() == 0 and
            ct.get_move_cooldown() == 0 and
            BuildManager.can_afford_gunner(pos)
        )


    @staticmethod
    def can_smartbuild_gunner(pos) -> bool:
        if pos == Globals.my_pos:
            return BuildManager.can_mbuild_gunner()
        return BuildManager.can_dbuild_gunner(pos)

    @staticmethod
    def smartbuild_gunner(pos, *a):
        if pos == Globals.my_pos:
            BuildManager.mbuild_gunner(*a)
            return 
        BuildManager.dbuild_gunner(pos, *a)


    @staticmethod
    def mbuild_gunner(*a):
        pos = Globals.my_pos
        if Globals.ct.can_destroy(pos):
            BuildManager.destroy(pos)

        success = Pathfinder.move_off()
        if not success:
            Debug.tee('failed move off')
            Debug.diamond(Color.YELLOW)

        if BuildManager.can_build_gunner(pos, *a):
            Globals.ct.build_gunner(pos, *a)


    @staticmethod
    def can_dbuild_gunner(pos) -> bool:
            
        return (
            Globals.ct.get_unit_count() < 50 and
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            not Map.tile_info[pos.x][pos.y].has_bot and
            BuildManager.can_afford_gunner(pos)
        )

    @staticmethod
    def can_build_gunner(*a) -> bool:
        return Globals.ct.can_build_gunner(*a)

    @staticmethod
    def can_afford_gunner(pos=None) -> bool:

        ti_cost, ax_cost = Globals.ct.get_gunner_cost()
        

        leftover_unscaled_ti = 0

        leftover_unscaled_ti += 0

        
        return (MarketMaker.ti - ti_cost) >= int(leftover_unscaled_ti * MarketMaker.scale_ratio) \
            and MarketMaker.ax >= ax_cost




    @staticmethod
    def build_sentinel(*a):
        Globals.ct.build_sentinel(*a)

    @staticmethod
    def dbuild_sentinel(pos, *a):
        if Globals.ct.can_destroy(pos):
            BuildManager.destroy(pos)
        Globals.ct.build_sentinel(pos, *a)


    @staticmethod
    def can_mbuild_sentinel() -> bool:
        # assert EntityType.SENTINEL in Constants.PASSABLE_SET  remove because changed
        pos = Globals.my_pos

        ct = Globals.ct

        return (
            (ct.can_destroy(pos) or Map.tile_info[pos.x][pos.y].entity_type is None) and
            ct.get_unit_count() < 50 and
            ct.get_action_cooldown() == 0 and
            ct.get_move_cooldown() == 0 and
            BuildManager.can_afford_sentinel(pos)
        )


    @staticmethod
    def can_smartbuild_sentinel(pos) -> bool:
        if pos == Globals.my_pos:
            return BuildManager.can_mbuild_sentinel()
        return BuildManager.can_dbuild_sentinel(pos)

    @staticmethod
    def smartbuild_sentinel(pos, *a):
        if pos == Globals.my_pos:
            BuildManager.mbuild_sentinel(*a)
            return 
        BuildManager.dbuild_sentinel(pos, *a)


    @staticmethod
    def mbuild_sentinel(*a):
        pos = Globals.my_pos
        if Globals.ct.can_destroy(pos):
            BuildManager.destroy(pos)

        success = Pathfinder.move_off()
        if not success:
            Debug.tee('failed move off')
            Debug.diamond(Color.YELLOW)

        if BuildManager.can_build_sentinel(pos, *a):
            Globals.ct.build_sentinel(pos, *a)


    @staticmethod
    def can_dbuild_sentinel(pos) -> bool:
            
        return (
            Globals.ct.get_unit_count() < 50 and
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            not Map.tile_info[pos.x][pos.y].has_bot and
            BuildManager.can_afford_sentinel(pos)
        )

    @staticmethod
    def can_build_sentinel(*a) -> bool:
        return Globals.ct.can_build_sentinel(*a)

    @staticmethod
    def can_afford_sentinel(pos=None) -> bool:

        ti_cost, ax_cost = Globals.ct.get_sentinel_cost()
        

        leftover_unscaled_ti = 0

        leftover_unscaled_ti += 0

        
        return (MarketMaker.ti - ti_cost) >= int(leftover_unscaled_ti * MarketMaker.scale_ratio) \
            and MarketMaker.ax >= ax_cost




    @staticmethod
    def build_breach(*a):
        Globals.ct.build_breach(*a)

    @staticmethod
    def dbuild_breach(pos, *a):
        if Globals.ct.can_destroy(pos):
            BuildManager.destroy(pos)
        Globals.ct.build_breach(pos, *a)


    @staticmethod
    def can_mbuild_breach() -> bool:
        # assert EntityType.BREACH in Constants.PASSABLE_SET  remove because changed
        pos = Globals.my_pos

        ct = Globals.ct

        return (
            (ct.can_destroy(pos) or Map.tile_info[pos.x][pos.y].entity_type is None) and
            ct.get_unit_count() < 50 and
            ct.get_action_cooldown() == 0 and
            ct.get_move_cooldown() == 0 and
            BuildManager.can_afford_breach(pos)
        )


    @staticmethod
    def can_smartbuild_breach(pos) -> bool:
        if pos == Globals.my_pos:
            return BuildManager.can_mbuild_breach()
        return BuildManager.can_dbuild_breach(pos)

    @staticmethod
    def smartbuild_breach(pos, *a):
        if pos == Globals.my_pos:
            BuildManager.mbuild_breach(*a)
            return 
        BuildManager.dbuild_breach(pos, *a)


    @staticmethod
    def mbuild_breach(*a):
        pos = Globals.my_pos
        if Globals.ct.can_destroy(pos):
            BuildManager.destroy(pos)

        success = Pathfinder.move_off()
        if not success:
            Debug.tee('failed move off')
            Debug.diamond(Color.YELLOW)

        if BuildManager.can_build_breach(pos, *a):
            Globals.ct.build_breach(pos, *a)


    @staticmethod
    def can_dbuild_breach(pos) -> bool:
            
        return (
            Globals.ct.get_unit_count() < 50 and
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            not Map.tile_info[pos.x][pos.y].has_bot and
            BuildManager.can_afford_breach(pos)
        )

    @staticmethod
    def can_build_breach(*a) -> bool:
        return Globals.ct.can_build_breach(*a)

    @staticmethod
    def can_afford_breach(pos=None) -> bool:

        ti_cost, ax_cost = Globals.ct.get_breach_cost()
        

        leftover_unscaled_ti = 0

        leftover_unscaled_ti += 40

        
        return (MarketMaker.ti - ti_cost) >= int(leftover_unscaled_ti * MarketMaker.scale_ratio) \
            and MarketMaker.ax >= ax_cost




    @staticmethod
    def build_launcher(*a):
        Globals.ct.build_launcher(*a)

    @staticmethod
    def dbuild_launcher(pos, *a):
        if Globals.ct.can_destroy(pos):
            BuildManager.destroy(pos)
        Globals.ct.build_launcher(pos, *a)


    @staticmethod
    def can_mbuild_launcher() -> bool:
        # assert EntityType.LAUNCHER in Constants.PASSABLE_SET  remove because changed
        pos = Globals.my_pos

        ct = Globals.ct

        return (
            (ct.can_destroy(pos) or Map.tile_info[pos.x][pos.y].entity_type is None) and
            ct.get_unit_count() < 50 and
            ct.get_action_cooldown() == 0 and
            ct.get_move_cooldown() == 0 and
            BuildManager.can_afford_launcher(pos)
        )


    @staticmethod
    def can_smartbuild_launcher(pos) -> bool:
        if pos == Globals.my_pos:
            return BuildManager.can_mbuild_launcher()
        return BuildManager.can_dbuild_launcher(pos)

    @staticmethod
    def smartbuild_launcher(pos, *a):
        if pos == Globals.my_pos:
            BuildManager.mbuild_launcher(*a)
            return 
        BuildManager.dbuild_launcher(pos, *a)


    @staticmethod
    def mbuild_launcher(*a):
        pos = Globals.my_pos
        if Globals.ct.can_destroy(pos):
            BuildManager.destroy(pos)

        success = Pathfinder.move_off()
        if not success:
            Debug.tee('failed move off')
            Debug.diamond(Color.YELLOW)

        if BuildManager.can_build_launcher(pos, *a):
            Globals.ct.build_launcher(pos, *a)


    @staticmethod
    def can_dbuild_launcher(pos) -> bool:
            
        return (
            Globals.ct.get_unit_count() < 50 and
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            not Map.tile_info[pos.x][pos.y].has_bot and
            BuildManager.can_afford_launcher(pos)
        )

    @staticmethod
    def can_build_launcher(*a) -> bool:
        return Globals.ct.can_build_launcher(*a)

    @staticmethod
    def can_afford_launcher(pos=None) -> bool:

        ti_cost, ax_cost = Globals.ct.get_launcher_cost()
        

        leftover_unscaled_ti = 0

        leftover_unscaled_ti += 0

        
        return (MarketMaker.ti - ti_cost) >= int(leftover_unscaled_ti * MarketMaker.scale_ratio) \
            and MarketMaker.ax >= ax_cost




    @staticmethod
    def build_conveyor(*a):
        Globals.ct.build_conveyor(*a)

    @staticmethod
    def dbuild_conveyor(pos, *a):
        if Globals.ct.can_destroy(pos):
            BuildManager.destroy(pos)
        Globals.ct.build_conveyor(pos, *a)


    @staticmethod
    def can_mbuild_conveyor() -> bool:
        # assert EntityType.CONVEYOR in Constants.PASSABLE_SET  remove because changed
        pos = Globals.my_pos

        ct = Globals.ct

        return (
            (ct.can_destroy(pos) or Map.tile_info[pos.x][pos.y].entity_type is None) and
            ct.get_action_cooldown() == 0 and
            ct.get_move_cooldown() == 0 and
            BuildManager.can_afford_conveyor(pos)
        )


    @staticmethod
    def can_smartbuild_conveyor(pos) -> bool:
        if pos == Globals.my_pos:
            return BuildManager.can_mbuild_conveyor()
        return BuildManager.can_dbuild_conveyor(pos)

    @staticmethod
    def smartbuild_conveyor(pos, *a):
        if pos == Globals.my_pos:
            BuildManager.mbuild_conveyor(*a)
            return 
        BuildManager.dbuild_conveyor(pos, *a)


    @staticmethod
    def mbuild_conveyor(*a):
        pos = Globals.my_pos
        if Globals.ct.can_destroy(pos):
            BuildManager.destroy(pos)


        if BuildManager.can_build_conveyor(pos, *a):
            Globals.ct.build_conveyor(pos, *a)


    @staticmethod
    def can_dbuild_conveyor(pos) -> bool:
        if pos == Globals.my_pos:
            return BuildManager.can_mbuild_conveyor()
            
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            BuildManager.can_afford_conveyor(pos)
        )

    @staticmethod
    def can_build_conveyor(*a) -> bool:
        return Globals.ct.can_build_conveyor(*a)

    @staticmethod
    def can_afford_conveyor(pos=None) -> bool:

        ti_cost, ax_cost = Globals.ct.get_conveyor_cost()
        

        leftover_unscaled_ti = 0

        if Globals.round > 50:
            leftover_unscaled_ti += 20

        if pos is not None:
            leftover_unscaled_ti += Util.linf(pos, Unit.core_pos) * 2
        
        return (MarketMaker.ti - ti_cost) >= int(leftover_unscaled_ti * MarketMaker.scale_ratio) \
            and MarketMaker.ax >= ax_cost




    @staticmethod
    def build_splitter(*a):
        Globals.ct.build_splitter(*a)

    @staticmethod
    def dbuild_splitter(pos, *a):
        if Globals.ct.can_destroy(pos):
            BuildManager.destroy(pos)
        Globals.ct.build_splitter(pos, *a)


    @staticmethod
    def can_mbuild_splitter() -> bool:
        # assert EntityType.SPLITTER in Constants.PASSABLE_SET  remove because changed
        pos = Globals.my_pos

        ct = Globals.ct

        return (
            (ct.can_destroy(pos) or Map.tile_info[pos.x][pos.y].entity_type is None) and
            ct.get_action_cooldown() == 0 and
            ct.get_move_cooldown() == 0 and
            BuildManager.can_afford_splitter(pos)
        )


    @staticmethod
    def can_smartbuild_splitter(pos) -> bool:
        if pos == Globals.my_pos:
            return BuildManager.can_mbuild_splitter()
        return BuildManager.can_dbuild_splitter(pos)

    @staticmethod
    def smartbuild_splitter(pos, *a):
        if pos == Globals.my_pos:
            BuildManager.mbuild_splitter(*a)
            return 
        BuildManager.dbuild_splitter(pos, *a)


    @staticmethod
    def mbuild_splitter(*a):
        pos = Globals.my_pos
        if Globals.ct.can_destroy(pos):
            BuildManager.destroy(pos)


        if BuildManager.can_build_splitter(pos, *a):
            Globals.ct.build_splitter(pos, *a)


    @staticmethod
    def can_dbuild_splitter(pos) -> bool:
        if pos == Globals.my_pos:
            return BuildManager.can_mbuild_splitter()
            
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            BuildManager.can_afford_splitter(pos)
        )

    @staticmethod
    def can_build_splitter(*a) -> bool:
        return Globals.ct.can_build_splitter(*a)

    @staticmethod
    def can_afford_splitter(pos=None) -> bool:

        ti_cost, ax_cost = Globals.ct.get_splitter_cost()
        

        leftover_unscaled_ti = 0

        if Globals.round > 50:
            leftover_unscaled_ti += 20

        if pos is not None:
            leftover_unscaled_ti += Util.linf(pos, Unit.core_pos) * 2
        
        return (MarketMaker.ti - ti_cost) >= int(leftover_unscaled_ti * MarketMaker.scale_ratio) \
            and MarketMaker.ax >= ax_cost




    @staticmethod
    def build_armoured_conveyor(*a):
        Globals.ct.build_armoured_conveyor(*a)

    @staticmethod
    def dbuild_armoured_conveyor(pos, *a):
        if Globals.ct.can_destroy(pos):
            BuildManager.destroy(pos)
        Globals.ct.build_armoured_conveyor(pos, *a)


    @staticmethod
    def can_mbuild_armoured_conveyor() -> bool:
        # assert EntityType.ARMOURED_CONVEYOR in Constants.PASSABLE_SET  remove because changed
        pos = Globals.my_pos

        ct = Globals.ct

        return (
            (ct.can_destroy(pos) or Map.tile_info[pos.x][pos.y].entity_type is None) and
            ct.get_action_cooldown() == 0 and
            ct.get_move_cooldown() == 0 and
            BuildManager.can_afford_armoured_conveyor(pos)
        )


    @staticmethod
    def can_smartbuild_armoured_conveyor(pos) -> bool:
        if pos == Globals.my_pos:
            return BuildManager.can_mbuild_armoured_conveyor()
        return BuildManager.can_dbuild_armoured_conveyor(pos)

    @staticmethod
    def smartbuild_armoured_conveyor(pos, *a):
        if pos == Globals.my_pos:
            BuildManager.mbuild_armoured_conveyor(*a)
            return 
        BuildManager.dbuild_armoured_conveyor(pos, *a)


    @staticmethod
    def mbuild_armoured_conveyor(*a):
        pos = Globals.my_pos
        if Globals.ct.can_destroy(pos):
            BuildManager.destroy(pos)


        if BuildManager.can_build_armoured_conveyor(pos, *a):
            Globals.ct.build_armoured_conveyor(pos, *a)


    @staticmethod
    def can_dbuild_armoured_conveyor(pos) -> bool:
        if pos == Globals.my_pos:
            return BuildManager.can_mbuild_armoured_conveyor()
            
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            BuildManager.can_afford_armoured_conveyor(pos)
        )

    @staticmethod
    def can_build_armoured_conveyor(*a) -> bool:
        return Globals.ct.can_build_armoured_conveyor(*a)

    @staticmethod
    def can_afford_armoured_conveyor(pos=None) -> bool:

        ti_cost, ax_cost = Globals.ct.get_armoured_conveyor_cost()
        

        leftover_unscaled_ti = 0

        if Globals.round > 50:
            leftover_unscaled_ti += 20

        if pos is not None:
            leftover_unscaled_ti += Util.linf(pos, Unit.core_pos) * 2
        
        return (MarketMaker.ti - ti_cost) >= int(leftover_unscaled_ti * MarketMaker.scale_ratio) \
            and MarketMaker.ax >= ax_cost




    @staticmethod
    def build_bridge(*a):
        Globals.ct.build_bridge(*a)

    @staticmethod
    def dbuild_bridge(pos, *a):
        if Globals.ct.can_destroy(pos):
            BuildManager.destroy(pos)
        Globals.ct.build_bridge(pos, *a)


    @staticmethod
    def can_mbuild_bridge() -> bool:
        # assert EntityType.BRIDGE in Constants.PASSABLE_SET  remove because changed
        pos = Globals.my_pos

        ct = Globals.ct

        return (
            (ct.can_destroy(pos) or Map.tile_info[pos.x][pos.y].entity_type is None) and
            ct.get_action_cooldown() == 0 and
            ct.get_move_cooldown() == 0 and
            BuildManager.can_afford_bridge(pos)
        )


    @staticmethod
    def can_smartbuild_bridge(pos) -> bool:
        if pos == Globals.my_pos:
            return BuildManager.can_mbuild_bridge()
        return BuildManager.can_dbuild_bridge(pos)

    @staticmethod
    def smartbuild_bridge(pos, *a):
        if pos == Globals.my_pos:
            BuildManager.mbuild_bridge(*a)
            return 
        BuildManager.dbuild_bridge(pos, *a)


    @staticmethod
    def mbuild_bridge(*a):
        pos = Globals.my_pos
        if Globals.ct.can_destroy(pos):
            BuildManager.destroy(pos)


        if BuildManager.can_build_bridge(pos, *a):
            Globals.ct.build_bridge(pos, *a)


    @staticmethod
    def can_dbuild_bridge(pos) -> bool:
        if pos == Globals.my_pos:
            return BuildManager.can_mbuild_bridge()
            
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            BuildManager.can_afford_bridge(pos)
        )

    @staticmethod
    def can_build_bridge(*a) -> bool:
        return Globals.ct.can_build_bridge(*a)

    @staticmethod
    def can_afford_bridge(pos=None) -> bool:

        ti_cost, ax_cost = Globals.ct.get_bridge_cost()
        

        leftover_unscaled_ti = 0

        if Globals.round > 50:
            leftover_unscaled_ti += 20

        if pos is not None:
            leftover_unscaled_ti += Util.linf(pos, Unit.core_pos) * 2
        
        return (MarketMaker.ti - ti_cost) >= int(leftover_unscaled_ti * MarketMaker.scale_ratio) \
            and MarketMaker.ax >= ax_cost




    @staticmethod
    def build_harvester(*a):
        Globals.ct.build_harvester(*a)

    @staticmethod
    def dbuild_harvester(pos, *a):
        if Globals.ct.can_destroy(pos):
            BuildManager.destroy(pos)
        Globals.ct.build_harvester(pos, *a)


    @staticmethod
    def can_mbuild_harvester() -> bool:
        # assert EntityType.HARVESTER in Constants.PASSABLE_SET  remove because changed
        pos = Globals.my_pos

        ct = Globals.ct

        return (
            (ct.can_destroy(pos) or Map.tile_info[pos.x][pos.y].entity_type is None) and
            ct.get_action_cooldown() == 0 and
            ct.get_move_cooldown() == 0 and
            BuildManager.can_afford_harvester(pos)
        )


    @staticmethod
    def can_smartbuild_harvester(pos) -> bool:
        if pos == Globals.my_pos:
            return BuildManager.can_mbuild_harvester()
        return BuildManager.can_dbuild_harvester(pos)

    @staticmethod
    def smartbuild_harvester(pos, *a):
        if pos == Globals.my_pos:
            BuildManager.mbuild_harvester(*a)
            return 
        BuildManager.dbuild_harvester(pos, *a)


    @staticmethod
    def mbuild_harvester(*a):
        pos = Globals.my_pos
        if Globals.ct.can_destroy(pos):
            BuildManager.destroy(pos)

        success = Pathfinder.move_off()
        if not success:
            Debug.tee('failed move off')
            Debug.diamond(Color.YELLOW)

        if BuildManager.can_build_harvester(pos, *a):
            Globals.ct.build_harvester(pos, *a)


    @staticmethod
    def can_dbuild_harvester(pos) -> bool:
            
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            not Map.tile_info[pos.x][pos.y].has_bot and
            BuildManager.can_afford_harvester(pos)
        )

    @staticmethod
    def can_build_harvester(*a) -> bool:
        return Globals.ct.can_build_harvester(*a)

    @staticmethod
    def can_afford_harvester(pos=None) -> bool:

        ti_cost, ax_cost = Globals.ct.get_harvester_cost()
        

        leftover_unscaled_ti = 0

        leftover_unscaled_ti += 20

        if pos is not None:
            leftover_unscaled_ti += Util.linf(pos, Unit.core_pos) * 2
        
        return (MarketMaker.ti - ti_cost) >= int(leftover_unscaled_ti * MarketMaker.scale_ratio) \
            and MarketMaker.ax >= ax_cost




    @staticmethod
    def build_foundry(*a):
        Globals.ct.build_foundry(*a)

    @staticmethod
    def dbuild_foundry(pos, *a):
        if Globals.ct.can_destroy(pos):
            BuildManager.destroy(pos)
        Globals.ct.build_foundry(pos, *a)


    @staticmethod
    def can_mbuild_foundry() -> bool:
        # assert EntityType.FOUNDRY in Constants.PASSABLE_SET  remove because changed
        pos = Globals.my_pos

        ct = Globals.ct

        return (
            (ct.can_destroy(pos) or Map.tile_info[pos.x][pos.y].entity_type is None) and
            ct.get_action_cooldown() == 0 and
            ct.get_move_cooldown() == 0 and
            BuildManager.can_afford_foundry(pos)
        )


    @staticmethod
    def can_smartbuild_foundry(pos) -> bool:
        if pos == Globals.my_pos:
            return BuildManager.can_mbuild_foundry()
        return BuildManager.can_dbuild_foundry(pos)

    @staticmethod
    def smartbuild_foundry(pos, *a):
        if pos == Globals.my_pos:
            BuildManager.mbuild_foundry(*a)
            return 
        BuildManager.dbuild_foundry(pos, *a)


    @staticmethod
    def mbuild_foundry(*a):
        pos = Globals.my_pos
        if Globals.ct.can_destroy(pos):
            BuildManager.destroy(pos)

        success = Pathfinder.move_off()
        if not success:
            Debug.tee('failed move off')
            Debug.diamond(Color.YELLOW)

        if BuildManager.can_build_foundry(pos, *a):
            Globals.ct.build_foundry(pos, *a)


    @staticmethod
    def can_dbuild_foundry(pos) -> bool:
            
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            not Map.tile_info[pos.x][pos.y].has_bot and
            BuildManager.can_afford_foundry(pos)
        )

    @staticmethod
    def can_build_foundry(*a) -> bool:
        return Globals.ct.can_build_foundry(*a)

    @staticmethod
    def can_afford_foundry(pos=None) -> bool:

        ti_cost, ax_cost = Globals.ct.get_foundry_cost()
        

        leftover_unscaled_ti = 0

        leftover_unscaled_ti += 0

        
        return (MarketMaker.ti - ti_cost) >= int(leftover_unscaled_ti * MarketMaker.scale_ratio) \
            and MarketMaker.ax >= ax_cost




    @staticmethod
    def build_road(*a):
        Globals.ct.build_road(*a)

    @staticmethod
    def dbuild_road(pos, *a):
        if Globals.ct.can_destroy(pos):
            BuildManager.destroy(pos)
        Globals.ct.build_road(pos, *a)


    @staticmethod
    def can_mbuild_road() -> bool:
        # assert EntityType.ROAD in Constants.PASSABLE_SET  remove because changed
        pos = Globals.my_pos

        ct = Globals.ct

        return (
            (ct.can_destroy(pos) or Map.tile_info[pos.x][pos.y].entity_type is None) and
            ct.get_action_cooldown() == 0 and
            ct.get_move_cooldown() == 0 and
            BuildManager.can_afford_road(pos)
        )


    @staticmethod
    def can_smartbuild_road(pos) -> bool:
        if pos == Globals.my_pos:
            return BuildManager.can_mbuild_road()
        return BuildManager.can_dbuild_road(pos)

    @staticmethod
    def smartbuild_road(pos, *a):
        if pos == Globals.my_pos:
            BuildManager.mbuild_road(*a)
            return 
        BuildManager.dbuild_road(pos, *a)


    @staticmethod
    def mbuild_road(*a):
        pos = Globals.my_pos
        if Globals.ct.can_destroy(pos):
            BuildManager.destroy(pos)


        if BuildManager.can_build_road(pos, *a):
            Globals.ct.build_road(pos, *a)


    @staticmethod
    def can_dbuild_road(pos) -> bool:
        if pos == Globals.my_pos:
            return BuildManager.can_mbuild_road()
            
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            BuildManager.can_afford_road(pos)
        )

    @staticmethod
    def can_build_road(*a) -> bool:
        return Globals.ct.can_build_road(*a)

    @staticmethod
    def can_afford_road(pos=None) -> bool:

        ti_cost, ax_cost = Globals.ct.get_road_cost()
        

        leftover_unscaled_ti = 0

        if Globals.round > 50:
            leftover_unscaled_ti += 20

        if pos is not None:
            leftover_unscaled_ti += Util.linf(pos, Unit.core_pos) * 2
        
        return (MarketMaker.ti - ti_cost) >= int(leftover_unscaled_ti * MarketMaker.scale_ratio) \
            and MarketMaker.ax >= ax_cost




    @staticmethod
    def build_barrier(*a):
        Globals.ct.build_barrier(*a)

    @staticmethod
    def dbuild_barrier(pos, *a):
        if Globals.ct.can_destroy(pos):
            BuildManager.destroy(pos)
        Globals.ct.build_barrier(pos, *a)


    @staticmethod
    def can_mbuild_barrier() -> bool:
        # assert EntityType.BARRIER in Constants.PASSABLE_SET  remove because changed
        pos = Globals.my_pos

        ct = Globals.ct

        return (
            (ct.can_destroy(pos) or Map.tile_info[pos.x][pos.y].entity_type is None) and
            ct.get_action_cooldown() == 0 and
            ct.get_move_cooldown() == 0 and
            BuildManager.can_afford_barrier(pos)
        )


    @staticmethod
    def can_smartbuild_barrier(pos) -> bool:
        if pos == Globals.my_pos:
            return BuildManager.can_mbuild_barrier()
        return BuildManager.can_dbuild_barrier(pos)

    @staticmethod
    def smartbuild_barrier(pos, *a):
        if pos == Globals.my_pos:
            BuildManager.mbuild_barrier(*a)
            return 
        BuildManager.dbuild_barrier(pos, *a)


    @staticmethod
    def mbuild_barrier(*a):
        pos = Globals.my_pos
        if Globals.ct.can_destroy(pos):
            BuildManager.destroy(pos)

        success = Pathfinder.move_off()
        if not success:
            Debug.tee('failed move off')
            Debug.diamond(Color.YELLOW)

        if BuildManager.can_build_barrier(pos, *a):
            Globals.ct.build_barrier(pos, *a)


    @staticmethod
    def can_dbuild_barrier(pos) -> bool:
            
        return (
            Globals.ct.get_action_cooldown() == 0 and
            BuildManager.is_dbuildable(pos) and 
            not Map.tile_info[pos.x][pos.y].has_bot and
            BuildManager.can_afford_barrier(pos)
        )

    @staticmethod
    def can_build_barrier(*a) -> bool:
        return Globals.ct.can_build_barrier(*a)

    @staticmethod
    def can_afford_barrier(pos=None) -> bool:

        ti_cost, ax_cost = Globals.ct.get_barrier_cost()
        

        leftover_unscaled_ti = 0

        leftover_unscaled_ti += 40

        
        return (MarketMaker.ti - ti_cost) >= int(leftover_unscaled_ti * MarketMaker.scale_ratio) \
            and MarketMaker.ax >= ax_cost




    @staticmethod
    def destroy(pos):
        # Debug.diamond(Color.RED, pos)
        Globals.ct.destroy(pos)

    @staticmethod
    def should_build_armoured(pos):



        return (min(pos.distance_squared(Unit.core_pos), pos.distance_squared(Symmetry.enemy_core_pos)) <= 20) or Map.tile_info[pos.x][pos.y].harvester_adjacent



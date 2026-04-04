#core.py
from cambc import *
from utils.constants import Constants
import random

class Core:
    num_spawned = 0
    ticks = 0
    last_spawn_tick = -9999
    danger = False
    
    @staticmethod
    def tick(ct: Controller) -> None:
        Core.ticks += 1
        width = ct.get_map_width()
        height = ct.get_map_height()
        pos = ct.get_position()
        
        if(Core.danger == False and ct.get_hp() < GameConstants.CORE_MAX_HP):
            Core.danger = True
            if Core.smart_spawn(ct, pos, width, height):
                    Core.last_spawn_tick = Core.ticks
        if ct.get_hp() == GameConstants.CORE_MAX_HP:
            Core.danger = False

        if(Core.ticks <= 4):
            if Core.smart_spawn(ct, pos, width, height):
                Core.last_spawn_tick = Core.ticks
    

        current_titanium = ct.get_global_resources()[0]
        bot_cost = ct.get_builder_bot_cost()[0]      

        if(Core.ticks < 50):
            pass # don't do anything
        else:
            if current_titanium > bot_cost + ct.get_foundry_cost()[0]:
                # 2-tick cooldown to prevent units spawning on top of each other
                if (Core.ticks - Core.last_spawn_tick) >= 2:
                    if Core.smart_spawn(ct, pos, width, height):
                        Core.last_spawn_tick = Core.ticks

    @staticmethod
    def smart_spawn(ct: Controller, pos: Position, width: int, height: int) -> bool:
        dirs = list(Constants.DIRECTIONS)
        random.shuffle(dirs)

        # Pure random for first 3 spawns
        if Core.num_spawned < 3:
            for d in dirs:
                spawn_pos = pos.add(d)
                if ct.can_spawn(spawn_pos):
                    ct.spawn_builder(spawn_pos)
                    Core.num_spawned += 1
                    return True
            return False

        best_dir = None
        best_score = -1
        
        for d in dirs:
            spawn_pos = pos.add(d)
            if not ct.can_spawn(spawn_pos):
                continue
                
            score = 0
            if d == Direction.NORTH: score = pos.y
            elif d == Direction.SOUTH: score = height - pos.y
            elif d == Direction.WEST: score = pos.x
            elif d == Direction.EAST: score = width - pos.x
            
            if score > best_score:
                best_score = score
                best_dir = d
                
        if best_dir is not None:
            ct.spawn_builder(pos.add(best_dir))
            Core.num_spawned += 1
            return True
            
        return False
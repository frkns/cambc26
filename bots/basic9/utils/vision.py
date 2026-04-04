from cambc import *
from bots.basic9.utils.constants import DIRECTIONS, CARDINAL_DIRECTIONS, CONVEYORS, WALKABLE, TURRETS
import random


class Symmetry(Enum):
    ROTATIONAL = "rotational"
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class Vision:
    def __init__(self, ct: Controller):
        self.c = ct
        self.mapwidth = ct.get_map_width()
        self.mapheight = ct.get_map_height()
        self.mapdata = {}
        self.walkable = set()
        self.empty = set()
        self.etype = {}
        self.friendly = {}
        self.conveyors = set()
        self.bridges = set()
        self.empty_ores = set()
        self.harvester_ores = set()
        self.unconnected_harvesters = set()
        self.core_loc = None

        self.symmetry = -1
        self.symmetries = {Symmetry.HORIZONTAL, Symmetry.VERTICAL, Symmetry.ROTATIONAL}

        # attack logic
        self.global_harvesters = set()
        self.global_enemy_harvesters = set()
        self.priority_attack = set()
        self.enemy_core_loc = None
        self.sentinel_placements = set()
        self.enemy_core_targets = set()
        self.global_friendly_sentinels = set()

        # defense logic
        self.needs_defend = {}
        self.positions_with_adjacent_harvesters = set()
        self.positions_with_adjacent_enemy_harvesters = set()
        self.friendly_harvesters = set()
        self.patrol_harvester = None
        self.enemy_sentinels = set()
        self.sentinel_defense_placements = set()
        self.change_orientation = set()

        for eid in ct.get_nearby_units():
            if (
                ct.get_entity_type(eid) == EntityType.CORE
                and ct.get_team(eid) == ct.get_team()
            ):
                self.core_loc = ct.get_position(eid)

        if self.c.get_entity_type() == EntityType.BUILDER_BOT:
            self.potential_enemy_core = self.rotations(self.core_loc)

        if self.c.get_entity_type() not in [EntityType.LAUNCHER, EntityType.SENTINEL]:
            core_pos = self.core_loc

            cx, cy = core_pos.x, core_pos.y

            targets = []
            for dx, dy in [
                (-1, -1),
                (-1, 0),
                (-1, 1),
                (0, -1),
                (0, 0),
                (0, 1),
                (1, -1),
                (1, 0),
                (1, -1),
            ]:
                targets.append(Position(cx + dx, cy + dy))

            self.core_targets = targets
            
            
    def best_sentinel_dir(self, pos: Position):
        best_score = 39
        best_dir = None
        for d in DIRECTIONS:
            if self.etype.get(pos.add(d), -1) == EntityType.HARVESTER:
                continue

            score = 0
            has_core = False
            for target in self.c.get_attackable_tiles_from(pos, d, EntityType.SENTINEL):
                if self.etype.get(target, -1) == -1:
                    continue
                if self.friendly[target]:
                    continue

                if self.etype[target] == EntityType.CORE:
                    has_core = True
                elif self.etype[target] in TURRETS:
                    score += 50
                elif self.etype[target] in CONVEYORS:
                    score += 40
                else:
                    score += 1
                    
            if has_core:
                score += 100

            if score > best_score:
                best_score = score
                best_dir = d

        return best_dir

    def squares_within_dist(self, pos: Position, d: int):
        res = []
        # Calculate bounding box to avoid checking entire map
        max_offset = int(d**0.5) + 1
        x_min = max(0, pos.x - max_offset)
        x_max = min(self.mapwidth - 1, pos.x + max_offset)
        y_min = max(0, pos.y - max_offset)
        y_max = min(self.mapheight - 1, pos.y + max_offset)

        for x in range(x_min, x_max + 1):
            for y in range(y_min, y_max + 1):
                p = Position(x, y)
                if p.distance_squared(pos) <= d:
                    res.append(p)

        return res

    def is_core(self, pos: Position):
        return self.core_loc.distance_squared(pos) <= 2

    def randomdir(self, pos: Position):
        return pos.add(DIRECTIONS[random.randint(0, 7)])

    def in_bounds(self, pos: Position):
        return 0 <= pos.x < self.mapwidth and 0 <= pos.y < self.mapheight

    def enemy_surrounded(self, pos: Position):
        for d in CARDINAL_DIRECTIONS:
            if (
                self.in_bounds(pos.add(d))
                and self.c.is_in_vision(pos.add(d))
                and self.mapdata.get(pos, -1) != Environment.WALL
            ):
                bid = self.c.get_tile_building_id(pos.add(d))
                if bid is None or (
                    bid is not None
                    and self.c.is_in_vision(pos.add(d))
                    and self.c.get_team(bid) == self.c.get_team()
                ):
                    return False

        return True

    def not_claimed(self, pos: Position):
        for d in CARDINAL_DIRECTIONS:
            if pos.add(d) in self.conveyors or pos.add(d) in self.bridges:
                return False

        return True

    def adj(self, pos: Position):
        res = []
        for d in CARDINAL_DIRECTIONS:
            if self.in_bounds(pos.add(d)):
                res.append(pos.add(d))
        return res

    def adj8(self, pos: Position):
        res = []
        for d in DIRECTIONS:
            if self.in_bounds(pos.add(d)):
                res.append(pos.add(d))

        return res

    def rotations(self, pos: Position):
        return [
            Position(pos.x, self.mapheight - pos.y - 1),
            Position(self.mapwidth - pos.x - 1, pos.y),
            Position(self.mapwidth - pos.x - 1, self.mapheight - pos.y - 1),
        ]

    def get_random_nearby_tile(self, pos: Position):
        res = Position(
            random.randint(pos.x - 7, pos.x + 7), random.randint(pos.y - 7, pos.y + 7)
        )
        while not self.in_bounds(res):
            res = Position(
                random.randint(pos.x - 7, pos.x + 7),
                random.randint(pos.y - 7, pos.y + 7),
            )

        return res

    def update(self):
        # update env states
        self.needs_defend = {}
        
        # Cache repetitive calls to self.c outside the loop
        nearby_tiles = self.c.get_nearby_tiles()
        bot_entity_type = self.c.get_entity_type()
        current_team = self.c.get_team()
        bot_position = self.c.get_position()

        for pos in nearby_tiles:
            if bot_entity_type == EntityType.BUILDER_BOT:
                current_env = self.c.get_tile_env(pos)
                if self.mapdata.get(pos, -1) != current_env:
                    self.mapdata[pos] = current_env

                # Cache per-position calls to self.c
                pos_bid = self.c.get_tile_building_id(pos)
                pos_is_empty = self.c.is_tile_empty(pos)
                pos_is_passable = self.c.is_tile_passable(pos)
                pos_is_in_vision = self.c.is_in_vision(pos)
                
                if pos_bid is not None:
                    pos_bid_ent_type = self.c.get_entity_type(pos_bid)
                    pos_bid_team = self.c.get_team(pos_bid)
                else:
                    pos_bid_ent_type = None
                    pos_bid_team = None

                if self.mapdata[pos] != Environment.WALL and (
                    pos_bid is None
                    or pos_bid in WALKABLE
                ):
                    self.walkable.add(pos)
                elif pos in self.walkable:
                    self.walkable.remove(pos)

                if pos_is_empty:
                    self.empty.add(pos)
                elif pos in self.empty:
                    self.empty.remove(pos)

                if self.symmetry == -1:
                    for otherpos, symtype in [
                        (
                            Position(pos.x, self.mapheight - pos.y - 1),
                            Symmetry.VERTICAL,
                        ),
                        (
                            Position(self.mapwidth - pos.x - 1, pos.y),
                            Symmetry.HORIZONTAL,
                        ),
                        (
                            Position(
                                self.mapwidth - pos.x - 1, self.mapheight - pos.y - 1
                            ),
                            Symmetry.ROTATIONAL,
                        ),
                    ]:
                        if (
                            self.mapdata.get(otherpos, -1) != -1
                            and self.mapdata[otherpos] != self.mapdata[pos]
                        ):
                            if symtype in self.symmetries:
                                self.symmetries.remove(symtype)

                        if len(self.symmetries) == 1:
                            self.symmetry = list(self.symmetries)[0]
                            if self.symmetry == Symmetry.ROTATIONAL:
                                self.enemy_core_loc = Position(
                                    self.mapwidth - self.core_loc.x - 1,
                                    self.mapheight - self.core_loc.y - 1,
                                )
                            elif self.symmetry == Symmetry.HORIZONTAL:
                                self.enemy_core_loc = Position(
                                    self.mapwidth - self.core_loc.x - 1, self.core_loc.y
                                )
                            else:
                                self.enemy_core_loc = Position(
                                    self.core_loc.x,
                                    self.mapheight - self.core_loc.y - 1,
                                )
                                
                if self.mapdata.get(pos, -1) == Environment.ORE_TITANIUM:
                    bid = pos_bid
                    if bid is None or (
                        pos_bid_ent_type != EntityType.HARVESTER
                        and pos_bid_team == current_team
                    ):
                        self.empty_ores.add(pos)
                    elif (
                        bid is not None
                        and pos_bid_ent_type == EntityType.HARVESTER
                        and pos_bid_team == current_team
                    ):
                        self.harvester_ores.add(pos)
                        if pos in self.empty_ores:
                            self.empty_ores.remove(pos)

                if (bid := pos_bid) is not None:
                    self.etype[pos] = pos_bid_ent_type
                    self.friendly[pos] = (pos_bid_team == current_team)

                if (
                    self.etype.get(pos, -1) == EntityType.SENTINEL
                    and pos_bid_team != current_team
                ):
                    self.enemy_sentinels.add(pos)
                    
                if self.etype.get(pos, -1) == EntityType.SENTINEL and self.friendly.get(pos, False):
                    self.global_friendly_sentinels.add(pos)
                    
                if (
                    (
                        pos_is_empty
                        or self.friendly.get(pos, False)
                        or pos_is_passable
                    )
                    and pos in self.positions_with_adjacent_enemy_harvesters
                    and not (
                        self.etype.get(pos, -1) == EntityType.SENTINEL
                        and self.friendly.get(pos, False)
                    )
                    or (
                        pos_is_in_vision
                        and pos_is_passable
                        and (
                            (
                                pos_bid_ent_type == EntityType.BRIDGE
                                and self.c.get_bridge_target(pos_bid) in self.enemy_core_targets
                            )
                            or pos_bid_ent_type == EntityType.CONVEYOR
                            and pos.add(self.c.get_direction(pos_bid)) in self.enemy_core_targets
                        )
                    )
                ) and (self.c.get_cpu_time_elapsed() < 1900 or self.best_sentinel_dir(pos) is not None):
                    self.sentinel_placements.add(pos)
                elif pos in self.sentinel_placements:
                    self.sentinel_placements.remove(pos)
                    

                addedthingy = False
                if (
                    pos_is_empty
                    or self.friendly.get(pos, False)
                    or pos_is_passable
                ):
                    if pos in self.positions_with_adjacent_harvesters:
                        harv = None
                        for d in CARDINAL_DIRECTIONS:
                            if self.etype.get(pos.add(d), -1) == EntityType.HARVESTER:
                                harv = pos.add(d)
                                break

                        if harv is not None:
                            for d in CARDINAL_DIRECTIONS:
                                if self.etype.get(
                                    pos.add(d), -1
                                ) == EntityType.SENTINEL and not self.friendly.get(
                                    pos.add(d), -1
                                ):
                                    self.sentinel_defense_placements.add(pos)
                                    addedthingy = True

                if not addedthingy and pos in self.sentinel_defense_placements:
                    self.sentinel_defense_placements.remove(pos)
                    
                if pos in self.potential_enemy_core:
                    if self.etype.get(pos, -1) != EntityType.CORE or self.friendly.get(
                        pos, -1
                    ):
                        self.potential_enemy_core.remove(pos)

                    if self.etype.get(
                        pos, -1
                    ) == EntityType.CORE and not self.friendly.get(pos, -1):
                        self.enemy_core_loc = self.c.get_position(pos_bid)
                        self.potential_enemy_core = {self.enemy_core_loc}

                if bid is None:
                    continue

                if self.etype.get(pos, -1) == EntityType.CONVEYOR and self.friendly.get(
                    pos, -1
                ):
                    self.conveyors.add(pos)
                elif pos in self.conveyors:
                    self.conveyors.remove(pos)

                if self.etype.get(pos, -1) == EntityType.BRIDGE and self.friendly.get(
                    pos, -1
                ):
                    self.bridges.add(pos)
                elif pos in self.bridges:
                    self.bridges.remove(pos)
                    
                if pos in self.enemy_sentinels:
                    for d in CARDINAL_DIRECTIONS:
                        ewreqwcr = False
                        pos_add_d = pos.add(d)
                        in_vision = self.c.is_in_vision(pos_add_d)
                        # Walrus operator ensures evaluation only executes when in vision
                        if (
                            in_vision
                            and self.in_bounds(pos_add_d)
                            and self.c.is_in_vision(pos_add_d)
                            and self.c.get_entity_type(add_d_bid := self.c.get_tile_building_id(pos_add_d)) == EntityType.CONVEYOR
                            and in_vision
                            and pos_add_d.add(self.c.get_direction(add_d_bid)) == pos
                        ):
                            self.change_orientation.add(pos_add_d)
                            ewreqwcr = True

                        if not ewreqwcr and pos_add_d in self.change_orientation:
                            self.change_orientation.remove(pos_add_d)

                pos_hp = self.c.get_hp(bid)
                pos_max_hp = self.c.get_max_hp(bid)

                if (
                    self.friendly[pos]
                    and (pos in self.conveyors or pos in self.bridges)
                    and pos_hp < pos_max_hp
                ):
                    self.needs_defend[pos] = pos_max_hp - pos_hp

                if (
                    self.friendly[pos]
                    and pos in self.positions_with_adjacent_harvesters
                    and pos_max_hp - pos_hp > 0
                ):
                    self.needs_defend[pos] = pos_max_hp - pos_hp

                if (
                    pos in self.core_targets
                    and pos_max_hp - pos_hp > 0
                ):
                    self.needs_defend[pos] = pos_max_hp - pos_hp

                if (
                    pos_bid_team != current_team
                    and self.etype.get(pos, -1) == EntityType.CORE
                ):
                    self.enemy_core_loc = self.c.get_position(bid)
                    
                my_team = current_team

                bid = pos_bid
                if bid is None:
                    continue

                entity_type = pos_bid_ent_type
                team = pos_bid_team
                friendly = (team == my_team)

                self.etype[pos] = entity_type
                self.friendly[pos] = friendly

                if entity_type == EntityType.HARVESTER:
                    self.global_harvesters.add(pos)

                    if friendly:
                        self.friendly_harvesters.add(pos)
                        if pos in self.global_enemy_harvesters:
                            self.global_enemy_harvesters.remove(pos)
                    else:
                        self.global_enemy_harvesters.add(pos)
                        if pos in self.friendly_harvesters:
                            self.friendly_harvesters.remove(pos)

                if not friendly:
                    added = False

                    for d in CARDINAL_DIRECTIONS:
                        adj_pos = pos.add(d)
                        if not self.in_bounds(adj_pos):
                            continue

                        if (
                            adj_pos in self.global_harvesters
                            and pos not in self.global_harvesters
                            and (
                                pos_is_passable
                                or bot_position == pos
                            )
                        ):
                            if entity_type in CONVEYORS:
                                self.priority_attack.add(pos)
                            added = True
                            break
                        
                    if (pos_bid_ent_type == EntityType.CONVEYOR and pos_is_in_vision and pos.add(self.c.get_direction(pos_bid)) in self.enemy_core_targets) or (pos_bid_ent_type == EntityType.BRIDGE and pos_is_in_vision and self.c.get_bridge_target(pos_bid) in self.enemy_core_targets):
                        self.priority_attack.add(pos)
                        added = True

                    if not added and pos in self.priority_attack:
                        self.priority_attack.remove(pos)

                elif pos in self.priority_attack:
                    self.priority_attack.remove(pos)

        # Update positions with adjacent harvesters based on known harvesters
        visible_tiles = set(nearby_tiles)

        # Keep positions outside vision, clear those in vision
        self.positions_with_adjacent_harvesters = {
            pos
            for pos in self.positions_with_adjacent_harvesters
            if pos not in visible_tiles
        }
        self.positions_with_adjacent_enemy_harvesters = {
            pos
            for pos in self.positions_with_adjacent_enemy_harvesters
            if pos not in visible_tiles
        }

        # Add all positions adjacent to known harvesters
        for harvester in self.global_harvesters:
            for d in CARDINAL_DIRECTIONS:
                adjacent_pos = harvester.add(d)
                if self.in_bounds(adjacent_pos):
                    self.positions_with_adjacent_harvesters.add(adjacent_pos)

        # Add all positions adjacent to known enemy harvesters
        for harvester in self.global_enemy_harvesters:
            for d in CARDINAL_DIRECTIONS:
                adjacent_pos = harvester.add(d)
                if self.in_bounds(adjacent_pos):
                    self.positions_with_adjacent_enemy_harvesters.add(adjacent_pos)

        # Update patrol target for defenders
        if self.friendly_harvesters:
            if self.patrol_harvester not in self.friendly_harvesters:
                self.patrol_harvester = random.choice(list(self.friendly_harvesters))
        else:
            self.patrol_harvester = None

        for ore in self.harvester_ores:
            if self.not_claimed(ore) and not self.enemy_surrounded(ore):
                self.unconnected_harvesters.add(ore)
            elif ore in self.unconnected_harvesters:
                self.unconnected_harvesters.remove(ore)

        if bot_entity_type == EntityType.BUILDER_BOT:
            if len(self.potential_enemy_core) == 1:
                self.enemy_core_loc = next(iter(self.potential_enemy_core))

        if not self.enemy_core_targets and self.enemy_core_loc:
            core_pos = self.enemy_core_loc

            cx, cy = core_pos.x, core_pos.y

            targets = []
            for dx, dy in [
                (-1, -1),
                (-1, 0),
                (-1, 1),
                (0, -1),
                (0, 0),
                (0, 1),
                (1, -1),
                (1, 0),
                (1, -1),
            ]:
                targets.append(Position(cx + dx, cy + dy))

            self.enemy_core_targets = targets
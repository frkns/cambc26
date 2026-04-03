#utils/nav.py
from cambc import *
from utils.constants import Constants
import random
import math
from utils.building import Building
from collections import deque

def dist_sq(p1, p2):
    return (p1.x - p2.x)**2 + (p1.y - p2.y)**2

SYM_HORIZONTAL = 'horizontal'   # (x, y)  →  (x,       H−1−y)
SYM_VERTICAL   = 'vertical'     # (x, y)  →  (W−1−x,   y    )
SYM_ROTATIONAL = 'rotational'   # (x, y)  →  (W−1−x,   H−1−y)
ALL_SYMMETRIES = {SYM_HORIZONTAL, SYM_VERTICAL, SYM_ROTATIONAL}

class Nav:
    CLEAR_MAP = [Constants.tiles.UNKNOWN] * (100 * 100)  # Placeholder for a max map size of 100x100
    REGION_SIZE = 5  # Adjust based on map scale (e.g., 10x10 tiles per region)
    BFS_STUCK_THRESHOLD   = 3          # hand off to DistBug after this many stuck ticks
    CAN_BUILD_ROAD_ON = [Constants.tiles.EMPTY, Constants.tiles.ORE_TITANIUM, Constants.tiles.ORE_AXIONITE, Constants.tiles.UNKNOWN]

    def __init__(self, ct):
        self.ct = ct
        self.width = ct.get_map_width()
        self.height = ct.get_map_height()
        
        # Initialize map arrays
        Nav.CLEAR_MAP = [Constants.tiles.UNKNOWN] * (self.width * self.height)
        self.envMap = Nav.CLEAR_MAP.copy()
        self.buildMap = Nav.CLEAR_MAP.copy()
        self.botsMap = Nav.CLEAR_MAP.copy()
        self.enemyThings = Nav.CLEAR_MAP.copy()
        self.nodes = []
        self.core = []
        self.enemyCore = []
        
        # Region Tracking Logic
        self.grid_w = math.ceil(self.width / self.REGION_SIZE)
        self.grid_h = math.ceil(self.height / self.REGION_SIZE)
        # Array of booleans: True if region is fully explored (no UNKNOWNs)
        self.scanned_regions = [False] * (self.grid_w * self.grid_h)

        self.bots = [] 
        self.target = None
        self.mode = 0 
        self.bug_sweep_start = 0
        self.bug_closest_dist = 10**9
        self.cw_dirs = None

        # NEW: Track whether the current bug mode was triggered by a bot (vs a real wall)
        self.bug_triggered_by_bot = False

        self.DA_SPLITTER = []
        self.nodeToSplitter = []
        self.FOUNDRIES = []
        self.NOROUTE = []

        self.history = []

        self.symmetry: str | None = None          # confirmed type, or None
        self.symmetry_candidates: set = set(ALL_SYMMETRIES)
        self._bfs_path        = []
        self._bfs_target      = None
        self._bfs_stuck_ticks = 0          # consecutive ticks we failed to execute BFS step
        self._bfs_path   = []    # list of (x, y) waypoints excl. current pos
        self._bfs_target = None  # Position the cached path was planned for

        self.titaniumOres = {}  # (x, y) -> 'A' available | 'R' routed | 'X' inaccessible
        self.axioniteOres = {}  # (x, y) -> 'A' available | 'R' routed | 'X' inaccessible
        self.hasSupplyToCore = False


    # ══════════════════════════════════════════════════════════════════════════════
    #  SYMMETRY DEDUCTION
    # ══════════════════════════════════════════════════════════════════════════════

    def _mirror(self, pos, sym: str):
        """
        Returns the mirror Position of `pos` under the given symmetry type.
        All three symmetry types collapse to simple arithmetic — no trig needed.
        """
        if sym == SYM_HORIZONTAL:
            return Position(pos.x, self.height - 1 - pos.y)
        if sym == SYM_VERTICAL:
            return Position(self.width - 1 - pos.x, pos.y)
        # SYM_ROTATIONAL
        return Position(self.width - 1 - pos.x, self.height - 1 - pos.y)

    def _tiles_match(self, a, b) -> bool:
        """
        Two tile values are consistent if either is UNKNOWN, or they are equal.
        UNKNOWN tiles carry no evidence — we simply skip them.
        """
        unk = Constants.tiles.UNKNOWN
        return a == unk or b == unk or a == b

    def _check_tile_against_symmetry(self, pos, tile) -> None:
        """
        Called every time a non-UNKNOWN tile is first written into envMap.
        Eliminates any candidate symmetry that is contradicted by this tile,
        then locks in the symmetry when only one candidate survives.

        Cost: O(|candidates|) per call — at most 3 comparisons total per tile.
        """
        if self.symmetry is not None or not self.symmetry_candidates:
            # Already confirmed — the fast path in encodeTile handles propagation.
            return

        mirror_idx_cache = {}

        for sym in list(self.symmetry_candidates):          # iterate over a copy
            m = self._mirror(pos, sym)
            mirror_idx = m.y * self.width + m.x
            mirror_idx_cache[sym] = (m, mirror_idx)

            mirror_tile = self.envMap[mirror_idx]
            if not self._tiles_match(tile, mirror_tile):
                self.symmetry_candidates.discard(sym)

        if len(self.symmetry_candidates) == 1:
            self.symmetry = next(iter(self.symmetry_candidates))
            self._on_symmetry_confirmed()

    def _on_symmetry_confirmed(self) -> None:
        sym = self.symmetry
        print(f"[Nav] Symmetry confirmed: {sym}")

        for idx in range(self.width * self.height):
            tile = self.envMap[idx]
            if tile == Constants.tiles.UNKNOWN:
                continue
            x = idx % self.width
            y = idx // self.width
            m = self._mirror(Position(x, y), sym)
            midx = m.y * self.width + m.x
            if self.envMap[midx] == Constants.tiles.UNKNOWN:
                self.envMap[midx] = tile

        # ── NEW: mirror already-scanned regions ──────────────────────────────
        for ry in range(self.grid_h):
            for rx in range(self.grid_w):
                if not self.scanned_regions[ry * self.grid_w + rx]:
                    continue
                # pick the center tile of this region and mirror it
                cx = min(rx * self.REGION_SIZE + self.REGION_SIZE // 2, self.width - 1)
                cy = min(ry * self.REGION_SIZE + self.REGION_SIZE // 2, self.height - 1)
                m  = self._mirror(Position(cx, cy), sym)
                mrx = m.x // self.REGION_SIZE
                mry = m.y // self.REGION_SIZE
                if 0 <= mrx < self.grid_w and 0 <= mry < self.grid_h:
                    self.scanned_regions[mry * self.grid_w + mrx] = True
        # ── END NEW ──────────────────────────────────────────────────────────

        # rebuild scanned_regions for tiles just propagated
        for ry in range(self.grid_h):
            for rx in range(self.grid_w):
                if not self.scanned_regions[ry * self.grid_w + rx]:
                    if self._is_region_cleared(rx, ry):
                        self.scanned_regions[ry * self.grid_w + rx] = True

        self._infer_enemy_core()

    def _infer_enemy_core(self) -> None:
        """
        Derives enemyCore positions from our own core using the confirmed symmetry.
        Safe to call multiple times — deduplicates automatically.
        """
        if self.symmetry is None or not self.core:
            return

        for core_pos in self.core:
            mirrored = self._mirror(core_pos, self.symmetry)
            if mirrored not in self.enemyCore:
                self.enemyCore.append(mirrored)
                print(f"[Nav] Inferred enemy core tile at {mirrored.x},{mirrored.y}")
    def _init_cw_dirs(self):
        """Sorts the 8 constants directions in a clockwise/counter-clockwise uniform circle"""
        if self.cw_dirs is not None:
            return
        p1 = self.ct.get_position()
        dirs = []
        for d in Constants.DIRECTIONS:
            p2 = p1.add(d)
            dx = p2.x - p1.x
            dy = p2.y - p1.y
            
            # Fallback in case of edge map boundary clamping on position evaluation
            if dx == 0 and dy == 0:
                name = str(d).upper()
                if 'NORTH' in name: dy = -1
                if 'SOUTH' in name: dy = 1
                if 'EAST' in name: dx = 1
                if 'WEST' in name: dx = -1
                
            angle = math.atan2(dy, dx)
            dirs.append((angle, d))
            
        dirs.sort()
        self.cw_dirs = [d for angle, d in dirs]
        
    def get_nearest_enemy_building(self, current_pos):
        """
        Scans the known buildMap and returns the Position of the 
        closest enemy building. Returns None if no enemy buildings are known.
        """
        best_dist = float('inf')
        nearest_pos = None
        my_team = self.ct.get_team()

        for idx, building in enumerate(self.buildMap):
            if building != Constants.tiles.UNKNOWN and building != 0 and building.is_passable():
                if hasattr(building, 'team') and building.team != my_team:
                    bx = idx % self.width
                    by = idx // self.width
                    d_sq = (current_pos.x - bx)**2 + (current_pos.y - by)**2
                    if d_sq < best_dist:
                        best_dist = d_sq
                        nearest_pos = Position(bx, by)

        return nearest_pos

    def getTile(self, pos):
        return self.envMap[pos.y * self.ct.get_map_width() + pos.x]

    def getBuilding(self, pos):
        return self.buildMap[pos.y * self.ct.get_map_width() + pos.x]

    def getBot(self, pos):
        return self.botsMap[pos.y * self.ct.get_map_width() + pos.x]

    def encodeTile(self, pos, tileType):
        """Updates a tile and checks if its parent region is now fully scanned."""
        idx = pos.y * self.width + pos.x

        # ── Symmetry: skip UNKNOWN tiles (carry no evidence)
        if tileType != Constants.tiles.UNKNOWN:
            self._check_tile_against_symmetry(pos, tileType)          # ← NEW

        self.envMap[idx] = tileType

        # ── Symmetry fast-path: if already confirmed, propagate immediately
        if self.symmetry is not None:                                  # ← NEW
            m = self._mirror(pos, self.symmetry)                       # ← NEW
            midx = m.y * self.width + m.x                             # ← NEW
            if self.envMap[midx] == Constants.tiles.UNKNOWN:          # ← NEW
                self.envMap[midx] = tileType                          # ← NEW
                rx, ry = m.x // self.REGION_SIZE, m.y // self.REGION_SIZE  # ← NEW
                r_idx = ry * self.grid_w + rx                         # ← NEW
                if not self.scanned_regions[r_idx] and self._is_region_cleared(rx, ry):  # ← NEW
                    self.scanned_regions[r_idx] = True                # ← NEW

        rx, ry = pos.x // self.REGION_SIZE, pos.y // self.REGION_SIZE
        region_idx = ry * self.grid_w + rx

        if not self.scanned_regions[region_idx]:
            if self._is_region_cleared(rx, ry):
                self.scanned_regions[region_idx] = True
                return True

    def _is_region_cleared(self, rx, ry):
        """Internal helper to check a 10x10 area for UNKNOWN tiles."""
        x_start, y_start = rx * self.REGION_SIZE, ry * self.REGION_SIZE
        x_end = min(x_start + self.REGION_SIZE, self.width)
        y_end = min(y_start + self.REGION_SIZE, self.height)

        for y in range(y_start, y_end):
            row_off = y * self.width
            for x in range(x_start, x_end):
                if self.envMap[row_off + x] == Constants.tiles.UNKNOWN:
                    return False
        return True
    
    def get_nearest_unknown_region_center(self, preferred_direction=None, threshold=100):
        """
        Returns the center Position of the closest incomplete region deterministically.
        Prefers candidates that align with 'preferred_direction'. 
        If multiple regions tie, or if no direction is given, it pseudo-randomly 
        (but deterministically) breaks ties using a spatial hash of the coordinates.
        """
        robot_pos = self.ct.get_position()
        best_dist = float('inf')
        
        candidates = []
        all_possible_centers = []

        # 1. Gather all candidates
        for ry in range(self.grid_h):
            for rx in range(self.grid_w):
                cx = min((rx * self.REGION_SIZE) + (self.REGION_SIZE // 2), self.width - 1)
                cy = min((ry * self.REGION_SIZE) + (self.REGION_SIZE // 2), self.height - 1)
                center_pos = Position(cx, cy)
                
                all_possible_centers.append(center_pos)

                if not self.scanned_regions[ry * self.grid_w + rx]:
                    dist_sq = (robot_pos.x - cx)**2 + (robot_pos.y - cy)**2
                    candidates.append((dist_sq, center_pos))
                    
                    if dist_sq < best_dist:
                        best_dist = dist_sq

        # 2. Filter down to valid options
        valid_options = []
        if candidates:
            valid_options = [
                pos for dist_sq, pos in candidates 
                if dist_sq <= best_dist + threshold
            ]
        elif all_possible_centers:
            valid_options = all_possible_centers
        else:
            return None

        # 3. Setup preferred direction vector
        dx, dy = 0, 0
        if preferred_direction:
            dir_vectors = {
                Direction.NORTH:     ( 0, -1),
                Direction.EAST:      ( 1,  0),
                Direction.SOUTH:     ( 0,  1),
                Direction.WEST:      (-1,  0),
                Direction.NORTHEAST: ( 1, -1),
                Direction.NORTHWEST: (-1, -1),
                Direction.SOUTHEAST: ( 1,  1),
                Direction.SOUTHWEST: (-1,  1)
            }
            dx, dy = dir_vectors[preferred_direction]

        # 4. Deterministic Scoring Function
        def get_score(pos):
            # -- Score Part A: Direction Alignment --
            dir_score = 0
            if preferred_direction:
                vx = pos.x - robot_pos.x
                vy = pos.y - robot_pos.y
                dist = math.hypot(vx, vy)
                if dist > 0:
                    # Dot product mapping to alignment (-1 to 1 for straight, up to 1.41 for diagonals)
                    dir_score = ((vx / dist) * dx) + ((vy / dist) * dy)
                else:
                    dir_score = -float('inf')

            # -- Score Part B: Spatial Hash (Pseudorandom Tie-Breaker) --
            # Mix the coordinates using large prime numbers.
            # This guarantees uniform scrambling that is 100% deterministic 
            # based solely on where the robot is and where the candidate is.
            p1, p2, p3, p4 = 73856093, 19349663, 83492791, 39916801
            
            # XOR bitwise mixing
            h = (pos.x * p1) ^ (pos.y * p2) ^ (robot_pos.x * p3) ^ (robot_pos.y * p4)
            hash_score = h % 1000000 
            
            # Python's max() will sort by the first item (Direction), 
            # and if they tie, fallback to the second item (Hash).
            return (dir_score, hash_score)

        # Return the position with the highest combined tuple score
        return max(valid_options, key=get_score)

    def moveRandomly(self):
        for d in Constants.DIRECTIONS:
            if self.ct.can_move(d):
                self.ct.move(d)
                break
        return self.ct.get_position()

    def encodeBuilding(self, pos, building):
        if building == 0:
            try: self.nodes.remove(pos)
            except ValueError: pass
        elif self.getBuilding(pos) != 0 and self.getBuilding(pos).entityType != building.entityType:
            try: self.nodes.remove(pos)
            except ValueError: pass
        self.buildMap[pos.y * self.ct.get_map_width() + pos.x] = building
        if(building == 0): return
        if not building.is_passable():
            self.ct.draw_indicator_dot(pos,0,255,0)
        if pos in self.DA_SPLITTER and (building.entityType not in [EntityType.ROAD,EntityType.SPLITTER] or building.team != self.ct.get_team()):
            self.DA_SPLITTER.remove(pos)
        if pos in self.FOUNDRIES and (building.entityType not in [EntityType.ROAD,EntityType.FOUNDRY, EntityType.BARRIER] or building.team != self.ct.get_team()):
            self.FOUNDRIES.remove(pos)
        if pos in self.NOROUTE and (building.entityType not in [EntityType.ROAD,EntityType.LAUNCHER, EntityType.BARRIER] or building.team != self.ct.get_team()):
            self.NOROUTE.remove(pos)

        if building.entityType == EntityType.BRIDGE and building.team != self.ct.get_team():
            thing = self.ct.get_bridge_target(building.id)
            self.enemyThings[thing.y * self.ct.get_map_width() + thing.x] += 1
        if building.entityType in [EntityType.CONVEYOR, EntityType.ARMOURED_CONVEYOR] and building.team != self.ct.get_team():
            dir = building.direction
            newPos = pos.add(dir)
            self.enemyThings[newPos.y * self.ct.get_map_width() + newPos.x] += 1

        if building.entityType in [EntityType.CONVEYOR,EntityType.ARMOURED_CONVEYOR] and building.team == self.ct.get_team():
            if building.direction is not None:
                next_pos = building.position.add(building.direction)
                if next_pos in self.core or next_pos in self.DA_SPLITTER:
                    self.hasSupplyToCore = True
        if building.entityType == EntityType.BRIDGE and building.team == self.ct.get_team():
            if building.target in self.core or building.target in self.DA_SPLITTER:
                self.hasSupplyToCore = True

        if building.entityType == EntityType.BRIDGE and building.team == self.ct.get_team():
            if building.position in self.nodes:
                return
            self.nodes.append(building.position)
            thing = self.ct.get_bridge_target(building.id)
            if thing in self.nodes:
                return
            self.nodes.append(thing)
        if building.entityType == EntityType.FOUNDRY and building.team == self.ct.get_team():
            if building.position in self.FOUNDRIES:
                return
            self.FOUNDRIES.append(building.position)
        if building.entityType in [EntityType.CONVEYOR,EntityType.ARMOURED_CONVEYOR] and building.team == self.ct.get_team():
            if building.position in self.nodes:
                return
            self.nodes.append(building.position)
        if building.entityType == EntityType.CORE and building.team != self.ct.get_team():
            if building.position in self.enemyCore:
                return
            self.enemyCore.append(building.position)
        if building.entityType == EntityType.CORE and building.team == self.ct.get_team():
            if building.position in self.core:
                return
            self.nodes.append(building.position)
            self.core.append(building.position)
        """
        if building.entityType == EntityType.SPLITTER and building.team == self.ct.get_team():
            if building.position not in self.DA_SPLITTER:
                self.DA_SPLITTER.append(building.position)
                self.nodeToSplitter.append(0)
        """

    def onMap(self, pos):
        if pos is None:
            return False
        return 0 <= pos.x < self.ct.get_map_width() and 0 <= pos.y < self.ct.get_map_height()

    def _is_bot_blocked(self, pos):
        """Returns True if this position is blocked exclusively by a bot (not a wall/building)."""
        if not self.onMap(pos):
            return False
        return self.botsMap[pos.y * self.width + pos.x] != Constants.tiles.UNKNOWN

    def is_passable(self, pos, noOnUnknown=False):
        if not self.onMap(pos):
            return False
        if self.botsMap[pos.y * self.ct.get_map_width() + pos.x] != Constants.tiles.UNKNOWN:
            self.ct.draw_indicator_dot(pos, 255, 0, 0)
            return False
        posBuilding = self.getBuilding(pos)
        if(self.getTile(pos) in [Constants.tiles.ORE_AXIONITE,Constants.tiles.ORE_TITANIUM] and ( posBuilding == 0 or posBuilding.is_passable())):
            return True
        if self.buildMap[pos.y * self.ct.get_map_width() + pos.x] != Constants.tiles.UNKNOWN and \
           self.buildMap[pos.y * self.ct.get_map_width() + pos.x].is_passable() == False:
            self.ct.draw_indicator_dot(pos, 150, 0, 0)
            return False

        tile = self.getTile(pos)
        if noOnUnknown:
            if tile == Constants.tiles.UNKNOWN:
                return False
        return tile != Constants.tiles.WALL and tile != Constants.tiles.ORE_TITANIUM and tile != Constants.tiles.ORE_AXIONITE

    def is_passable_ignoring_bots(self, pos, noOnUnknown=False):
        if not self.onMap(pos):
            return False
        
        posBuilding = self.getBuilding(pos)
        
        # --- ADD THIS BLOCK ---
        if self.getTile(pos) in[Constants.tiles.ORE_AXIONITE, Constants.tiles.ORE_TITANIUM]:
            if posBuilding == 0 or posBuilding == Constants.tiles.UNKNOWN or posBuilding.is_passable():
                return True
        # ----------------------

        if self.buildMap[pos.y * self.ct.get_map_width() + pos.x] != Constants.tiles.UNKNOWN and \
           self.buildMap[pos.y * self.ct.get_map_width() + pos.x].is_passable() == False:
            return False

        tile = self.getTile(pos)
        if noOnUnknown:
            if tile == Constants.tiles.UNKNOWN:
                return False
        return tile != Constants.tiles.WALL and tile != Constants.tiles.ORE_TITANIUM and tile != Constants.tiles.ORE_AXIONITE

    def get_enemy_core_center(self):
        """
        Returns the estimated center Position of the enemy core (a 3x3 area).
        If all tiles are known, the average gives the exact center.
        If only some tiles are known, the average is used as a best guess.
        Returns None if no enemy core tiles are known at all.
        """
        if not self.enemyCore:
            return None
        if(len(self.enemyCore)) == 0:
            return None

        avg_x = sum(p.x for p in self.enemyCore) / len(self.enemyCore)
        avg_y = sum(p.y for p in self.enemyCore) / len(self.enemyCore)

        return Position(round(avg_x), round(avg_y))

    def get_highest_enemy_thing_near_core(self, dist_sq_threshold=25):
        """
        Scans enemyThings for the nearest qualifying tile to the BOT 
        that is within dist_sq_threshold of the enemy core.
        """
        curr_pos = self.ct.get_position()
        best_dist = float('inf')
        best_pos = None

        for idx, count in enumerate(self.enemyThings):
            # Must have a nonzero score
            if count == 0:
                continue

            x = idx % self.width
            y = idx // self.width
            candidate_pos = Position(x, y)

            # 1. Proximity to Core Check
            # Check if this tile is near any known piece of the enemy core
            is_near_core = False
            for core_pos in self.enemyCore:
                d_to_core = (x - core_pos.x)**2 + (y - core_pos.y)**2
                # d > 0 ensures we aren't trying to build directly ON a core tile 
                # (unless your strategy allows overlapping)
                if 0 < d_to_core <= dist_sq_threshold:
                    is_near_core = True
                    break
            
            if not is_near_core:
                continue

            # 2. Validity Checks (Not blocked by walls or other bots)
            building = self.buildMap[idx]
            if building != Constants.tiles.UNKNOWN and building != 0:
                if not building.is_passable():
                    continue
            
            # Check botsMap for other units
            if self.botsMap[idx] != 0:
                continue

            # 3. Distance to Bot Check (The "Nearest" logic)
            d_to_bot = (x - curr_pos.x)**2 + (y - curr_pos.y)**2
            if d_to_bot < best_dist:
                best_dist = d_to_bot
                best_pos = candidate_pos

        return best_pos
    def dist_sq_to_nearest_enemy_core(self, pos):
        """
        Returns the squared distance from pos to the nearest known enemy core.
        Returns None if no enemy cores are known.
        """
        if not self.enemyCore:
            return None

        return min((pos.x - core_pos.x) ** 2 + (pos.y - core_pos.y) ** 2 for core_pos in self.enemyCore)

    def setup(self, ct: Controller):
        self.ct = ct
        self.botsMap = Nav.CLEAR_MAP.copy()
        self.bots = []
        self.enemyThings = Nav.CLEAR_MAP.copy()

    def moveTo(self, target):
        START = self.ct.get_cpu_time_elapsed()
        self._init_cw_dirs()
        if target is None:
            return
        print("Moving to:",target)

        robot_pos = self.ct.get_position()

        # ── Reset everything on target change ────────────────────────────────────
        target_changed = (
            self._bfs_target is None
            or self._bfs_target.x != target.x
            or self._bfs_target.y != target.y
        )
        if target_changed:
            self._bfs_target          = target
            self._bfs_path            = []
            self._bfs_stuck_ticks     = 0
            # Keep DistBug coherent for the fallback
            self.target               = target
            self.mode                 = 0
            self.bug_closest_dist     = 10**9
            self.bug_sweep_start      = 0
            self.bug_triggered_by_bot = False
            self.history              = []

        # ── Always keep DistBug target in sync (needed if BFS hands off mid-route)
        self.target = target

        # ── Consume waypoints we've already walked onto ───────────────────────────
        while self._bfs_path and self._bfs_path[0] == (robot_pos.x, robot_pos.y):
            self._bfs_path.pop(0)

        # ── Classify the next planned step ───────────────────────────────────────
        #    HARD block  = wall / impassable building → replan BFS from scratch
        #    SOFT block  = bot in the way             → keep plan, take detour
        if self._bfs_path:
            wx, wy      = self._bfs_path[0]
            next_pos    = Position(wx, wy)
            is_passable = self.is_passable(next_pos)

            if not is_passable:
                building = self.getBuilding(next_pos)
                # Check if it's our barrier
                is_friendly_barrier = (
                    building != 0 and 
                    building != Constants.tiles.UNKNOWN and 
                    building.entityType == EntityType.BARRIER and 
                    building.team == self.ct.get_team()
                )

                if is_friendly_barrier:
                    # Increment stuck ticks. The BFS decided this is the optimal route.
                    self._bfs_stuck_ticks += 1
                    # Visualize that we are "working" on the barrier
                    self.ct.draw_indicator_dot(next_pos, 255, 165, 0) # Orange
                    
                    if self._bfs_stuck_ticks >= self.BFS_STUCK_THRESHOLD:
                        if self.ct.can_destroy(next_pos):
                            self.ct.destroy(next_pos)
                            # Do NOT clear BFS path; the path is now clear to walk
                            self._bfs_stuck_ticks = 0
                elif self._is_bot_blocked(next_pos):
                    # It's just a bot, wait for it
                    self._bfs_stuck_ticks += 1
                else:
                    # Hard wall or enemy building - the weighted BFS path is now invalid
                    self._bfs_path = []
                    self._bfs_stuck_ticks = 0
            else:
                self._bfs_stuck_ticks = 0

        # ── If stuck by bots too long, hand off to DistBug for this tick ─────────
        if self._bfs_stuck_ticks >= self.BFS_STUCK_THRESHOLD:
            self._bfs_stuck_ticks = 0
            self._bfs_path        = []          # stale; replan fresh next tick
            self._bug_moveTo(robot_pos, target)
            return

        # ── Replan BFS when we have no valid path ─────────────────────────────────
        if not self._bfs_path:
            self._bfs_path = self._bfs_find_path(robot_pos, target)

        # ── No BFS path found (budget exceeded / map too unknown) → DistBug ───────
        if not self._bfs_path:
            self._bug_moveTo(robot_pos, target)
            return

        # ── Translate first waypoint → direction ──────────────────────────────────
        wx, wy   = self._bfs_path[0]
        move_dir = None
        for d in self.cw_dirs:
            p = robot_pos.add(d)
            if p.x == wx and p.y == wy:
                move_dir = d
                break

        # ── Next step is bot-blocked: take the best passable greedy detour ────────
        #    Don't clear the BFS path — we'll come back to it once the bot moves.
        if move_dir is not None and not self.is_passable(robot_pos.add(move_dir)):
            move_dir = None
            # Sort all 8 dirs by distance to *target* (not the waypoint) and
            # pick the closest passable one.  This keeps us making forward
            # progress rather than circling.
            dir_distances = sorted(
                ((dist_sq(robot_pos.add(d), target), i, d)
                for i, d in enumerate(self.cw_dirs)),
                key=lambda x: x[0]
            )
            for ds, i, d in dir_distances:
                if self.is_passable(robot_pos.add(d)):
                    move_dir = d
                    break

        # ── Final fallback: DistBug ───────────────────────────────────────────────
        if move_dir is None:
            self._bug_moveTo(robot_pos, target)
            return

        # ── Execute move (road-building logic preserved) ──────────────────────────
        move_pos = robot_pos.add(move_dir)
        self.ct.draw_indicator_dot(move_pos, 0, 0, 255)
        building = self.getBuilding(move_pos)
        if (building == 0
                or building == Constants.tiles.UNKNOWN
                or building.entityType == EntityType.MARKER):
            if (self.getTile(move_pos) in Nav.CAN_BUILD_ROAD_ON
                    and self.ct.can_build_road(move_pos)):
                self.ct.build_road(move_pos)
        if self.ct.can_move(move_dir):
            self.ct.move(move_dir)

        print("Pathfinding ran in:",self.ct.get_cpu_time_elapsed()-START)

    # ══════════════════════════════════════════════════════════════════════════
    #  BIDIRECTIONAL BFS
    # ══════════════════════════════════════════════════════════════════════════

    def _bfs_find_path(self, start, goal):
        """
        Weighted Search using Dial's Algorithm (Bucket Queue).
        Penalty for friendly barriers: 20.
        Uses collections.deque buckets to avoid heapq.
        """
        W, H = self.width, self.height
        si = start.y * W + start.x
        gi = goal.y * W + goal.x
        if si == gi:
            return []

        envMap = self.envMap
        buildMap = self.buildMap
        UNK = Constants.tiles.UNKNOWN
        WALL = Constants.tiles.WALL
        ORE_TI = Constants.tiles.ORE_TITANIUM
        ORE_AX = Constants.tiles.ORE_AXIONITE
        my_team = self.ct.get_team()

        # Costs: 1 for move, 20 for barrier. Max penalty is 20, so 21 buckets.
        num_buckets = 21
        buckets = [deque() for _ in range(num_buckets)]
        
        dists = [10**9] * (W * H)
        parents = [-1] * (W * H)
        
        dists[si] = 0
        buckets[0].append(si)
        
        curr_dist = 0
        nodes_processed = 0
        # Maximum distance we're willing to search to save CPU
        max_search_dist = 200 

        DIRS = ((-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(-1,1),(0,1),(1,1))

        while nodes_processed < (W * H):
            # Find the next non-empty bucket
            bucket_idx = curr_dist % num_buckets
            while not buckets[bucket_idx]:
                curr_dist += 1
                bucket_idx = curr_dist % num_buckets
                if curr_dist > max_search_dist or curr_dist > (dists[gi] if dists[gi] != 10**9 else 10**8):
                    break
            
            if not buckets[bucket_idx] or curr_dist > max_search_dist:
                break
            
            idx = buckets[bucket_idx].popleft()
            if idx == gi: break
            
            # CPU Safety
            if nodes_processed % 100 == 0 and self.ct.get_cpu_time_elapsed() > 1700:
                return []

            x, y = idx % W, idx // W
            for dx, dy in DIRS:
                nx, ny = x + dx, y + dy
                if 0 <= nx < W and 0 <= ny < H:
                    nidx = ny * W + nx
                    
                    # Determine weight
                    weight = 1
                    b = buildMap[nidx]
                    if b != UNK and b != 0 and not b.is_passable():
                        if b.entityType == EntityType.BARRIER and b.team == my_team:
                            weight = 20
                        elif nidx != gi:
                            continue
                    
                    if envMap[nidx] == WALL:
                        continue
                    
                    # ORE check
                    if (envMap[nidx] == ORE_TI or envMap[nidx] == ORE_AX) and weight == 1:
                        if not (b == UNK or b == 0 or b.is_passable()):
                            continue

                    new_dist = dists[idx] + weight
                    if new_dist < dists[nidx]:
                        dists[nidx] = new_dist
                        parents[nidx] = idx
                        buckets[new_dist % num_buckets].append(nidx)
            
            nodes_processed += 1

        if parents[gi] == -1:
            return []

        path = []
        curr = gi
        while curr != si:
            path.append((curr % W, curr // W))
            curr = parents[curr]
        path.reverse()
        return path

    # ══════════════════════════════════════════════════════════════════════════
    #  DISTBUG FALLBACK  (original moveTo logic, extracted verbatim)
    # ══════════════════════════════════════════════════════════════════════════

    def _bug_moveTo(self, robot_pos, target):
        """
        Original DistBug wall-follower, called when BFS cannot find a path.
        All logic is identical to the previous moveTo() — nothing changed.
        """
        curr_dist      = dist_sq(robot_pos, target)
        if curr_dist == 0:
            return

        curr_pos_tuple = (robot_pos.x, robot_pos.y)

        # ── Loop detector (bug mode only) ─────────────────────────────────────
        random_escape = False
        if self.mode == 1:
            if curr_pos_tuple in self.history:
                loop_length = len(self.history) - self.history.index(curr_pos_tuple)
                if loop_length >= 4:
                    self.mode             = 0
                    self.bug_triggered_by_bot = False
                    self.history.clear()
                    random_escape         = True
            if self.mode == 1:
                self.history.append(curr_pos_tuple)
                if len(self.history) > 50:
                    self.history.pop(0)
        else:
            self.history.clear()

        # ── Greedy direction ranking ──────────────────────────────────────────
        dir_distances = []
        for i, d in enumerate(self.cw_dirs):
            p = robot_pos.add(d)
            dir_distances.append((dist_sq(p, target), i, d))
        dir_distances.sort(key=lambda x: x[0])

        best_greedy_dist = dir_distances[0][0]
        best_greedy_dir  = dir_distances[0][2]
        best_greedy_idx  = dir_distances[0][1]
        move_dir         = None

        # ── Mode 0: greedy go-to-goal ─────────────────────────────────────────
        if self.mode == 0:
            if random_escape:
                passable_dirs = [d for ds, i, d in dir_distances
                                 if self.is_passable(robot_pos.add(d))]
                if passable_dirs:
                    move_dir = random.choice(passable_dirs)
            else:
                for ds, i, d in dir_distances:
                    if ds < curr_dist and self.is_passable(robot_pos.add(d)):
                        move_dir = d
                        break

            if move_dir is None:
                if best_greedy_dist == 0 and not self.is_passable(target):
                    return
                best_pos = robot_pos.add(best_greedy_dir)
                is_bot   = self._is_bot_blocked(best_pos)
                if is_bot and random.random() < 0.6:
                    passable = [d for ds, i, d in dir_distances
                                if self.is_passable(robot_pos.add(d))]
                    if passable and random.random() < 0.5:
                        move_dir = random.choice(passable)
                else:
                    self.mode                 = 1
                    self.bug_closest_dist     = curr_dist
                    self.bug_sweep_start      = best_greedy_idx
                    self.bug_triggered_by_bot = is_bot
                    self.history              = [curr_pos_tuple]

        # ── Mode 1: wall-following ────────────────────────────────────────────
        if self.mode == 1:

            # Bot-triggered escape
            if self.bug_triggered_by_bot:
                for ds, i, d in dir_distances:
                    if ds < curr_dist and self.is_passable(robot_pos.add(d)):
                        self.mode = 0; self.bug_triggered_by_bot = False
                        self.history.clear(); move_dir = d; break
                if move_dir is None and self.mode == 1:
                    best_pos = robot_pos.add(best_greedy_dir)
                    if not self._is_bot_blocked(best_pos) and self.is_passable(best_pos):
                        self.mode = 0; self.bug_triggered_by_bot = False
                        self.history.clear(); move_dir = best_greedy_dir

            # Standard DistBug escape (we physically got closer)
            if self.mode == 1 and move_dir is None:
                if curr_dist < self.bug_closest_dist:
                    self.mode = 0; self.bug_closest_dist = curr_dist
                    self.bug_triggered_by_bot = False; self.history.clear()
                    for ds, i, d in dir_distances:
                        if ds < curr_dist and self.is_passable(robot_pos.add(d)):
                            move_dir = d; break
                    if move_dir is None:
                        if best_greedy_dist == 0 and not self.is_passable(target):
                            return
                        self.mode            = 1
                        self.bug_sweep_start = best_greedy_idx
                        self.history         = [curr_pos_tuple]

            # Wall-follow sweep
            if self.mode == 1 and move_dir is None:
                sweep_order = list(range(8))
                if self.bug_triggered_by_bot:
                    non_bot, bot_only = [], []
                    for offset in range(8):
                        cp = robot_pos.add(self.cw_dirs[(self.bug_sweep_start + offset) % 8])
                        (bot_only if self._is_bot_blocked(cp)
                                  and self.is_passable_ignoring_bots(cp)
                         else non_bot).append(offset)
                    sweep_order = non_bot + bot_only

                moved = False
                for offset in sweep_order:
                    check_idx = (self.bug_sweep_start + offset) % 8
                    check_dir = self.cw_dirs[check_idx]
                    if self.is_passable(robot_pos.add(check_dir)):
                        move_dir             = check_dir
                        self.bug_sweep_start = (check_idx - 3) % 8
                        moved                = True; break
                if not moved:
                    return

        # ── Execute move ──────────────────────────────────────────────────────
        if move_dir is not None:
            move_pos = robot_pos.add(move_dir)
            self.ct.draw_indicator_dot(move_pos, 0, 0, 255)

            building = self.getBuilding(move_pos)
            if (building == 0 or building == Constants.tiles.UNKNOWN
                    or building.entityType == EntityType.MARKER):
                target_tile = self.getTile(move_pos)
                if (target_tile in Nav.CAN_BUILD_ROAD_ON
                        and self.ct.can_build_road(move_pos)):
                    self.ct.build_road(move_pos)
            if self.ct.can_move(move_dir):
                self.ct.move(move_dir)
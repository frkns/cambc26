from cambc import Controller, EntityType, Environment, Position
from heapq import heappush, heappop

from unit import Unit
from mapUtils import isMoveableDirection
from movementManager import lockMovement, tryMove
from data import DEBUG, DIRECTIONS, WALKABLE_ENTITIES, BARRIER_AND_WALKABLE_ENTITIES
import mapUtils

_EMPTY = Environment.EMPTY

ct: Controller = None

class AStar:
    def __init__(self, _ct: Controller):
        global ct
        ct = _ct

    def moveTo(self, target: Position):
        if target is None: return
        if ct.get_move_cooldown() > 0: return
        myLoc = ct.get_position()
        if myLoc.distance_squared(target) == 0: return
        if DEBUG: ct.draw_indicator_line(myLoc, target, 255, 255, 255)

        _imd = isMoveableDirection; _tm = tryMove; _lm = lockMovement
        mW = ct.get_map_width(); mH = ct.get_map_height()

        # Padded grid — 1-cell border eliminates bounds checks
        # grid: 0=passable undiscovered, 1=blocked/border, 2=discovered/visited
        # dirs: first-direction index (0-7) for discovered nodes
        S = mW + 2
        gsz = S * (mH + 2)
        grid = bytearray(gsz)
        dirs = bytearray(gsz)
        bdr = b'\x01' * S
        grid[0:S] = bdr; grid[gsz - S:gsz] = bdr
        for y in range(1, mH + 1):
            o = y * S; grid[o] = 1; grid[o + mW + 1] = 1

        # Mark obstacles from symmetry (walls + all ores)
        sym = Unit.symmetry
        for p in sym.walls: grid[(p.y + 1) * S + p.x + 1] = 1
        for p in sym.oresA: grid[(p.y + 1) * S + p.x + 1] = 1
        for p in sym.oresT: grid[(p.y + 1) * S + p.x + 1] = 1
        if sym.canPredict():
            sf = sym.getSymmetryType()
            for p in sym.walls: sp = sf(ct, p); grid[(sp.y + 1) * S + sp.x + 1] = 1
            for p in sym.oresA: sp = sf(ct, p); grid[(sp.y + 1) * S + sp.x + 1] = 1
            for p in sym.oresT: sp = sf(ct, p); grid[(sp.y + 1) * S + sp.x + 1] = 1

        # Mark impassable visible tiles
        _gte = ct.get_tile_env; _EMP = _EMPTY
        _gbi = ct.get_tile_building_id; _get = ct.get_entity_type; _gtm = ct.get_team
        myTeam = ct.get_team()
        _walk = BARRIER_AND_WALKABLE_ENTITIES if mapUtils._breakBarriers else WALKABLE_ENTITIES
        _gbbot = ct.get_tile_builder_bot_id
        noRoadMoney = ct.get_global_resources()[0] < ct.get_road_cost()[0]
        for p in ct.get_nearby_tiles():
            k = (p.y + 1) * S + p.x + 1
            if _gte(p) != _EMP:
                grid[k] = 1; continue
            bid = _gbbot(p)
            if bid is not None: #and _gtm(bid) == myTeam:
                grid[k] = 1; continue
            bid = _gbi(p)
            if bid is not None:
                bt = _gtm(bid); be = _get(bid)
                if bt != myTeam and be in (EntityType.CORE, EntityType.BARRIER):
                    grid[k] = 1; continue
                if be not in _walk:
                    grid[k] = 1; continue
            elif noRoadMoney:
                grid[k] = 1; continue

        sk = (myLoc.y + 1) * S + myLoc.x + 1
        tk = (target.y + 1) * S + target.x + 1
        grid[sk] = 2  # mark start as discovered

        # Direction deltas: N,S,E,W,NE,SW,SE,NW (matches DIRECTIONS order)
        dN = -S; dS = S; dE = 1; dW = -1
        dNE = dN + 1; dSW = dS - 1; dSE = dS + 1; dNW = dN - 1

        # If target is blocked, pathfind to adjacent tiles instead
        targetBlocked = grid[tk] == 1
        if targetBlocked:
            # Check if already adjacent (<=2 for 1-tile, <=8 for 3x3 cores)
            dSq = myLoc.distance_squared(target)
            isCore = False
            if ct.is_in_vision(target):
                bid = ct.get_tile_building_id(target)
                isCore = bid is not None and _get(bid) == EntityType.CORE
            if dSq <= (8 if isCore else 2): return
            # Passable neighbors of target as goals
            goalSet = set()
            for delta in (dN, dS, dE, dW, dNE, dSW, dSE, dNW):
                gk = tk + delta
                if not grid[gk]: goalSet.add(gk)
            if not goalSet: return
        else:
            goalSet = None

        # A* — Chebyshev heuristic
        hp = heappush; hpop = heappop
        tx1 = target.x + 1; ty1 = target.y + 1
        sx1 = myLoc.x + 1; sy1 = myLoc.y + 1
        adx = sx1 - tx1; ady = sy1 - ty1
        if adx < 0: adx = -adx
        if ady < 0: ady = -ady
        heap = [(adx if adx > ady else ady, 0, sk)]

        found = False
        exp = 0; ck = sk

        while heap:
            f, g, ck = hpop(heap)
            if (goalSet is None and ck == tk) or (goalSet is not None and ck in goalSet):
                found = True; break
            exp += 1
            if exp >= 600: break

            ng = g + 1
            fd = dirs[ck] if ck != sk else 255  # 255 = start sentinel

            # Unrolled 8 directions — discover undiscovered passable neighbors
            k=ck+dN
            if not grid[k]:
                grid[k]=2; dirs[k]=0 if fd==255 else fd
                adx=(k%S)-tx1; ady=(k//S)-ty1
                if adx<0: adx=-adx
                if ady<0: ady=-ady
                hp(heap,(ng+(adx if adx>ady else ady),ng,k))
            k=ck+dS
            if not grid[k]:
                grid[k]=2; dirs[k]=1 if fd==255 else fd
                adx=(k%S)-tx1; ady=(k//S)-ty1
                if adx<0: adx=-adx
                if ady<0: ady=-ady
                hp(heap,(ng+(adx if adx>ady else ady),ng,k))
            k=ck+dE
            if not grid[k]:
                grid[k]=2; dirs[k]=2 if fd==255 else fd
                adx=(k%S)-tx1; ady=(k//S)-ty1
                if adx<0: adx=-adx
                if ady<0: ady=-ady
                hp(heap,(ng+(adx if adx>ady else ady),ng,k))
            k=ck+dW
            if not grid[k]:
                grid[k]=2; dirs[k]=3 if fd==255 else fd
                adx=(k%S)-tx1; ady=(k//S)-ty1
                if adx<0: adx=-adx
                if ady<0: ady=-ady
                hp(heap,(ng+(adx if adx>ady else ady),ng,k))
            k=ck+dNE
            if not grid[k]:
                grid[k]=2; dirs[k]=4 if fd==255 else fd
                adx=(k%S)-tx1; ady=(k//S)-ty1
                if adx<0: adx=-adx
                if ady<0: ady=-ady
                hp(heap,(ng+(adx if adx>ady else ady),ng,k))
            k=ck+dSW
            if not grid[k]:
                grid[k]=2; dirs[k]=5 if fd==255 else fd
                adx=(k%S)-tx1; ady=(k//S)-ty1
                if adx<0: adx=-adx
                if ady<0: ady=-ady
                hp(heap,(ng+(adx if adx>ady else ady),ng,k))
            k=ck+dSE
            if not grid[k]:
                grid[k]=2; dirs[k]=6 if fd==255 else fd
                adx=(k%S)-tx1; ady=(k//S)-ty1
                if adx<0: adx=-adx
                if ady<0: ady=-ady
                hp(heap,(ng+(adx if adx>ady else ady),ng,k))
            k=ck+dNW
            if not grid[k]:
                grid[k]=2; dirs[k]=7 if fd==255 else fd
                adx=(k%S)-tx1; ady=(k//S)-ty1
                if adx<0: adx=-adx
                if ady<0: ady=-ady
                hp(heap,(ng+(adx if adx>ady else ady),ng,k))

        # Execute move — no path means do nothing
        if not found: return
        fd = dirs[ck]
        if fd != 255:
            d = DIRECTIONS[fd]
            if _imd(ct, d): _tm(ct, d); _lm()

from cambc import Controller, EntityType, Environment, Position

from data import SymmetryType

class Symmetry:
    def __init__(self):
        self.oresA: set[Position] = set()
        self.oresT: set[Position] = set()
        self.walls: set[Position] = set()
        self.empties: set[Position] = set()
        self.harvesters: set[Position] = set()
        self.alliedHarvesters: set[Position] = set()
        self.storages = (self.oresA, self.oresT, self.walls, self.empties)
        self.seen: set[Position] = set()  # all tiles we've already classified
        self.horizontal: bool = True
        self.vertical: bool = True
        self.rotational: bool = True

    def __str__(self):
        return f"Symmetry: {1*self.horizontal}{1*self.vertical}{1*self.rotational}"

    def canPredict(self) -> bool:
        return (self.horizontal + self.vertical + self.rotational) == 1
    
    def getSymmetryType(self) -> SymmetryType:
        if self.rotational:
            return SymmetryType.ROTATIONAL
        elif self.horizontal:
            return SymmetryType.HORIZONTAL
        else:
            return SymmetryType.VERTICAL
    
    def getOpenOrePositions(self, ct: Controller) -> set[Position]:
        ores = self.oresA.union(self.oresT)
        if self.canPredict():
            for ore in ores.copy():
                if self.horizontal:
                    ores.add(SymmetryType.HORIZONTAL(ct, ore))
                elif self.vertical:
                    ores.add(SymmetryType.VERTICAL(ct, ore))
                else:
                    ores.add(SymmetryType.ROTATIONAL(ct, ore))
        
        ores = ores.difference(self.harvesters)

        return ores

    def getOpenTitaniumOrePositions(self, ct: Controller) -> set[Position]:
        ores = self.oresT.copy()
        if self.canPredict():
            for ore in ores.copy():
                if self.horizontal:
                    ores.add(SymmetryType.HORIZONTAL(ct, ore))
                elif self.vertical:
                    ores.add(SymmetryType.VERTICAL(ct, ore))
                else:
                    ores.add(SymmetryType.ROTATIONAL(ct, ore))
        
        ores = ores.difference(self.harvesters)

        return ores
    
    def process(self, ct: Controller, pos: Position, storage: set[Position]):
        # Stores a position and updates symmetries accordingly
        storage.add(pos)
        if not self.canPredict():
            hSymm = None if not self.horizontal else SymmetryType.HORIZONTAL(ct, pos)
            vSymm = None if not self.vertical else SymmetryType.VERTICAL(ct, pos)
            rSymm = None if not self.rotational else SymmetryType.ROTATIONAL(ct, pos)
            # Iterate through the storages we have
            for s in self.storages:
                if s is storage: continue

                # If we've already marked the opposite tile in a different storage,
                # that symmetry is no longer possible
                if hSymm in s: self.horizontal = False
                if vSymm in s: self.vertical = False
                if rSymm in s: self.rotational = False

    def update(self, ct: Controller) -> None:
        for tilePos in ct.get_nearby_tiles():
            # Fast path: skip tiles we've already fully classified (env doesn't change)
            isNew = tilePos not in self.seen
            isOre = False

            if isNew:
                self.seen.add(tilePos)
                env: Environment = ct.get_tile_env(tilePos)
                if env == Environment.ORE_AXIONITE:
                    self.process(ct, tilePos, self.oresA)
                    isOre = True
                elif env == Environment.ORE_TITANIUM:
                    self.process(ct, tilePos, self.oresT)
                    isOre = True
                elif env == Environment.WALL:
                    self.process(ct, tilePos, self.walls)
                else:
                    self.process(ct, tilePos, self.empties)
            else:
                # Still need to check harvester changes on ore tiles
                isOre = tilePos in self.oresA or tilePos in self.oresT

            if isOre:
                buildingId = ct.get_tile_building_id(tilePos)
                if buildingId is not None and ct.get_entity_type(buildingId) == EntityType.HARVESTER:
                    self.harvesters.add(tilePos)
                    if ct.get_team(buildingId) == ct.get_team():
                        self.alliedHarvesters.add(tilePos)
                elif tilePos in self.harvesters:
                    self.harvesters.discard(tilePos)
                    self.alliedHarvesters.discard(tilePos)
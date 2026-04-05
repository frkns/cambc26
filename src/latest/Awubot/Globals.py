class Globals:
    # const
    ct: Controller
    my_id: int
    my_team: Team
    my_type: EntityType
    
    # updating
    round: int
    my_pos: Position

    @classmethod
    def init(cls, ct: Controller):
        cls.ct = ct
        cls.my_id = ct.get_id()
        cls.my_team = ct.get_team()
        cls.my_pos = ct.get_position()
        cls.my_type = ct.get_entity_type()

    @classmethod
    def start_tick(cls):
        cls.round = cls.ct.get_current_round()
        cls.my_pos = cls.ct.get_position()


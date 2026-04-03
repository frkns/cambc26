from cambc import Controller, Position

def tryLaunch(ct: Controller, target: Position, end: Position) -> bool:
    if ct.can_launch(target, end):
        ct.launch(target, end)
        return True
    return False
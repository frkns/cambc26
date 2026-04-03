from cambc import Controller, Position

def tryHeal(ct: Controller, target: Position) -> bool:
    if ct.can_heal(target):
        ct.heal(target)
        return True
    return False
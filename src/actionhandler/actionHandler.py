import random

from lib.pyenvlib.grid import Grid
from lib.pyenvlib.location import Location


# @author Daniel McCoy Stephenson
# @since August 31st, 2026
class ActionHandler:
    def __init__(self, environment):
        self.environment = environment

    def getRandomAdjacentLocation(self, grid: Grid, location: Location):
        direction = random.randrange(0, 4)
        if direction == 0:
            return grid.getUp(location)
        elif direction == 1:
            return grid.getRight(location)
        elif direction == 2:
            return grid.getDown(location)
        elif direction == 3:
            return grid.getLeft(location)

    def isLocationImpassible(self, location: Location):
        # search current location
        for eid in location.getEntities():
            entity = location.getEntities()[eid]
            if entity.isSolid():
                return True
        return False

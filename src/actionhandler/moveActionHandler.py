import random

from lib.pyenvlib.entity import Entity
from lib.pyenvlib.grid import Grid
from lib.pyenvlib.location import Location


# @author Daniel McCoy Stephenson
# @since July 26th, 2022
class MoveActionHandler:
    def __init__(self, environment):
        self.environment = environment
        self.debug = False
        self.energyCost = 1

    def chooseRandomDirection(self, grid: Grid, location: Location):
        direction = random.randrange(0, 4)
        if direction == 0:
            return grid.getUp(location)
        elif direction == 1:
            return grid.getRight(location)
        elif direction == 2:
            return grid.getDown(location)
        elif direction == 3:
            return grid.getLeft(location)
        
    def countEdibleEntities(self, entity, location: Location):
        count = 0
        for eid in location.getEntities():
            if entity.canEat(location.getEntities()[eid]):
                count += 1
        return count

    def searchForFood(self, entity, grid: Grid, location: Location):
        # optimal foraging theory (RESEARCH.md): don't abandon a patch that already has food.
        if self.countEdibleEntities(entity, location) > 0:
            return location

        # search nearby locations and prefer the richest patch found within the search budget,
        # rather than settling for the first patch with any food at all.
        bestLocation = -1
        bestFoodCount = 0
        attempts = 0
        maxAttempts = random.randrange(1, 5)
        while attempts < maxAttempts:
            searchLocation = self.chooseRandomDirection(grid, location)
            attempts += 1
            if searchLocation == -1:
                continue
            foodCount = self.countEdibleEntities(entity, searchLocation)
            if foodCount > bestFoodCount:
                bestFoodCount = foodCount
                bestLocation = searchLocation
        return bestLocation
    
    def isLocationImpassible(self, location: Location):
        # search current location
        for eid in location.getEntities():
            entity = location.getEntities()[eid]
            if entity.isSolid():
                return True
        return False
        
    def initiateMoveAction(self, entity: Entity):
        # get location
        locationID = entity.getLocationID()
        grid = self.environment.getGrid()
        location = grid.getLocation(locationID)
        
        # return if we don't need energy
        if not entity.needsEnergy():
            return

        # get new location
        newLocation = self.searchForFood(entity, grid, location)
        if newLocation == -1 or self.isLocationImpassible(newLocation):
            # no food found
            for i in range(0, 10):
                newLocation = self.chooseRandomDirection(grid, location)

                if (newLocation == -1 or self.isLocationImpassible(newLocation)):
                    continue

                if (not self.isLocationImpassible(newLocation)):
                    break
            
        if newLocation == -1:
            # location doesn't exist, we're at a border
            return
        
        # move entity
        location.removeEntity(entity)
        newLocation.addEntity(entity)

        # energy cost for action
        entity.removeEnergy(self.energyCost)

        if self.debug:
            print("[EVENT] ", entity.getName(), "moved to (", location.getX(), ",", location.getY(), ")")
from actionhandler.actionHandler import ActionHandler
from lib.pyenvlib.entity import Entity

from entity.excrement import Excrement


# @author Daniel McCoy Stephenson
# @since July 27th, 2022
class ExcreteActionHandler(ActionHandler):

    def __init__(self, environment):
        super().__init__(environment)
        self.debug = False
        self.energyCost = 1

    def initiateExcreteAction(self, entity: Entity, callbackFunction, tick):
        # get location
        locationID = entity.getLocationID()
        grid = self.environment.getGrid()
        location = grid.getLocation(locationID)
        excretionLocation = self.getRandomAdjacentLocation(grid, location)
        excrement = Excrement(tick)
        if (excretionLocation == -1 or self.isLocationImpassible(excretionLocation)):
            location.addEntity(excrement)
        else:
            excretionLocation.addEntity(excrement)
            callbackFunction(excrement)
        
        # energy cost for action
        entity.removeEnergy(self.energyCost)
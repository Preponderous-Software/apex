import random

from actionhandler.actionHandler import ActionHandler
from lib.pyenvlib.entity import Entity
from lib.pyenvlib.environment import Environment

from simulation.config import Config
from service.soundService import SoundService


# @author Daniel McCoy Stephenson
# @since July 27th, 2022
class ReproduceActionHandler(ActionHandler):

    def __init__(self, environment: Environment, soundService: SoundService, config: Config):
        super().__init__(environment)
        self.childCount = 0
        self.soundService = soundService
        self.config = config

    def initiateReproduceAction(self, entity: Entity, callbackFunction):
        # get location
        locationID = entity.getLocationID()
        grid = self.environment.getGrid()
        location = grid.getLocation(locationID)

        mate = -1
        for eid in location.getEntities():
            targetEntity = location.getEntities()[eid]
            if type(targetEntity) is type(entity) and targetEntity.getID() is not entity.getID() and targetEntity.getSex() is not entity.getSex():
                mate = targetEntity

        if mate == -1:
            # no valid mate
            return

        # energy cost for action
        energyCost = random.randrange(1, entity.getEnergy() // 2)
        entity.removeEnergy(energyCost)
        mate.removeEnergy(energyCost)

        name = entity.getName()
        child = type(entity)(name)
        targetLocation = self.getRandomAdjacentLocation(grid, location)
        if targetLocation == -1 or self.isLocationImpassible(targetLocation):
            targetLocation = location
            return
        self.environment.addEntityToLocation(child, targetLocation)
        callbackFunction(child)
        
        if not self.config.muted:
            self.soundService.playReproduceSoundEffect()

        self.childCount += 1

        print(entity.getName(), "has reproduced with", mate.getName() , "at (", location.getX(), ",", location.getY(), ").")
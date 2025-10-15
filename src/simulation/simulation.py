import random
from actionhandler.eatActionHandler import EatActionHandler
from actionhandler.excreteActionHandler import ExcreteActionHandler
from actionhandler.moveActionHandler import MoveActionHandler
from actionhandler.reproduceActionHandler import ReproduceActionHandler
from entity.berries import Berries
from entity.berryBush import BerryBush
from service.soundService import SoundService

from lib.pyenvlib.entity import Entity
from lib.pyenvlib.environment import Environment

from entity.chicken import Chicken
from entity.cow import Cow
from entity.excrement import Excrement
from entity.fox import Fox
from entity.grass import Grass
from entity.livingEntity import LivingEntity
from entity.pig import Pig
from entity.rabbit import Rabbit
from entity.wolf import Wolf
from entity.water import Water
from entity.rock import Rock


# @author Daniel McCoy Stephenson
# @since July 26th, 2022
class Simulation:
    # constructors ------------------------------------------------------------
    def __init__(self, name, config, gameDisplay, soundService=None):
        self.__config = config
        self.__gameDisplay = gameDisplay
        if soundService is None:
            self.__soundService = SoundService()
        else:
            self.__soundService = soundService
        
        self.environment = Environment(name, self.getConfig().gridSize)

        self.__moveActionHandler = MoveActionHandler(self.environment)
        self.__eatActionHandler = EatActionHandler(self.environment)
        self.__excreteActionHandler = ExcreteActionHandler(self.environment)
        self.__reproduceActionHandler = ReproduceActionHandler(self.environment, self.__soundService, config)
        self.__excrementIds = []
        self.__berryBushIds = []
        
        self.name = name
        self.entities = dict()
        self.livingEntityIds = []
        self.running = True
        self.numTicks = 0
        self.numEntitiesAtStart = 0
        self.numLivingEntitiesAtStart = 0
        
        self.numDeaths = 0

        self.initializeLocationWidthAndHeight()
    
    # public methods ---------------------------------------------------------
    def getConfig(self):
        return self.__config
    
    def setConfig(self, config):
        self.__config = config
    
    def getGameDisplay(self):
        return self.__gameDisplay
    
    def setGameDisplay(self, gameDisplay):
        self.__gameDisplay = gameDisplay
    
    def getExcrementIds(self):
        return self.__excrementIds
    
    def setExcrementIds(self, excrementIds):
        self.__excrementIds = excrementIds
    
    def getBerryBushIds(self):
        return self.__berryBushIds
    
    def setBerryBushIds(self, berryBushIds):
        self.__berryBushIds = berryBushIds
    
    def getSoundService(self):
        return self.__soundService
    
    def setSoundService(self, soundService):
        self.__soundService = soundService
    
    def getMoveActionHandler(self):
        return self.__moveActionHandler
    
    def setMoveActionHandler(self, moveActionHandler):
        self.__moveActionHandler = moveActionHandler
        
    def getEatActionHandler(self):
        return self.__eatActionHandler
    
    def setEatActionHandler(self, eatActionHandler):
        self.__eatActionHandler = eatActionHandler
        
    def getExcreteActionHandler(self):
        return self.__excreteActionHandler
    
    def setExcreteActionHandler(self, excreteActionHandler):
        self.__excreteActionHandler = excreteActionHandler
        
    def getReproduceActionHandler(self):
        return self.__reproduceActionHandler
    
    def setReproduceActionHandler(self, reproduceActionHandler):
        self.__reproduceActionHandler = reproduceActionHandler
    
    def initializeLocationWidthAndHeight(self):
        x, y = self.getGameDisplay().get_size()
        self.locationWidth = x/self.environment.getGrid().getRows()
        self.locationHeight = y/self.environment.getGrid().getColumns()
    
    def addEntityToTrackedEntities(self, entity: Entity):
        self.entities[entity.getID()] = entity
        if isinstance(entity, LivingEntity):
            self.livingEntityIds.append(entity.getID())
        if type(entity) is Excrement:
            self.__excrementIds.append(entity.getID())
        if type(entity) is BerryBush:
            self.__berryBushIds.append(entity.getID())
            
    def generateInitialEntities(self):        
        for i in range(self.getConfig().numWaterEntities):
            self.addEntityToTrackedEntities(Water())
        
        for i in range(self.getConfig().numRockEntities):
            self.addEntityToTrackedEntities(Rock())
            
        for i in range(self.getConfig().numGrassEntities):
            self.addEntityToTrackedEntities(Grass())
            
        for i in range(self.getConfig().numBerriesEntities):
            self.addEntityToTrackedEntities(Berries())
            
        for i in range(self.getConfig().numBerryBushEntities):
            self.addEntityToTrackedEntities(BerryBush())

        for i in range(self.getConfig().numChickensToStart):
            self.addEntityToTrackedEntities(Chicken("Chicken"))

        for i in range(self.getConfig().numPigsToStart):
            self.addEntityToTrackedEntities(Pig("Pig"))

        for i in range(self.getConfig().numWolvesToStart):
            self.addEntityToTrackedEntities(Wolf("Wolf"))
        
        for i in range (self.getConfig().numCowsToStart):
            self.addEntityToTrackedEntities(Cow("Cow"))
        
        for i in range(self.getConfig().numFoxesToStart):
            self.addEntityToTrackedEntities(Fox("Fox"))

        for i in range(self.getConfig().numRabbitsToStart):
            self.addEntityToTrackedEntities(Rabbit("Rabbit"))
    
    def placeInitialEntitiesInEnvironment(self):
        for entityId in self.entities:
            entity = self.entities[entityId]
            self.environment.addEntity(entity)
        self.numEntitiesAtStart = len(self.entities)
        self.numLivingEntitiesAtStart = len(self.livingEntityIds)

    def getNumberOfEntitiesOfType(self, entityType):
        count = 0
        for entityId in self.entities:
            entity = self.entities[entityId]
            if type(entity) is entityType:
                count += 1
        return count
    
    def getNumberOfLivingEntitiesOfType(self, entityType):
        count = 0
        for entityId in self.livingEntityIds:
            entity = self.entities[entityId]
            if type(entity) is entityType:
                count += 1
        return count
    
    def getNumLivingEntities(self):
        return len(self.livingEntityIds)

    def getNumExcrement(self):
        return len(self.__excrementIds)
    
    def cleanup(self):
        print("---")
        print("State of environment:")
        self.environment.printInfo()
        print("Length of simulation:", self.numTicks, "ticks")
        print("---")
    
    def update(self):
        # initiate entity actions
        self.initiateEntityActions()
        
        # decrease energy for living entities
        self.decreaseEnergyForLivingEntities()
        
        # make grass grow
        self.growGrass()

        # make berries grow
        self.growBerries()
    
    def getNumEntities(self):
        return len(self.entities)
    
    def getNumTicks(self):
        return self.numTicks
    
    def getGridSize(self):
        return self.getConfig().gridSize
    
    def getNumDeaths(self):
        return self.numDeaths
    
    def getNumEntitiesAtStart(self):
        return self.numEntitiesAtStart
    
    def getNumLivingEntitiesAtStart(self):
        return self.numLivingEntitiesAtStart

    # private methods --------------------------------------------------------
    def removeEntityFromLocation(self, entity: Entity):
        locationID = entity.getLocationID()
        grid = self.environment.getGrid()
        location = grid.getLocation(locationID)
        if location.isEntityPresent(entity):
            location.removeEntity(entity)
            
    def printDeathInfo(self, entity, oldestLivingEntity):
            toPrint = entity.getName() + " has died."
            if len(self.livingEntityIds) > 0:
                if entity.getID() == oldestLivingEntity.getID():
                    toPrint += " They were the oldest living entity."
            print(toPrint)
            
    def removeEntity(self, entity: Entity):
        if len(self.livingEntityIds) > 0:
            oldestLivingEntityId = self.livingEntityIds[0]
            oldestLivingEntity = self.entities[oldestLivingEntityId]

        del self.entities[entity.getID()]
        self.removeEntityFromLocation(entity)
        if isinstance(entity, LivingEntity):
            self.livingEntityIds.remove(entity.getID())
            self.printDeathInfo(entity, oldestLivingEntity)
            if not self.getConfig().muted:
                self.__soundService.playDeathSoundEffect()
            self.numDeaths += 1
        if type(entity) is Excrement:
            self.__excrementIds.remove(entity.getID())
        if type(entity) is BerryBush:
            self.__berryBushIds.remove(entity.getID())

    def performExcrementCheck(self, excrement):
        if self.shouldExcrementTurnIntoGrass(excrement):
            locationID = excrement.getLocationID()
            grid = self.environment.getGrid()
            location = grid.getLocation(locationID)
            
            self.removeEntity(excrement)
            grass = Grass()
            location.addEntity(grass)
            self.addEntityToTrackedEntities(grass)

    def growGrass(self):
        for excrementId in self.__excrementIds:
            excrement = self.entities[excrementId]
            self.performExcrementCheck(excrement)

    def growBerries(self):
        for berryBushId in self.__berryBushIds:
            berryBush = self.entities[berryBushId]
            if self.shouldBerryBushGainEnergy():
                berryBush.energy += 1
            berryBush.incrementTick()
            self.performBerryBushCheck(berryBush)

    def performBerryBushCheck(self, berryBush):
        if (berryBush.getTick() % self.getConfig().berryBushGrowTime) != 0:
            return
        
        if berryBush.getEnergy() < 10:
            return
        
        locationID = berryBush.getLocationID()
        grid = self.environment.getGrid()
        location = grid.getLocation(locationID)
        
        numBerries = self.countBerriesInLocation(location)
        if numBerries >= 10:
            return
        
        berries = Berries()
        location.addEntity(berries)
        self.addEntityToTrackedEntities(berries)
        berryBush.energy = berryBush.getEnergy() // 2

    def countBerriesInLocation(self, location):
        count = 0
        for entityId in location.getEntities():
            entity = location.getEntity(entityId)
            if type(entity) is Berries:
                count += 1
        return count

    def initiateEntityActions(self):
        for entityId in self.livingEntityIds:
            entity = self.entities[entityId]
            self.__moveActionHandler.initiateMoveAction(entity)
            if entity.needsEnergy():
                self.__eatActionHandler.initiateEatAction(entity, self.removeEntity)
            else:
                if self.shouldEntityExcrete():
                    self.__excreteActionHandler.initiateExcreteAction(entity, self.addEntityToTrackedEntities, self.numTicks)
                if self.shouldEntityReproduce():
                    self.__reproduceActionHandler.initiateReproduceAction(entity, self.addEntityToTrackedEntities)

    def decreaseEnergyForLivingEntities(self):
        for entityId in self.livingEntityIds:
            entity = self.entities[entityId]
            entity.removeEnergy(1)
            if entity.getEnergy() <= 0:
                self.removeEntity(entity)
                
    def shouldExcrementTurnIntoGrass(self, excrement):
        return (self.numTicks - excrement.getTick()) > self.getConfig().grassGrowTime

    def shouldBerryBushGainEnergy(self):
        return random.randrange(0, 100) < 10

    def shouldEntityExcrete(self):
        return random.randrange(0, 100) < (self.getConfig().chanceToExcrete*100)
    
    def shouldEntityReproduce(self):
        return random.randrange(0, 100) < (self.getConfig().chanceToReproduce*100)

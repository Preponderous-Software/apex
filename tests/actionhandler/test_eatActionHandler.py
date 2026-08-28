from unittest.mock import MagicMock

from actionhandler.eatActionHandler import EatActionHandler
from entity.grass import Grass
from entity.rabbit import Rabbit
from entity.water import Water
from lib.pyenvlib.grid import Grid


# helper methods -------------------------------------------------------------
def getHandler(grid):
    environment = MagicMock()
    environment.getGrid.return_value = grid
    return EatActionHandler(environment)

def getGridWithRabbitAt(x, y):
    grid = Grid(3, 3)
    location = grid.getLocationByCoordinates(x, y)
    rabbit = Rabbit("test rabbit")
    location.addEntity(rabbit)
    return grid, location, rabbit

# initiateEatAction tests ----------------------------------------------------
def test_initiateEatAction_transfersFoodEnergyMinusTheActionCost():
    # prepare
    grid, location, rabbit = getGridWithRabbitAt(1, 1)
    handler = getHandler(grid)
    grass = Grass()
    location.addEntity(grass)
    energyBefore = rabbit.getEnergy()
    callback = MagicMock()

    # execute
    handler.initiateEatAction(rabbit, callback)

    # assert
    assert rabbit.getEnergy() == energyBefore + grass.getEnergy() - handler.energyCost

def test_initiateEatAction_passesTheEatenEntityToTheCallback():
    # prepare
    grid, location, rabbit = getGridWithRabbitAt(1, 1)
    handler = getHandler(grid)
    grass = Grass()
    location.addEntity(grass)
    callback = MagicMock()

    # execute
    handler.initiateEatAction(rabbit, callback)

    # assert: removal of the food is the callback's responsibility, not the handler's,
    # so the handler leaves the eaten entity in the location.
    callback.assert_called_once_with(grass)
    assert location.isEntityPresent(grass)

def test_initiateEatAction_doesNothingWhenNoFoodIsPresent():
    # prepare
    grid, location, rabbit = getGridWithRabbitAt(1, 1)
    handler = getHandler(grid)
    energyBefore = rabbit.getEnergy()
    callback = MagicMock()

    # execute
    handler.initiateEatAction(rabbit, callback)

    # assert
    assert rabbit.getEnergy() == energyBefore
    callback.assert_not_called()

def test_initiateEatAction_ignoresEntitiesThatAreNotInTheEntitysDiet():
    # prepare
    grid, location, rabbit = getGridWithRabbitAt(1, 1)
    handler = getHandler(grid)
    location.addEntity(Water())  # not edible by a rabbit
    energyBefore = rabbit.getEnergy()
    callback = MagicMock()

    # execute
    handler.initiateEatAction(rabbit, callback)

    # assert
    assert rabbit.getEnergy() == energyBefore
    callback.assert_not_called()

def test_initiateEatAction_eatsOnlyOneEntityPerAction():
    # prepare
    grid, location, rabbit = getGridWithRabbitAt(1, 1)
    handler = getHandler(grid)
    location.addEntity(Grass())
    location.addEntity(Grass())
    callback = MagicMock()

    # execute
    handler.initiateEatAction(rabbit, callback)

    # assert
    assert callback.call_count == 1

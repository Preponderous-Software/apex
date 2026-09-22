from unittest.mock import MagicMock, patch

from actionhandler.excreteActionHandler import ExcreteActionHandler
from entity.excrement import Excrement
from entity.rabbit import Rabbit
from entity.water import Water
from lib.pyenvlib.grid import Grid


# helper methods -------------------------------------------------------------
def getHandler(grid):
    environment = MagicMock()
    environment.getGrid.return_value = grid
    return ExcreteActionHandler(environment)

def getGridWithRabbitAt(x, y):
    grid = Grid(3, 3)
    location = grid.getLocationByCoordinates(x, y)
    rabbit = Rabbit("test rabbit")
    location.addEntity(rabbit)
    return grid, location, rabbit

def getExcrement(location):
    return [entity for entity in location.getEntities().values() if isinstance(entity, Excrement)]

# initiateExcreteAction tests ------------------------------------------------
@patch("actionhandler.actionHandler.random")
def test_initiateExcreteAction_placesExcrementOnTheChosenNeighbor(mock_random):
    # prepare
    grid, location, rabbit = getGridWithRabbitAt(1, 1)
    handler = getHandler(grid)
    up = grid.getLocationByCoordinates(1, 0)
    mock_random.randrange.return_value = 0  # up
    callback = MagicMock()

    # execute
    handler.initiateExcreteAction(rabbit, callback, 7)

    # assert
    excrement = getExcrement(up)
    assert len(excrement) == 1
    assert excrement[0].getTick() == 7
    assert getExcrement(location) == []
    callback.assert_called_once_with(excrement[0])

@patch("actionhandler.actionHandler.random")
def test_initiateExcreteAction_fallsBackToTheEntitysOwnLocationAtABorder(mock_random):
    # prepare: the entity sits on the top row, so the location above it is off-grid.
    grid, location, rabbit = getGridWithRabbitAt(1, 0)
    handler = getHandler(grid)
    mock_random.randrange.return_value = 0  # up
    callback = MagicMock()

    # execute
    handler.initiateExcreteAction(rabbit, callback, 7)

    # assert: the fallback excrement is registered too, so the simulation tracks it and it
    # can grow into grass like any other (regression test for issue #69).
    excrement = getExcrement(location)
    assert len(excrement) == 1
    callback.assert_called_once_with(excrement[0])

@patch("actionhandler.actionHandler.random")
def test_initiateExcreteAction_fallsBackToTheEntitysOwnLocationWhenTheNeighborIsSolid(mock_random):
    # prepare
    grid, location, rabbit = getGridWithRabbitAt(1, 1)
    handler = getHandler(grid)
    up = grid.getLocationByCoordinates(1, 0)
    up.addEntity(Water())  # solid
    mock_random.randrange.return_value = 0  # up
    callback = MagicMock()

    # execute
    handler.initiateExcreteAction(rabbit, callback, 7)

    # assert: same tracked fallback as at a border (regression test for issue #69).
    excrement = getExcrement(location)
    assert len(excrement) == 1
    assert getExcrement(up) == []
    callback.assert_called_once_with(excrement[0])

@patch("actionhandler.actionHandler.random")
def test_initiateExcreteAction_chargesTheActionCostOnBothBranches(mock_random):
    # prepare
    grid, location, rabbit = getGridWithRabbitAt(1, 1)
    handler = getHandler(grid)
    energyBefore = rabbit.getEnergy()
    mock_random.randrange.return_value = 0  # up, which is a free location
    borderGrid, borderLocation, borderRabbit = getGridWithRabbitAt(1, 0)
    borderHandler = getHandler(borderGrid)
    borderEnergyBefore = borderRabbit.getEnergy()

    # execute
    handler.initiateExcreteAction(rabbit, MagicMock(), 7)
    borderHandler.initiateExcreteAction(borderRabbit, MagicMock(), 7)

    # assert
    assert rabbit.getEnergy() == energyBefore - handler.energyCost
    assert borderRabbit.getEnergy() == borderEnergyBefore - borderHandler.energyCost

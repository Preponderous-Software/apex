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

# getRandomDirection tests ---------------------------------------------------
@patch("actionhandler.excreteActionHandler.random")
def test_getRandomDirection_mapsEachRollToTheMatchingNeighbor(mock_random):
    # prepare
    grid = Grid(3, 3)
    handler = getHandler(grid)
    location = grid.getLocationByCoordinates(1, 1)
    expected = [
        grid.getLocationByCoordinates(1, 0),  # up
        grid.getLocationByCoordinates(2, 1),  # right
        grid.getLocationByCoordinates(1, 2),  # down
        grid.getLocationByCoordinates(0, 1),  # left
    ]

    # execute
    mock_random.randrange.side_effect = [0, 1, 2, 3]
    results = [handler.getRandomDirection(grid, location) for _ in range(4)]

    # assert
    assert results == expected

# isLocationImpassible tests -------------------------------------------------
def test_isLocationImpassible_isTrueOnlyWhenASolidEntityIsPresent():
    # prepare
    grid = Grid(3, 3)
    handler = getHandler(grid)
    empty = grid.getLocationByCoordinates(0, 0)
    passable = grid.getLocationByCoordinates(1, 1)
    passable.addEntity(Rabbit("test rabbit"))  # not solid
    solid = grid.getLocationByCoordinates(2, 2)
    solid.addEntity(Water())  # solid

    # execute / assert
    assert handler.isLocationImpassible(empty) == False
    assert handler.isLocationImpassible(passable) == False
    assert handler.isLocationImpassible(solid) == True

# initiateExcreteAction tests ------------------------------------------------
@patch("actionhandler.excreteActionHandler.random")
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

@patch("actionhandler.excreteActionHandler.random")
def test_initiateExcreteAction_fallsBackToTheEntitysOwnLocationAtABorder(mock_random):
    # prepare: the entity sits on the top row, so the location above it is off-grid.
    grid, location, rabbit = getGridWithRabbitAt(1, 0)
    handler = getHandler(grid)
    mock_random.randrange.return_value = 0  # up
    callback = MagicMock()

    # execute
    handler.initiateExcreteAction(rabbit, callback, 7)

    # assert: the excrement is placed but the callback never fires, so the simulation
    # does not track it and it can never grow into grass (see issue #69).
    assert len(getExcrement(location)) == 1
    callback.assert_not_called()

@patch("actionhandler.excreteActionHandler.random")
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

    # assert: same untracked fallback as at a border (see issue #69).
    assert len(getExcrement(location)) == 1
    assert getExcrement(up) == []
    callback.assert_not_called()

@patch("actionhandler.excreteActionHandler.random")
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

from unittest.mock import MagicMock, patch

from actionhandler.actionHandler import ActionHandler
from entity.grass import Grass
from entity.rabbit import Rabbit
from entity.rock import Rock
from entity.water import Water
from lib.pyenvlib.grid import Grid


# helper methods -------------------------------------------------------------
def getHandler(grid):
    environment = MagicMock()
    environment.getGrid.return_value = grid
    return ActionHandler(environment)

# getRandomAdjacentLocation tests ---------------------------------------------
@patch("actionhandler.actionHandler.random")
def test_getRandomAdjacentLocation_mapsEachRollToTheMatchingNeighbor(mock_random):
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
    mock_random.randrange.side_effect = [0, 1, 2, 3]

    # execute
    results = [handler.getRandomAdjacentLocation(grid, location) for _ in range(4)]

    # assert
    assert results == expected

@patch("actionhandler.actionHandler.random")
def test_getRandomAdjacentLocation_returnsNegativeOneAtABorder(mock_random):
    # prepare: a single-location grid, so every neighbor is off the grid.
    grid = Grid(1, 1)
    handler = getHandler(grid)
    location = grid.getLocationByCoordinates(0, 0)
    mock_random.randrange.side_effect = [0, 1, 2, 3]

    # execute
    results = [handler.getRandomAdjacentLocation(grid, location) for _ in range(4)]

    # assert
    assert results == [-1, -1, -1, -1]

# isLocationImpassible tests -------------------------------------------------
def test_isLocationImpassible_isTrueOnlyWhenASolidEntityIsPresent():
    # prepare
    grid = Grid(3, 3)
    handler = getHandler(grid)
    empty = grid.getLocationByCoordinates(0, 0)
    passable = grid.getLocationByCoordinates(1, 1)
    passable.addEntity(Grass())  # not solid
    passable.addEntity(Rabbit("test rabbit"))  # not solid
    solidRock = grid.getLocationByCoordinates(2, 2)
    solidRock.addEntity(Rock())  # solid
    solidWater = grid.getLocationByCoordinates(0, 2)
    solidWater.addEntity(Water())  # solid

    # execute / assert
    assert handler.isLocationImpassible(empty) == False
    assert handler.isLocationImpassible(passable) == False
    assert handler.isLocationImpassible(solidRock) == True
    assert handler.isLocationImpassible(solidWater) == True

def test_isLocationImpassible_isTrueWhenASolidEntitySharesTheLocationWithPassableOnes():
    # prepare
    grid = Grid(3, 3)
    handler = getHandler(grid)
    location = grid.getLocationByCoordinates(1, 1)
    location.addEntity(Grass())
    location.addEntity(Rock())  # solid

    # execute / assert
    assert handler.isLocationImpassible(location) == True

# constructor tests ----------------------------------------------------------
def test_constructor_retainsTheEnvironment():
    # prepare
    environment = MagicMock()

    # execute
    handler = ActionHandler(environment)

    # assert
    assert handler.environment == environment

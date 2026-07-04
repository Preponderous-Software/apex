from unittest.mock import MagicMock, patch

from actionhandler.moveActionHandler import MoveActionHandler
from entity.grass import Grass
from entity.rabbit import Rabbit
from entity.water import Water
from lib.pyenvlib.grid import Grid


def getHandler():
    return MoveActionHandler(MagicMock())

def test_countEdibleEntities_countsOnlyEdibleEntities():
    # prepare
    handler = getHandler()
    grid = Grid(3, 3)
    location = grid.getLocationByCoordinates(1, 1)
    rabbit = Rabbit("test rabbit")
    location.addEntity(Grass())
    location.addEntity(Grass())
    location.addEntity(Water())  # not edible by a rabbit

    # execute
    result = handler.countEdibleEntities(rabbit, location)

    # assert
    assert result == 2

def test_searchForFood_prefersCurrentLocationWhenFoodIsAlreadyPresent():
    # prepare: this models the marginal value theorem (RESEARCH.md, "Optimal foraging theory") -
    # an entity shouldn't abandon a patch that already has food to go searching for a better one.
    handler = getHandler()
    grid = Grid(3, 3)
    location = grid.getLocationByCoordinates(1, 1)
    rabbit = Rabbit("test rabbit")
    location.addEntity(Grass())

    richerNeighbor = grid.getLocationByCoordinates(1, 0)
    richerNeighbor.addEntity(Grass())
    richerNeighbor.addEntity(Grass())
    richerNeighbor.addEntity(Grass())

    # execute
    result = handler.searchForFood(rabbit, grid, location)

    # assert
    assert result == location

@patch("actionhandler.moveActionHandler.random")
def test_searchForFood_prefersTheRichestNeighboringPatch(mock_random):
    # prepare: no food in the current location; two neighboring patches have food,
    # one richer than the other. Optimal foraging theory predicts a preference for
    # the denser patch (RESEARCH.md, "Optimal foraging theory").
    handler = getHandler()
    grid = Grid(3, 3)
    location = grid.getLocationByCoordinates(1, 1)
    rabbit = Rabbit("test rabbit")

    up = grid.getLocationByCoordinates(1, 0)      # direction 0
    right = grid.getLocationByCoordinates(2, 1)   # direction 1
    down = grid.getLocationByCoordinates(1, 2)    # direction 2
    left = grid.getLocationByCoordinates(0, 1)    # direction 3

    up.addEntity(Grass())
    down.addEntity(Grass())
    down.addEntity(Grass())
    down.addEntity(Grass())

    # first randrange call picks maxAttempts (visit all 4 directions),
    # remaining calls pick the direction for each attempt: up, right, down, left
    mock_random.randrange.side_effect = [4, 0, 1, 2, 3]

    # execute
    result = handler.searchForFood(rabbit, grid, location)

    # assert
    assert result == down

def test_searchForFood_returnsNegativeOneWhenNoFoodIsFound():
    # prepare
    handler = getHandler()
    grid = Grid(3, 3)
    location = grid.getLocationByCoordinates(1, 1)
    rabbit = Rabbit("test rabbit")

    # execute
    result = handler.searchForFood(rabbit, grid, location)

    # assert
    assert result == -1

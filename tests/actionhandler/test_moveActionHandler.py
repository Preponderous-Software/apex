from unittest.mock import MagicMock, patch

from actionhandler.moveActionHandler import MoveActionHandler
from entity.grass import Grass
from entity.rabbit import Rabbit
from entity.rock import Rock
from entity.water import Water
from lib.pyenvlib.grid import Grid


def getHandler():
    return MoveActionHandler(MagicMock())

def getHandlerFor(grid):
    environment = MagicMock()
    environment.getGrid.return_value = grid
    return MoveActionHandler(environment)

def getHungryRabbit():
    rabbit = Rabbit("test rabbit")
    rabbit.removeEnergy(5)  # drops it below its target energy
    return rabbit

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

# isLocationImpassible tests -------------------------------------------------
def test_isLocationImpassible_isTrueOnlyWhenASolidEntityIsPresent():
    # prepare
    handler = getHandler()
    grid = Grid(3, 3)
    empty = grid.getLocationByCoordinates(0, 0)
    passable = grid.getLocationByCoordinates(1, 1)
    passable.addEntity(Grass())  # not solid
    solid = grid.getLocationByCoordinates(2, 2)
    solid.addEntity(Rock())  # solid

    # execute / assert
    assert handler.isLocationImpassible(empty) == False
    assert handler.isLocationImpassible(passable) == False
    assert handler.isLocationImpassible(solid) == True

# initiateMoveAction tests ---------------------------------------------------
def test_initiateMoveAction_doesNothingWhenTheEntityDoesNotNeedEnergy():
    # prepare
    grid = Grid(3, 3)
    handler = getHandlerFor(grid)
    location = grid.getLocationByCoordinates(1, 1)
    rabbit = Rabbit("test rabbit")  # starts at its target energy
    location.addEntity(rabbit)
    energyBefore = rabbit.getEnergy()

    # execute
    handler.initiateMoveAction(rabbit)

    # assert
    assert location.isEntityPresent(rabbit)
    assert rabbit.getEnergy() == energyBefore

@patch("actionhandler.moveActionHandler.random")
def test_initiateMoveAction_movesTowardFoodAndChargesTheActionCost(mock_random):
    # prepare
    grid = Grid(3, 3)
    handler = getHandlerFor(grid)
    location = grid.getLocationByCoordinates(1, 1)
    up = grid.getLocationByCoordinates(1, 0)
    up.addEntity(Grass())
    rabbit = getHungryRabbit()
    location.addEntity(rabbit)
    energyBefore = rabbit.getEnergy()
    # one search attempt, which looks up and finds the grass
    mock_random.randrange.side_effect = [1, 0]

    # execute
    handler.initiateMoveAction(rabbit)

    # assert
    assert up.isEntityPresent(rabbit)
    assert location.isEntityPresent(rabbit) == False
    assert rabbit.getEnergy() == energyBefore - handler.energyCost

@patch("actionhandler.moveActionHandler.random")
def test_initiateMoveAction_wandersInARandomDirectionWhenNoFoodIsFound(mock_random):
    # prepare
    grid = Grid(3, 3)
    handler = getHandlerFor(grid)
    location = grid.getLocationByCoordinates(1, 1)
    right = grid.getLocationByCoordinates(2, 1)
    rabbit = getHungryRabbit()
    location.addEntity(rabbit)
    # one fruitless search attempt looking up, then a wander to the right
    mock_random.randrange.side_effect = [1, 0, 1]

    # execute
    handler.initiateMoveAction(rabbit)

    # assert
    assert right.isEntityPresent(rabbit)

@patch("actionhandler.moveActionHandler.random")
def test_initiateMoveAction_skipsImpassableDestinationsWhileWandering(mock_random):
    # prepare
    grid = Grid(3, 3)
    handler = getHandlerFor(grid)
    location = grid.getLocationByCoordinates(1, 1)
    right = grid.getLocationByCoordinates(2, 1)
    right.addEntity(Water())  # solid
    down = grid.getLocationByCoordinates(1, 2)
    rabbit = getHungryRabbit()
    location.addEntity(rabbit)
    # one fruitless search attempt looking up, then a blocked wander right, then down
    mock_random.randrange.side_effect = [1, 0, 1, 2]

    # execute
    handler.initiateMoveAction(rabbit)

    # assert
    assert down.isEntityPresent(rabbit)
    assert right.isEntityPresent(rabbit) == False

@patch("actionhandler.moveActionHandler.random")
def test_initiateMoveAction_staysPutWhenEveryDirectionIsOffGrid(mock_random):
    # prepare: a single-location grid, so every neighbor is a border.
    grid = Grid(1, 1)
    handler = getHandlerFor(grid)
    location = grid.getLocationByCoordinates(0, 0)
    rabbit = getHungryRabbit()
    location.addEntity(rabbit)
    energyBefore = rabbit.getEnergy()
    mock_random.randrange.return_value = 0

    # execute
    handler.initiateMoveAction(rabbit)

    # assert
    assert location.isEntityPresent(rabbit)
    assert rabbit.getEnergy() == energyBefore

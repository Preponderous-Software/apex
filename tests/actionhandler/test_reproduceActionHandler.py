from unittest.mock import MagicMock, patch

from actionhandler.reproduceActionHandler import ReproduceActionHandler
from entity.chicken import Chicken
from entity.livingEntity import LivingEntity
from entity.rabbit import Rabbit
from entity.water import Water
from lib.pyenvlib.environment import Environment


# helper methods -------------------------------------------------------------
def getHandler(environment, muted=False):
    # a real Environment is used here rather than a mock because the child placement this
    # handler performs goes through Environment.addEntityToLocation and is only observable
    # on a real grid.
    soundService = MagicMock()
    config = MagicMock()
    config.muted = muted
    return ReproduceActionHandler(environment, soundService, config), soundService

def getPair(location, sexes=(LivingEntity.MALE, LivingEntity.FEMALE)):
    parent = Rabbit("test rabbit")
    mate = Rabbit("test rabbit")
    parent.sex = sexes[0]
    mate.sex = sexes[1]
    location.addEntity(parent)
    location.addEntity(mate)
    return parent, mate

def countRabbits(grid):
    count = 0
    for location in grid.getLocations().values():
        count += len([e for e in location.getEntities().values() if isinstance(e, Rabbit)])
    return count

def getChild(location, parent, mate):
    return [e for e in location.getEntities().values() if isinstance(e, Rabbit) and e not in (parent, mate)]

# mate selection tests -------------------------------------------------------
@patch("actionhandler.actionHandler.random")
@patch("actionhandler.reproduceActionHandler.random")
def test_initiateReproduceAction_doesNothingWhenTheEntityIsAlone(mock_random, mock_base_random):
    # prepare
    environment = Environment("test", 3)
    grid = environment.getGrid()
    location = grid.getLocationByCoordinates(1, 1)
    handler, soundService = getHandler(environment)
    parent = Rabbit("test rabbit")
    location.addEntity(parent)
    energyBefore = parent.getEnergy()
    callback = MagicMock()

    # execute
    handler.initiateReproduceAction(parent, callback)

    # assert
    assert parent.getEnergy() == energyBefore
    assert handler.childCount == 0
    callback.assert_not_called()
    mock_random.randrange.assert_not_called()

@patch("actionhandler.actionHandler.random")
@patch("actionhandler.reproduceActionHandler.random")
def test_initiateReproduceAction_doesNothingWhenTheOnlyCandidateIsTheSameSex(mock_random, mock_base_random):
    # prepare
    environment = Environment("test", 3)
    grid = environment.getGrid()
    location = grid.getLocationByCoordinates(1, 1)
    handler, soundService = getHandler(environment)
    parent, mate = getPair(location, sexes=(LivingEntity.MALE, LivingEntity.MALE))
    callback = MagicMock()

    # execute
    handler.initiateReproduceAction(parent, callback)

    # assert
    assert handler.childCount == 0
    assert countRabbits(grid) == 2
    callback.assert_not_called()

@patch("actionhandler.actionHandler.random")
@patch("actionhandler.reproduceActionHandler.random")
def test_initiateReproduceAction_doesNothingWhenTheOnlyCandidateIsADifferentSpecies(mock_random, mock_base_random):
    # prepare
    environment = Environment("test", 3)
    grid = environment.getGrid()
    location = grid.getLocationByCoordinates(1, 1)
    handler, soundService = getHandler(environment)
    parent = Rabbit("test rabbit")
    parent.sex = LivingEntity.MALE
    chicken = Chicken("test chicken")
    chicken.sex = LivingEntity.FEMALE
    location.addEntity(parent)
    location.addEntity(chicken)
    callback = MagicMock()

    # execute
    handler.initiateReproduceAction(parent, callback)

    # assert
    assert handler.childCount == 0
    callback.assert_not_called()

# successful reproduction tests ----------------------------------------------
@patch("actionhandler.actionHandler.random")
@patch("actionhandler.reproduceActionHandler.random")
def test_initiateReproduceAction_placesTheChildOnTheChosenNeighbor(mock_random, mock_base_random):
    # prepare
    environment = Environment("test", 3)
    grid = environment.getGrid()
    location = grid.getLocationByCoordinates(1, 1)
    up = grid.getLocationByCoordinates(1, 0)
    handler, soundService = getHandler(environment)
    parent, mate = getPair(location)
    mock_random.randrange.return_value = 3  # energy cost
    mock_base_random.randrange.return_value = 0  # "up"
    callback = MagicMock()

    # execute
    handler.initiateReproduceAction(parent, callback)

    # assert
    assert len(up.getEntities()) == 1
    child = list(up.getEntities().values())[0]
    assert isinstance(child, Rabbit)
    assert child.getName() == parent.getName()
    callback.assert_called_once_with(child)
    assert handler.childCount == 1

@patch("actionhandler.actionHandler.random")
@patch("actionhandler.reproduceActionHandler.random")
def test_initiateReproduceAction_chargesBothParentsTheSameEnergyCost(mock_random, mock_base_random):
    # prepare
    environment = Environment("test", 3)
    grid = environment.getGrid()
    location = grid.getLocationByCoordinates(1, 1)
    handler, soundService = getHandler(environment)
    parent, mate = getPair(location)
    parentEnergyBefore = parent.getEnergy()
    mateEnergyBefore = mate.getEnergy()
    mock_random.randrange.return_value = 3  # energy cost
    mock_base_random.randrange.return_value = 0  # "up"

    # execute
    handler.initiateReproduceAction(parent, MagicMock())

    # assert
    assert parent.getEnergy() == parentEnergyBefore - 3
    assert mate.getEnergy() == mateEnergyBefore - 3

@patch("actionhandler.actionHandler.random")
@patch("actionhandler.reproduceActionHandler.random")
def test_initiateReproduceAction_playsTheReproduceSoundWhenNotMuted(mock_random, mock_base_random):
    # prepare
    environment = Environment("test", 3)
    location = environment.getGrid().getLocationByCoordinates(1, 1)
    handler, soundService = getHandler(environment, muted=False)
    parent, mate = getPair(location)
    mock_random.randrange.return_value = 3  # energy cost
    mock_base_random.randrange.return_value = 0  # "up"

    # execute
    handler.initiateReproduceAction(parent, MagicMock())

    # assert
    soundService.playReproduceSoundEffect.assert_called_once()

@patch("actionhandler.actionHandler.random")
@patch("actionhandler.reproduceActionHandler.random")
def test_initiateReproduceAction_staysSilentWhenMuted(mock_random, mock_base_random):
    # prepare
    environment = Environment("test", 3)
    location = environment.getGrid().getLocationByCoordinates(1, 1)
    handler, soundService = getHandler(environment, muted=True)
    parent, mate = getPair(location)
    mock_random.randrange.return_value = 3  # energy cost
    mock_base_random.randrange.return_value = 0  # "up"

    # execute
    handler.initiateReproduceAction(parent, MagicMock())

    # assert
    soundService.playReproduceSoundEffect.assert_not_called()
    assert handler.childCount == 1

# invalid target tests -------------------------------------------------------
@patch("actionhandler.actionHandler.random")
@patch("actionhandler.reproduceActionHandler.random")
def test_initiateReproduceAction_placesTheChildWithItsParentsAtABorder(mock_random, mock_base_random):
    # prepare: the parents sit on the top row, so the location above them is off-grid.
    environment = Environment("test", 3)
    grid = environment.getGrid()
    location = grid.getLocationByCoordinates(1, 0)
    handler, soundService = getHandler(environment)
    parent, mate = getPair(location)
    parentEnergyBefore = parent.getEnergy()
    mock_random.randrange.return_value = 3  # energy cost
    mock_base_random.randrange.return_value = 0  # "up"
    callback = MagicMock()

    # execute
    handler.initiateReproduceAction(parent, callback)

    # assert: the child the parents paid for lands on their own tile and is registered like
    # any other (regression test for issue #112).
    assert parent.getEnergy() == parentEnergyBefore - 3
    assert countRabbits(grid) == 3
    child = getChild(location, parent, mate)
    assert len(child) == 1
    callback.assert_called_once_with(child[0])
    assert handler.childCount == 1

@patch("actionhandler.actionHandler.random")
@patch("actionhandler.reproduceActionHandler.random")
def test_initiateReproduceAction_placesTheChildWithItsParentsWhenTheNeighborIsSolid(mock_random, mock_base_random):
    # prepare
    environment = Environment("test", 3)
    grid = environment.getGrid()
    location = grid.getLocationByCoordinates(1, 1)
    up = grid.getLocationByCoordinates(1, 0)
    up.addEntity(Water())  # solid
    handler, soundService = getHandler(environment)
    parent, mate = getPair(location)
    mock_random.randrange.return_value = 3  # energy cost
    mock_base_random.randrange.return_value = 0  # "up"
    callback = MagicMock()

    # execute
    handler.initiateReproduceAction(parent, callback)

    # assert: same fallback to the parents' tile as at a border (regression test for
    # issue #112); the solid neighbor stays untouched.
    assert countRabbits(grid) == 3
    assert len(getChild(location, parent, mate)) == 1
    assert [e for e in up.getEntities().values() if isinstance(e, Rabbit)] == []
    callback.assert_called_once()
    assert handler.childCount == 1

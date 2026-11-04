import datetime
from unittest.mock import patch

from entity.drawableEntity import DrawableEntity
from lib.pyenvlib.environment import Environment
from lib.pyenvlib.grid import Grid


# helper methods -------------------------------------------------------------
def getSolidEntity():
    return DrawableEntity("solid entity", (0, 0, 0), True)

def getPassableEntity():
    return DrawableEntity("passable entity", (0, 0, 0), False)

# construction tests ---------------------------------------------------------
def test_newEnvironment_hasASquareGridOfTheGivenSize():
    grid = Environment("test environment", 3).getGrid()

    assert grid.getColumns() == 3
    assert grid.getRows() == 3
    assert grid.getSize() == 9

def test_newEnvironment_keepsItsNameAndRecordsWhenItWasCreated():
    before = datetime.datetime.now()

    environment = Environment("test environment", 1)

    assert environment.getName() == "test environment"
    assert before <= environment.getCreationDate() <= datetime.datetime.now()

def test_newEnvironments_getDistinctIDs():
    assert Environment("test", 1).getID() != Environment("test", 1).getID()

# setter tests ---------------------------------------------------------------
def test_setters_replaceWhatTheGettersReturn():
    environment = Environment("test environment", 1)
    grid = Grid(2, 2)

    environment.setID("new id")
    environment.setName("new name")
    environment.setGrid(grid)

    assert environment.getID() == "new id"
    assert environment.getName() == "new name"
    assert environment.getGrid() is grid

# addEntity tests ------------------------------------------------------------
def test_addEntity_stampsTheEnvironmentAndGridOnThePlacedEntity():
    environment = Environment("test environment", 2)
    entity = getPassableEntity()

    environment.addEntity(entity)

    assert environment.isEntityPresent(entity)
    assert entity.getEnvironmentID() == environment.getID()
    assert entity.getGridID() == environment.getGrid().getID()

def test_addEntity_stopsRetryingOnceTheGridAcceptsTheEntity(capsys):
    environment = Environment("test environment", 1)

    with patch.object(environment.getGrid(), "addEntity", side_effect=[False, False, True]) as addEntity:
        environment.addEntity(getPassableEntity())

    assert addEntity.call_count == 3
    assert capsys.readouterr().out == ""

def test_addEntity_givesUpAfterAHundredAttempts(capsys):
    environment = Environment("test environment", 1)

    with patch.object(environment.getGrid(), "addEntity", return_value=False) as addEntity:
        environment.addEntity(getPassableEntity())

    assert addEntity.call_count == 100
    assert "Failed to add entity to environment" in capsys.readouterr().out

def test_addEntity_leavesAnEntityUnplacedWhenEveryLocationIsImpassible(capsys):
    environment = Environment("test environment", 1)
    environment.addEntity(getSolidEntity())
    entity = getPassableEntity()

    environment.addEntity(entity)

    assert not environment.isEntityPresent(entity)
    assert environment.getNumEntities() == 1
    assert entity.getLocationID() == -1

# addEntityToLocation tests --------------------------------------------------
def test_addEntityToLocation_placesTheEntityThere():
    environment = Environment("test environment", 2)
    location = environment.getGrid().getLocationByCoordinates(1, 1)
    entity = getPassableEntity()

    environment.addEntityToLocation(entity, location)

    assert location.isEntityPresent(entity)
    assert entity.getEnvironmentID() == environment.getID()
    assert entity.getGridID() == environment.getGrid().getID()

# entity lookup tests --------------------------------------------------------
def test_getEntity_findsAnEntityByID():
    environment = Environment("test environment", 2)
    entity = getPassableEntity()
    environment.addEntity(entity)

    assert environment.getEntity(entity.getID()) is entity

def test_getEntity_returnsNoneForAnUnknownID():
    assert Environment("test environment", 2).getEntity("unknown id") is None

def test_removeEntity_takesItOutOfTheGrid():
    environment = Environment("test environment", 2)
    entity = getPassableEntity()
    environment.addEntity(entity)

    environment.removeEntity(entity)

    assert not environment.isEntityPresent(entity)
    assert environment.getNumEntities() == 0

def test_getNumEntities_countsEveryPlacedEntity():
    environment = Environment("test environment", 2)
    environment.addEntity(getPassableEntity())
    environment.addEntity(getPassableEntity())

    assert environment.getNumEntities() == 2

# printInfo tests ------------------------------------------------------------
def test_printInfo_summarisesTheEnvironment(capsys):
    environment = Environment("test environment", 2)
    environment.addEntity(getPassableEntity())

    environment.printInfo()

    output = capsys.readouterr().out
    assert "test environment" in output
    assert "Num entities:  1" in output
    assert "Num locations:  4" in output
    assert str(environment.getCreationDate()) in output
    assert str(environment.getID()) in output
    assert str(environment.getGrid().getID()) in output

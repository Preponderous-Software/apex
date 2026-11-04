from unittest.mock import patch

import pytest

from entity.drawableEntity import DrawableEntity
from lib.pyenvlib.grid import Grid
from lib.pyenvlib.location import Location


# helper methods -------------------------------------------------------------
def getSolidEntity():
    return DrawableEntity("solid entity", (0, 0, 0), True)

def getPassableEntity():
    return DrawableEntity("passable entity", (0, 0, 0), False)

# generateLocations tests ----------------------------------------------------
def test_newGrid_hasOneLocationForEveryCoordinate():
    grid = Grid(2, 3)

    coordinates = [(location.getX(), location.getY()) for location in grid.getLocations().values()]

    assert sorted(coordinates) == [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]

def test_newGrid_reportsItsDimensionsAndSize():
    grid = Grid(2, 3)

    assert grid.getColumns() == 2
    assert grid.getRows() == 3
    assert grid.getSize() == 6

def test_newGrids_getDistinctIDs():
    assert Grid(1, 1).getID() != Grid(1, 1).getID()

# setter tests ---------------------------------------------------------------
def test_setID_replacesTheID():
    grid = Grid(1, 1)

    grid.setID("new id")

    assert grid.getID() == "new id"

def test_setColumnsAndSetRows_doNotRegenerateTheLocations():
    grid = Grid(2, 2)

    grid.setColumns(5)
    grid.setRows(7)

    assert grid.getColumns() == 5
    assert grid.getRows() == 7
    assert grid.getSize() == 4

def test_setLocations_replacesTheLocations():
    grid = Grid(2, 2)
    location = Location(9, 9)

    grid.setLocations({location.getID(): location})

    assert grid.getSize() == 1
    assert grid.getLocation(location.getID()) is location

# location management tests --------------------------------------------------
def test_addLocation_makesItRetrievableByIDAndCoordinates():
    grid = Grid(1, 1)
    location = Location(4, 5)

    grid.addLocation(location)

    assert grid.getSize() == 2
    assert grid.getLocation(location.getID()) is location
    assert grid.getLocationByCoordinates(4, 5) is location

@pytest.mark.skip(reason="issue 164: getFirstLocation indexes the UUID-keyed locations dict with 0")
def test_getFirstLocation_returnsTheFirstGeneratedLocation():
    grid = Grid(2, 2)

    assert grid.getFirstLocation() is grid.getLocationByCoordinates(0, 0)

@pytest.mark.skip(reason="issue 164: removeLocation calls list.remove on the locations dict")
def test_removeLocation_removesItFromTheGrid():
    grid = Grid(2, 2)
    location = grid.getLocationByCoordinates(1, 1)

    grid.removeLocation(location)

    assert grid.getSize() == 3
    assert grid.getLocationByCoordinates(1, 1) == -1

# getRandomLocation tests ----------------------------------------------------
@patch("lib.pyenvlib.grid.random")
def test_getRandomLocation_picksAcrossEveryLocation(mock_random):
    grid = Grid(2, 3)
    locations = list(grid.getLocations().values())
    mock_random.randrange.return_value = 4

    location = grid.getRandomLocation()

    assert location is locations[4]
    mock_random.randrange.assert_called_once_with(0, 6)

# coordinate lookup tests ----------------------------------------------------
def test_getLocationByCoordinates_returnsTheMatchingLocation():
    grid = Grid(3, 3)

    location = grid.getLocationByCoordinates(2, 1)

    assert (location.getX(), location.getY()) == (2, 1)

@pytest.mark.parametrize("x, y", [(-1, 0), (0, -1), (3, 0), (0, 3)])
def test_getLocationByCoordinates_returnsNegativeOneOffTheGrid(x, y):
    assert Grid(3, 3).getLocationByCoordinates(x, y) == -1

def test_neighbors_followScreenCoordinates():
    # y grows downwards, so "up" is the smaller y
    grid = Grid(3, 3)
    center = grid.getLocationByCoordinates(1, 1)

    assert grid.getUp(center) is grid.getLocationByCoordinates(1, 0)
    assert grid.getRight(center) is grid.getLocationByCoordinates(2, 1)
    assert grid.getDown(center) is grid.getLocationByCoordinates(1, 2)
    assert grid.getLeft(center) is grid.getLocationByCoordinates(0, 1)

def test_neighbors_doNotWrapAroundTheEdges():
    grid = Grid(3, 3)
    topLeft = grid.getLocationByCoordinates(0, 0)
    bottomRight = grid.getLocationByCoordinates(2, 2)

    assert grid.getUp(topLeft) == -1
    assert grid.getLeft(topLeft) == -1
    assert grid.getRight(bottomRight) == -1
    assert grid.getDown(bottomRight) == -1

def test_neighbors_passTheOffGridSentinelThrough():
    grid = Grid(3, 3)

    assert grid.getUp(-1) == -1
    assert grid.getRight(-1) == -1
    assert grid.getDown(-1) == -1
    assert grid.getLeft(-1) == -1

# addEntity tests ------------------------------------------------------------
def test_addEntity_placesTheEntityInTheChosenLocation():
    grid = Grid(1, 1)
    location = grid.getLocationByCoordinates(0, 0)
    entity = getPassableEntity()

    assert grid.addEntity(entity) == True

    assert location.isEntityPresent(entity)
    assert entity.getGridID() == grid.getID()
    assert entity.getLocationID() == location.getID()

def test_addEntity_sharesALocationHoldingOnlyPassableEntities():
    grid = Grid(1, 1)
    grid.addEntity(getPassableEntity())

    assert grid.addEntity(getPassableEntity()) == True

    assert grid.getNumEntities() == 2

def test_addEntity_failsWhenTheChosenLocationIsImpassible():
    grid = Grid(1, 1)
    grid.addEntity(getSolidEntity())
    entity = getPassableEntity()

    assert grid.addEntity(entity) == False

    assert not grid.isEntityPresent(entity)
    assert entity.getLocationID() == -1

def test_addEntity_stampsTheGridIDEvenWhenItFails():
    grid = Grid(1, 1)
    grid.addEntity(getSolidEntity())
    entity = getPassableEntity()

    grid.addEntity(entity)

    assert entity.getGridID() == grid.getID()

# isLocationImpassible tests -------------------------------------------------
def test_isLocationImpassible_isFalseForAnEmptyLocation():
    grid = Grid(1, 1)

    assert grid.isLocationImpassible(grid.getLocationByCoordinates(0, 0)) == False

def test_isLocationImpassible_isFalseWhenEveryEntityIsPassable():
    grid = Grid(1, 1)
    location = grid.getLocationByCoordinates(0, 0)
    location.addEntity(getPassableEntity())

    assert grid.isLocationImpassible(location) == False

def test_isLocationImpassible_isTrueWhenAnyEntityIsSolid():
    grid = Grid(1, 1)
    location = grid.getLocationByCoordinates(0, 0)
    location.addEntity(getPassableEntity())
    location.addEntity(getSolidEntity())

    assert grid.isLocationImpassible(location) == True

# addEntityToLocation tests --------------------------------------------------
def test_addEntityToLocation_placesTheEntityThere():
    grid = Grid(2, 2)
    location = grid.getLocationByCoordinates(1, 0)
    entity = getPassableEntity()

    grid.addEntityToLocation(entity, location)

    assert location.isEntityPresent(entity)
    assert entity.getGridID() == grid.getID()
    assert entity.getLocationID() == location.getID()

def test_addEntityToLocation_ignoresSolidEntitiesAlreadyThere():
    # unlike addEntity, which refuses an impassible location
    grid = Grid(1, 1)
    location = grid.getLocationByCoordinates(0, 0)
    grid.addEntityToLocation(getSolidEntity(), location)
    entity = getPassableEntity()

    grid.addEntityToLocation(entity, location)

    assert location.isEntityPresent(entity)

def test_addEntityToLocation_rejectsALocationFromAnotherGrid():
    grid = Grid(1, 1)

    with pytest.raises(KeyError):
        grid.addEntityToLocation(getPassableEntity(), Location(0, 0))

# entity lookup tests --------------------------------------------------------
def test_getNumEntities_countsAcrossEveryLocation():
    grid = Grid(2, 2)
    grid.addEntityToLocation(getPassableEntity(), grid.getLocationByCoordinates(0, 0))
    grid.addEntityToLocation(getPassableEntity(), grid.getLocationByCoordinates(0, 0))
    grid.addEntityToLocation(getPassableEntity(), grid.getLocationByCoordinates(1, 1))

    assert grid.getNumEntities() == 3

def test_isEntityPresent_findsAnEntityInAnyLocation():
    grid = Grid(2, 2)
    entity = getPassableEntity()
    grid.addEntityToLocation(entity, grid.getLocationByCoordinates(1, 1))

    assert grid.isEntityPresent(entity)

def test_isEntityPresent_isFalsyForAnEntityThatIsNotInTheGrid():
    assert not Grid(2, 2).isEntityPresent(getPassableEntity())

def test_getEntity_findsAnEntityInAnyLocation():
    grid = Grid(2, 2)
    entity = getPassableEntity()
    grid.addEntityToLocation(entity, grid.getLocationByCoordinates(1, 1))

    assert grid.getEntity(entity.getID()) is entity

def test_getEntity_returnsNoneForAnUnknownID():
    assert Grid(2, 2).getEntity("unknown id") is None

def test_removeEntity_removesItFromTheLocationHoldingIt():
    grid = Grid(2, 2)
    kept = getPassableEntity()
    removed = getPassableEntity()
    location = grid.getLocationByCoordinates(1, 1)
    grid.addEntityToLocation(kept, location)
    grid.addEntityToLocation(removed, location)

    grid.removeEntity(removed)

    assert not grid.isEntityPresent(removed)
    assert grid.isEntityPresent(kept)

def test_removeEntity_ignoresAnEntityThatIsNotInTheGrid():
    grid = Grid(2, 2)
    grid.addEntityToLocation(getPassableEntity(), grid.getLocationByCoordinates(0, 0))

    grid.removeEntity(getPassableEntity())

    assert grid.getNumEntities() == 1

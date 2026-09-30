from unittest.mock import MagicMock

from entity.grass import Grass
from entity.rock import Rock
from lib.pyenvlib.location import Location
from ui.textAlertFactory import TextAlertFactory


# helper methods -------------------------------------------------------------
def getTestSimulation(locationWidth, locationHeight):
    simulation = MagicMock()
    simulation.locationWidth = locationWidth
    simulation.locationHeight = locationHeight
    return simulation

def getTestConfig():
    config = MagicMock()
    config.black = (0, 0, 0)
    return config

def createAlert(location, locationWidth=10, locationHeight=10):
    factory = TextAlertFactory()
    return factory.createTextAlertForLocationInfo(location, getTestSimulation(locationWidth, locationHeight), getTestConfig())

# createTextAlertForLocationInfo tests ---------------------------------------
def test_createTextAlertForLocationInfo_positionsTheAlertOffsetFromTheLocationsPixelCoordinates():
    # prepare
    location = Location(3, 5)

    # execute
    alert = createAlert(location, locationWidth=10, locationHeight=20)

    # assert
    assert alert.x == 3 * 10 + 20
    assert alert.y == 5 * 20 + 100

def test_createTextAlertForLocationInfo_usesConfiguredBlackWithFixedSizeAndDuration():
    # prepare
    location = Location(0, 0)

    # execute
    alert = createAlert(location)

    # assert
    assert alert.color == (0, 0, 0)
    assert alert.size == 20
    assert alert.duration == 10

def test_createTextAlertForLocationInfo_describesAnEmptyLocation():
    # prepare
    location = Location(2, 4)

    # execute
    alert = createAlert(location)

    # assert
    assert alert.text == ["Location (2, 4)", "Number of entities: 0"]

def test_createTextAlertForLocationInfo_countsEntitiesByName():
    # prepare
    location = Location(1, 1)
    location.addEntity(Grass())
    location.addEntity(Grass())
    location.addEntity(Rock())

    # execute
    alert = createAlert(location)

    # assert
    assert alert.text[:2] == ["Location (1, 1)", "Number of entities: 3"]
    # per-name lines are emitted in set() iteration order, so compare unordered
    assert sorted(alert.text[2:]) == ["Grass: 2", "Rock: 1"]

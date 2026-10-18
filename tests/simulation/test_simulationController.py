from unittest.mock import MagicMock

import pytest

from entity.chicken import Chicken
from entity.cow import Cow
from entity.fox import Fox
from entity.pig import Pig
from entity.rabbit import Rabbit
from entity.wolf import Wolf
from simulation.simulationController import SimulationController


# helper methods -------------------------------------------------------------
def getTestConfig(tickSpeed=30, maxTickSpeed=60, limitTickSpeed=True):
    config = MagicMock()
    config.tickSpeed = tickSpeed
    config.maxTickSpeed = maxTickSpeed
    config.limitTickSpeed = limitTickSpeed
    config.endSimulationUponAllLivingEntitiesDying = True
    return config

def getTestController(**configValues):
    simulation = MagicMock()
    simulation.running = True
    simulation.numTicks = 0
    return SimulationController(simulation, getTestConfig(**configValues))

# pause tests ----------------------------------------------------------------
def test_startsUnpaused():
    assert getTestController().isPaused() == False

def test_togglePauseFlipsAndReturnsTheNewState():
    controller = getTestController()

    assert controller.togglePause() == True
    assert controller.isPaused() == True
    assert controller.togglePause() == False

# tick speed tests -----------------------------------------------------------
def test_increaseTickSpeedStopsAtTheMaximum():
    controller = getTestController(tickSpeed=59, maxTickSpeed=60)

    assert controller.increaseTickSpeed() == 60
    assert controller.increaseTickSpeed() == 60

def test_decreaseTickSpeedStopsAtOne():
    controller = getTestController(tickSpeed=2)

    assert controller.decreaseTickSpeed() == 1
    assert controller.decreaseTickSpeed() == 1

def test_toggleTickSpeedLimit():
    controller = getTestController(limitTickSpeed=True)

    assert controller.toggleTickSpeedLimit() == False
    assert controller.config.limitTickSpeed == False

def test_tickDelayMatchesTheSimulationScreensFormula():
    controller = getTestController(tickSpeed=30, maxTickSpeed=60)

    assert controller.getTickDelay() == pytest.approx(0.5)

def test_tickDelayIsZeroWithoutTheLimit():
    assert getTestController(limitTickSpeed=False).getTickDelay() == 0

# spawn tests ----------------------------------------------------------------
@pytest.mark.parametrize("key, entityClass, name", [
    ("c", Chicken, "player-created-chicken"),
    ("p", Pig, "player-created-pig"),
    ("k", Cow, "player-created-cow"),
    ("w", Wolf, "player-created-wolf"),
    ("f", Fox, "player-created-fox"),
    ("b", Rabbit, "player-created-rabbit"),
])
def test_spawnPlacesAndTracksTheEntityBoundToTheKey(key, entityClass, name):
    controller = getTestController()

    entity = controller.spawn(key)

    assert type(entity) is entityClass
    assert entity.getName() == name
    controller.simulation.environment.addEntity.assert_called_once_with(entity)
    controller.simulation.addEntityToTrackedEntities.assert_called_once_with(entity)

def test_spawnIgnoresAKeyBoundToNothing():
    controller = getTestController()

    assert controller.spawn("z") is None
    controller.simulation.environment.addEntity.assert_not_called()

# update tests ---------------------------------------------------------------
def test_updateTicksTheSimulation():
    controller = getTestController()

    assert controller.update() == True
    controller.simulation.update.assert_called_once()
    assert controller.simulation.numTicks == 1

def test_updateDoesNothingWhilePaused():
    controller = getTestController()
    controller.togglePause()

    assert controller.update() == False
    controller.simulation.update.assert_not_called()
    assert controller.simulation.numTicks == 0

def test_updateDoesNothingOnceTheSimulationHasEnded():
    # a quit or restart ends the simulation; no tick may run after its cleanup
    controller = getTestController()
    controller.end()

    assert controller.update() == False
    controller.simulation.update.assert_not_called()
    assert controller.simulation.running == False

# end tests ------------------------------------------------------------------
def test_shouldEndWhenNoLivingEntitiesRemain():
    controller = getTestController()
    controller.simulation.getNumLivingEntities.return_value = 0

    assert controller.shouldEnd() == True

def test_shouldNotEndWhileEntitiesLive():
    controller = getTestController()
    controller.simulation.getNumLivingEntities.return_value = 3

    assert controller.shouldEnd() == False

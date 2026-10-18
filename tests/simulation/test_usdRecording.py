"""UsdRecording (apex.py --record) against real stages; skipped when the optional
usd-recorder package (requirements-record.txt) is not installed."""
import sys
from unittest.mock import MagicMock

import pytest

pytest.importorskip("usd_recorder")
from pxr import Usd, UsdGeom  # noqa: E402

import service  # noqa: E402
from entity.chicken import Chicken  # noqa: E402
from entity.grass import Grass  # noqa: E402
from simulation.simulation import Simulation  # noqa: E402
from simulation.usdRecording import UsdRecording  # noqa: E402

# mock pygame (the simulation's SoundService loads sounds)
service.soundService.pygame = MagicMock()


# helper methods -------------------------------------------------------------
def getTestSimulation(gridSize=3):
    config = MagicMock()
    config.gridSize = gridSize
    gameDisplay = MagicMock()
    gameDisplay.get_size.return_value = (300, 300)
    return Simulation("recorded simulation", config, gameDisplay)

def place(simulation, entity, x, y):
    grid = simulation.environment.getGrid()
    simulation.environment.addEntityToLocation(entity, grid.getLocationByCoordinates(x, y))
    simulation.addEntityToTrackedEntities(entity)

def entityPrims(stage):
    return [prim for prim in stage.Traverse() if prim.HasAttribute("recorder:id")]

# tests ------------------------------------------------------------------------
def test_recordsEveryEntityAtItsLocationAndLayer(tmp_path):
    simulation = getTestSimulation()
    grass = Grass()
    chicken = Chicken("Chicken")
    place(simulation, grass, 1, 2)
    place(simulation, chicken, 1, 2)
    path = tmp_path / "run.usda"
    recording = UsdRecording(str(path), gridSize=3)

    recording.recordTick(simulation)
    recording.close()

    stage = Usd.Stage.Open(str(path))
    prims = {prim.GetAttribute("extras:kind").Get(0): prim for prim in entityPrims(stage)}
    assert sorted(prims) == ["Chicken", "Grass"]
    # the grass is at the bottom of the location's stack, the chicken (drawn by the game) on top
    assert tuple(prims["Grass"].GetAttribute("xformOp:translate").Get(0)) == (1, 2, 0)
    assert tuple(prims["Chicken"].GetAttribute("xformOp:translate").Get(0)) == (1, 2, 1)
    assert prims["Chicken"].GetAttribute("extras:energy").Get(0) == chicken.getEnergy()
    assert not prims["Grass"].HasAttribute("extras:energy")
    colour = UsdGeom.Gprim(prims["Chicken"].GetChild("geom")).GetDisplayColorAttr().Get(0)[0]
    assert tuple(round(c * 255) for c in colour) == chicken.getColor()
    world = stage.GetDefaultPrim()
    assert world.GetAttribute("extras:livingEntities").Get(0) == 1
    assert world.GetAttribute("extras:grass").Get(0) == 1
    assert stage.GetRootLayer().customLayerData["apex:gridSize"] == 3
    assert recording.getTicksRecorded() == 1


def test_anEntityRemovedFromTheEnvironmentIsHiddenFromThatTick(tmp_path):
    simulation = getTestSimulation()
    chicken = Chicken("Chicken")
    place(simulation, chicken, 0, 0)
    path = tmp_path / "run.usda"
    recording = UsdRecording(str(path))

    recording.recordTick(simulation)
    simulation.environment.removeEntity(chicken)
    grass = Grass()
    place(simulation, grass, 2, 2)
    simulation.numTicks = 1
    recording.recordTick(simulation)
    recording.close()

    stage = Usd.Stage.Open(str(path))
    prims = {prim.GetAttribute("extras:kind").Get(1): prim for prim in entityPrims(stage)}
    assert prims["Chicken"].GetAttribute("visibility").Get(0) == "inherited"
    assert prims["Chicken"].GetAttribute("visibility").Get(1) == "invisible"
    # the grass did not exist at tick 0
    assert prims["Grass"].GetAttribute("visibility").Get(0) == "invisible"
    assert prims["Grass"].GetAttribute("visibility").Get(1) == "inherited"
    assert (stage.GetStartTimeCode(), stage.GetEndTimeCode()) == (0, 1)


def test_aGeneratedSimulationRecordsOneTimeCodePerTick(tmp_path):
    simulation = getTestSimulation(gridSize=4)
    simulation.getConfig().numWaterEntities = 2
    simulation.getConfig().numRockEntities = 1
    simulation.getConfig().numGrassEntities = 10
    simulation.getConfig().numBerriesEntities = 0
    simulation.getConfig().numBerryBushEntities = 0
    for species in ["Chickens", "Pigs", "Wolves", "Cows", "Foxes", "Rabbits"]:
        setattr(simulation.getConfig(), "num" + species + "ToStart", 1)
    simulation.getConfig().chanceToExcrete = 0.1
    simulation.getConfig().chanceToReproduce = 0.02
    simulation.getConfig().grassGrowTime = 100
    simulation.getConfig().berryBushGrowTime = 300
    simulation.getConfig().muted = True
    simulation.generateInitialEntities()
    simulation.placeInitialEntitiesInEnvironment()
    path = tmp_path / "run.usda"
    recording = UsdRecording(str(path))

    for tick in range(5):
        simulation.update()
        recording.recordTick(simulation)
        simulation.numTicks += 1
    recording.close()

    stage = Usd.Stage.Open(str(path))
    assert (stage.GetStartTimeCode(), stage.GetEndTimeCode()) == (0, 4)
    assert stage.GetTimeCodesPerSecond() == UsdRecording.TIME_CODES_PER_SECOND
    assert len(entityPrims(stage)) >= 19


def test_withoutUsdRecorderRecordingExplainsWhatToInstall(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "usd_recorder", None)

    assert not UsdRecording.isAvailable()
    with pytest.raises(RuntimeError, match="requirements-record.txt"):
        UsdRecording(str(tmp_path / "run.usda"))

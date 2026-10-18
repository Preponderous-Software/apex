import importlib
import inspect
import os
import pkgutil
from unittest.mock import MagicMock, patch

import entity
from entity.chicken import Chicken
from entity.drawableEntity import DrawableEntity
from entity.grass import Grass
from entity.livingEntity import LivingEntity
from entity.water import Water
from entity.wolf import Wolf
from lib.pyenvlib.grid import Grid
from simulation.config import Config
from simulation.simulation import Simulation
from simulation.simulationController import SimulationController
from ui.textRenderer import (EMPTY_GLYPH, GLYPHS, UNKNOWN_GLYPH, EventLog, glyphFor, renderCells,
                             renderRows, statusLines, topEntity)


# helper methods -------------------------------------------------------------
def allEntityTypes():
    types = set()
    for module in pkgutil.iter_modules([os.path.dirname(entity.__file__)]):
        loaded = importlib.import_module("entity." + module.name)
        for _, member in inspect.getmembers(loaded, inspect.isclass):
            if issubclass(member, DrawableEntity) and member not in (DrawableEntity, LivingEntity):
                types.add(member)
    return types

def getTestSimulation(gridSize=8):
    config = Config()
    config.gridSize = gridSize
    config.muted = True
    config.calculateValues()
    display = MagicMock()
    display.get_size.return_value = (gridSize, gridSize)
    simulation = Simulation("test", config, display)
    simulation.generateInitialEntities()
    simulation.placeInitialEntitiesInEnvironment()
    return simulation

def placeAt(grid, x, y, *entities):
    location = grid.getLocationByCoordinates(x, y)
    for each in entities:
        location.addEntity(each)
    return location

# glyph tests ----------------------------------------------------------------
def test_everyEntityTypeHasARealGlyph():
    entityTypes = allEntityTypes()

    assert len(entityTypes) >= 12  # the discovery itself found the entity package
    for entityType in entityTypes:
        assert entityType in GLYPHS, entityType.__name__ + " would be drawn as " + UNKNOWN_GLYPH[0]

def test_glyphsAreDistinct():
    glyphs = [glyph for glyph, _ in GLYPHS.values()]

    assert len(glyphs) == len(set(glyphs))
    assert EMPTY_GLYPH[0] not in glyphs
    assert UNKNOWN_GLYPH[0] not in glyphs

def test_glyphForUsesTheEntitysType():
    assert glyphFor(Water()) == ("~", "BLUE")
    assert glyphFor(object()) == UNKNOWN_GLYPH

# render tests ---------------------------------------------------------------
def test_topEntityIsTheLastOneAdded():
    grid = Grid(3, 3)
    grass = Grass()
    wolf = Wolf("Wolf")
    location = placeAt(grid, 0, 0, grass, wolf)

    assert topEntity(location) is wolf
    assert topEntity(grid.getLocationByCoordinates(1, 1)) is None

def test_renderCellsPlacesEachLocationByItsCoordinates():
    grid = Grid(4, 3)  # 4 columns, 3 rows
    placeAt(grid, 3, 0, Chicken("Chicken"))
    placeAt(grid, 0, 2, Grass(), Wolf("Wolf"))

    cells = renderCells(grid)

    assert len(cells) == 3 and all(len(row) == 4 for row in cells)
    assert cells[0][3] == GLYPHS[Chicken]
    assert cells[2][0] == GLYPHS[Wolf]
    assert cells[1][1] == EMPTY_GLYPH

def test_renderRowsSeparatesCellsWithSpaces():
    grid = Grid(3, 2)
    placeAt(grid, 1, 0, Water())

    assert renderRows(grid) == [". ~ .", ". . ."]

def test_renderDoesNotLookUpLocationsByCoordinates():
    # getLocationByCoordinates scans every location; calling it per cell made a frame O(n^2)
    grid = Grid(5, 5)
    with patch.object(Grid, "getLocationByCoordinates", side_effect=AssertionError("per-cell lookup")):
        renderCells(grid)

def test_aRealSimulationRendersWithoutUnknownGlyphs():
    simulation = getTestSimulation()

    rows = renderRows(simulation.environment.getGrid())

    assert len(rows) == 8
    assert all(UNKNOWN_GLYPH[0] not in row for row in rows)

# status tests ---------------------------------------------------------------
def test_statusLinesReportTicksStateAndPopulation():
    simulation = getTestSimulation()
    simulation.numTicks = 42
    controller = SimulationController(simulation, simulation.getConfig())
    controller.togglePause()

    lines = statusLines(simulation, controller)

    assert "Tick 42" in lines[0]
    assert "PAUSED" in lines[0]
    assert "living " + str(simulation.getNumLivingEntities()) in lines[0]
    assert "C:" + str(simulation.getNumberOfLivingEntitiesOfType(Chicken)) in lines[1]

def test_statusLinesShowAnUnlimitedSpeed():
    simulation = getTestSimulation()
    simulation.getConfig().limitTickSpeed = False
    controller = SimulationController(simulation, simulation.getConfig())

    assert "speed unlimited" in statusLines(simulation, controller)[0]

# event log tests ------------------------------------------------------------
def test_eventLogJoinsPrintFragmentsIntoOneLine():
    log = EventLog()

    print("Pig has reproduced with Pig at (", 23, ",", 14, ").", file=log)

    assert log.getLatest() == "Pig has reproduced with Pig at ( 23 , 14 )."

def test_eventLogHoldsBackAnUnfinishedLine():
    log = EventLog()
    print("Wolf has died.", file=log)
    log.write("Fox has")

    assert log.getLatest() == "Wolf has died."
    log.write(" died.\n")
    assert log.getLatest() == "Fox has died."

def test_eventLogSkipsBlankLines():
    log = EventLog()
    print("Cow has died.", file=log)
    print("", file=log)
    print("\n", file=log)

    assert log.getLatest() == "Cow has died."

def test_eventLogKeepsOnlyTheNewestLines():
    log = EventLog(maxLines=2)
    for i in range(5):
        print("event " + str(i), file=log)

    assert log.getLines() == ["event 3", "event 4"]

def test_eventLogClear():
    log = EventLog()
    print("Warning: no sound", file=log)
    log.write("partial")
    log.clear()

    assert log.getLatest() == ""
    log.write("\n")
    assert log.getLines() == []

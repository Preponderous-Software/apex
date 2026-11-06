from unittest.mock import MagicMock, patch

import pygame

from entity.chicken import Chicken
from entity.cow import Cow
from entity.drawableEntity import DrawableEntity
from entity.fox import Fox
from entity.grass import Grass
from entity.pig import Pig
from entity.rabbit import Rabbit
from entity.water import Water
from entity.wolf import Wolf
from lib.pyenvlib.environment import Environment
from lib.pyenvlib.location import Location
from screen.screenType import ScreenType
from screen.simulationScreen import SimulationScreen
from simulation.config import Config
from ui.textAlert import TextAlert


# helper methods -------------------------------------------------------------
def getTestScreen(fullscreen=False):
    graphik = MagicMock()
    config = MagicMock()
    config.fullscreen = fullscreen
    config.displayWidth = 1280
    config.displayHeight = 720
    screen = SimulationScreen(graphik, config)
    screen.simulation = MagicMock()
    return screen

def getNextScreen(screen):
    return screen._SimulationScreen__nextScreen

def getChangeScreen(screen):
    return screen._SimulationScreen__changeScreen

def handleKey(screen, key):
    screen._SimulationScreen__handleKeyDownEvent(key)

def getRealConfigScreen():
    screen = SimulationScreen(MagicMock(), Config())
    screen.simulation = MagicMock()
    return screen

def getConfig(screen):
    return screen._SimulationScreen__config

def getSelectedEntity(screen):
    return screen._SimulationScreen__selectedEntity

def getLocationWith(*entities):
    location = Location(0, 0)
    for entity in entities:
        location.addEntity(entity)
    return location

def clickOn(screen, location):
    screen.simulation.locationWidth = 10
    screen.simulation.locationHeight = 10
    screen.simulation.environment.getGrid.return_value.getLocationByCoordinates.return_value = location
    with patch("screen.simulationScreen.pygame.display"), patch("builtins.print"):
        screen._SimulationScreen__handleMouseClickEvent((25, 35))

# quit key tests -------------------------------------------------------------
def test_quitKeyRequestsApplicationShutdown():
    # prepare
    screen = getTestScreen()

    # execute
    handleKey(screen, pygame.K_q)

    # assert
    assert getNextScreen(screen) == ScreenType.NONE
    assert getChangeScreen(screen) == True

def test_quitKeyEndsTheSimulationInsteadInTheBrowser(monkeypatch):
    # a browser tab has nothing to quit to: q shows the results instead of leaving a dead canvas
    monkeypatch.setattr("screen.simulationScreen.sys.platform", "emscripten")
    screen = getTestScreen()

    handleKey(screen, pygame.K_q)

    assert getNextScreen(screen) == ScreenType.RESULTS_SCREEN
    assert getChangeScreen(screen) == True
    screen.simulation.cleanup.assert_called_once()

def test_quitKeyCleansUpTheSimulation():
    # prepare
    screen = getTestScreen()

    # execute
    handleKey(screen, pygame.K_q)

    # assert
    screen.simulation.cleanup.assert_called_once()

def test_restartKeyStillRequestsTheSetupScreen():
    # prepare
    screen = getTestScreen()

    # execute
    handleKey(screen, pygame.K_r)

    # assert
    assert getNextScreen(screen) == ScreenType.SETUP_SCREEN
    assert getChangeScreen(screen) == True

# fullscreen toggle tests ----------------------------------------------------
def test_fullscreenKeyEntersFullscreenWithoutError():
    # prepare
    screen = getTestScreen(fullscreen=False)
    newDisplay = MagicMock()

    # execute
    with patch("screen.simulationScreen.pygame.display") as display:
        display.set_mode.return_value = newDisplay
        handleKey(screen, pygame.K_F11)

    # assert
    assert screen._SimulationScreen__config.fullscreen == True
    display.set_mode.assert_called_once_with((1280, 720), pygame.FULLSCREEN)

def test_fullscreenKeyLeavesFullscreenAsAResizableWindow():
    # prepare
    screen = getTestScreen(fullscreen=True)
    newDisplay = MagicMock()

    # execute
    with patch("screen.simulationScreen.pygame.display") as display:
        display.set_mode.return_value = newDisplay
        handleKey(screen, pygame.K_F11)

    # assert
    assert screen._SimulationScreen__config.fullscreen == False
    display.set_mode.assert_called_once_with((1280, 720), pygame.RESIZABLE)

def test_fullscreenKeyRepointsGraphikAndSimulationAtTheNewDisplay():
    # prepare
    screen = getTestScreen(fullscreen=False)
    newDisplay = MagicMock()

    # execute
    with patch("screen.simulationScreen.pygame.display") as display:
        display.set_mode.return_value = newDisplay
        handleKey(screen, pygame.K_F11)

    # assert
    assert screen._SimulationScreen__graphik.gameDisplay == newDisplay
    screen.simulation.setGameDisplay.assert_called_once_with(newDisplay)
    screen.simulation.initializeLocationWidthAndHeight.assert_called_once()

# toggle key tests -----------------------------------------------------------
def test_toggleKeysFlipTheirConfigFlagAndBackAgain():
    keysAndFlags = [
        (pygame.K_l, "limitTickSpeed"),
        (pygame.K_v, "localView"),
        (pygame.K_h, "highlightOldestEntity"),
        (pygame.K_e, "eyesEnabled"),
    ]
    for key, flag in keysAndFlags:
        screen = getRealConfigScreen()
        initial = getattr(getConfig(screen), flag)

        handleKey(screen, key)
        assert getattr(getConfig(screen), flag) == (not initial), flag

        handleKey(screen, key)
        assert getattr(getConfig(screen), flag) == initial, flag

def test_pauseKeysTogglePause():
    for key in (pygame.K_SPACE, pygame.K_ESCAPE):
        screen = getRealConfigScreen()

        handleKey(screen, key)
        assert screen._SimulationScreen__paused == True

        handleKey(screen, key)
        assert screen._SimulationScreen__paused == False

def test_debugKeyTogglesDebugMode():
    screen = getRealConfigScreen()

    handleKey(screen, pygame.K_d)
    assert screen._SimulationScreen__debug == True

    handleKey(screen, pygame.K_d)
    assert screen._SimulationScreen__debug == False

def test_muteKeyTogglesMutedAndMarksTheCaption():
    screen = getRealConfigScreen()
    screen.simulation.name = "Simulation"
    screen.simulation.environment.getGrid.return_value.getColumns.return_value = 20
    screen.simulation.environment.getGrid.return_value.getRows.return_value = 18

    with patch("screen.simulationScreen.pygame.display") as display:
        handleKey(screen, pygame.K_m)
        assert getConfig(screen).muted == True
        display.set_caption.assert_called_with("Apex - Simulation - 20x18 (muted)")

        handleKey(screen, pygame.K_m)
        assert getConfig(screen).muted == False
        display.set_caption.assert_called_with("Apex - Simulation - 20x18")

# bounded adjustment key tests -----------------------------------------------
def test_tickSpeedKeysAdjustTheTickSpeedByOne():
    screen = getRealConfigScreen()
    getConfig(screen).tickSpeed = 30

    handleKey(screen, pygame.K_RIGHTBRACKET)
    assert getConfig(screen).tickSpeed == 31

    handleKey(screen, pygame.K_LEFTBRACKET)
    handleKey(screen, pygame.K_LEFTBRACKET)
    assert getConfig(screen).tickSpeed == 29

def test_tickSpeedStopsAtTheMaximum():
    screen = getRealConfigScreen()
    getConfig(screen).tickSpeed = getConfig(screen).maxTickSpeed

    handleKey(screen, pygame.K_RIGHTBRACKET)

    assert getConfig(screen).tickSpeed == getConfig(screen).maxTickSpeed

def test_tickSpeedStopsAtOne():
    screen = getRealConfigScreen()
    getConfig(screen).tickSpeed = 1

    handleKey(screen, pygame.K_LEFTBRACKET)

    assert getConfig(screen).tickSpeed == 1

def test_viewDistanceKeysAdjustTheLocalViewSizeByOne():
    screen = getRealConfigScreen()
    getConfig(screen).localViewSize = 4

    handleKey(screen, pygame.K_UP)
    assert getConfig(screen).localViewSize == 5

    handleKey(screen, pygame.K_DOWN)
    handleKey(screen, pygame.K_DOWN)
    assert getConfig(screen).localViewSize == 3

def test_viewDistanceStopsAtTheMaximum():
    screen = getRealConfigScreen()
    getConfig(screen).localViewSize = getConfig(screen).maxLocalViewSize

    handleKey(screen, pygame.K_UP)

    assert getConfig(screen).localViewSize == getConfig(screen).maxLocalViewSize

def test_viewDistanceStopsAtOne():
    screen = getRealConfigScreen()
    getConfig(screen).localViewSize = 1

    handleKey(screen, pygame.K_DOWN)

    assert getConfig(screen).localViewSize == 1

# spawn key tests ------------------------------------------------------------
def test_spawnKeysAddAndTrackOneEntityOfTheirSpecies():
    keysAndTypes = [
        (pygame.K_c, Chicken, "player-created-chicken"),
        (pygame.K_p, Pig, "player-created-pig"),
        (pygame.K_k, Cow, "player-created-cow"),
        (pygame.K_w, Wolf, "player-created-wolf"),
        (pygame.K_f, Fox, "player-created-fox"),
        (pygame.K_b, Rabbit, "player-created-rabbit"),
    ]
    for key, entityType, name in keysAndTypes:
        screen = getRealConfigScreen()

        handleKey(screen, key)

        screen.simulation.environment.addEntity.assert_called_once()
        added = screen.simulation.environment.addEntity.call_args[0][0]
        assert type(added) == entityType
        assert added.getName() == name
        screen.simulation.addEntityToTrackedEntities.assert_called_once_with(added)

# mouse click tests ----------------------------------------------------------
def test_clickLooksUpTheLocationUnderTheCursor():
    screen = getRealConfigScreen()

    clickOn(screen, -1)

    grid = screen.simulation.environment.getGrid.return_value
    grid.getLocationByCoordinates.assert_called_once_with(2, 3)

def test_clickOnALivingEntitySelectsIt():
    screen = getRealConfigScreen()
    chicken = Chicken("chicken")

    clickOn(screen, getLocationWith(Grass(), chicken))

    assert getSelectedEntity(screen) == chicken
    assert len(screen._SimulationScreen__textAlerts) == 1

def test_clickOnANonLivingEntityClearsTheSelection():
    screen = getRealConfigScreen()
    screen._SimulationScreen__selectedEntity = Chicken("chicken")

    clickOn(screen, getLocationWith(Grass()))

    assert getSelectedEntity(screen) == None

def test_clickOnAnEmptyLocationKeepsTheSelection():
    screen = getRealConfigScreen()
    chicken = Chicken("chicken")
    screen._SimulationScreen__selectedEntity = chicken

    clickOn(screen, getLocationWith())

    assert getSelectedEntity(screen) == chicken

def test_clickOutsideTheGridDoesNothing():
    screen = getRealConfigScreen()
    chicken = Chicken("chicken")
    screen._SimulationScreen__selectedEntity = chicken

    clickOn(screen, -1)

    assert getSelectedEntity(screen) == chicken
    assert screen._SimulationScreen__textAlerts == []

# location colour tests ------------------------------------------------------
def getColorOfLocation(screen, location):
    return screen._SimulationScreen__getColorOfLocation(location)

def trackOldest(screen, entity):
    screen.simulation.livingEntityIds = [entity.getID()]
    screen.simulation.entities = {entity.getID(): entity}

def test_locationOutsideTheGridIsBlack():
    screen = getRealConfigScreen()

    assert getColorOfLocation(screen, -1) == getConfig(screen).black

def test_emptyLocationIsBrown():
    screen = getRealConfigScreen()

    assert getColorOfLocation(screen, getLocationWith()) == getConfig(screen).brown

def test_locationTakesTheColorOfItsTopEntity():
    screen = getRealConfigScreen()
    grass = Grass()
    chicken = Chicken("chicken")
    trackOldest(screen, Chicken("oldest"))

    assert getColorOfLocation(screen, getLocationWith(grass, chicken)) == chicken.getColor()
    assert getColorOfLocation(screen, getLocationWith(chicken, grass)) == grass.getColor()

def test_oldestEntityIsHighlightedOnlyWhenHighlightingIsOn():
    screen = getRealConfigScreen()
    oldest = Chicken("oldest")
    trackOldest(screen, oldest)
    location = getLocationWith(Grass(), oldest)

    getConfig(screen).highlightOldestEntity = False
    assert getColorOfLocation(screen, location) == oldest.getColor()

    getConfig(screen).highlightOldestEntity = True
    assert getColorOfLocation(screen, location) == getConfig(screen).highlightColor

# text alert tests -----------------------------------------------------------
def drawTextAlerts(screen):
    drawn = []
    screen._SimulationScreen__textAlertDrawTool = MagicMock()
    screen._SimulationScreen__textAlertDrawTool.drawTextAlert.side_effect = lambda alert, graphik: drawn.append(alert)
    screen._SimulationScreen__drawTextAlerts()
    return drawn

def test_textAlertIsDrawnOncePerFrameUntilItsDurationRunsOut():
    screen = getRealConfigScreen()
    alert = TextAlert(0, 0, 12, (0, 0, 0), 2)
    screen._SimulationScreen__textAlerts = [alert]

    assert drawTextAlerts(screen) == [alert]
    assert alert.duration == 1
    assert screen._SimulationScreen__textAlerts == [alert]

    assert drawTextAlerts(screen) == [alert]
    assert screen._SimulationScreen__textAlerts == []

    assert drawTextAlerts(screen) == []

def test_everyTextAlertIsDrawnOnTheFrameAnotherExpires():
    screen = getRealConfigScreen()
    expiring = TextAlert(0, 0, 12, (0, 0, 0), 1)
    following = TextAlert(0, 0, 12, (0, 0, 0), 2)
    screen._SimulationScreen__textAlerts = [expiring, following]

    assert drawTextAlerts(screen) == [expiring, following]
    assert following.duration == 1

# drawing tests --------------------------------------------------------------
def getDrawingScreen(gridSize=3):
    # a real grid behind a recording Graphik: what is checked is what reaches the display
    graphik = MagicMock()
    graphik.gameDisplay.get_size.return_value = (900, 600)
    config = Config()
    config.eyesEnabled = False
    config.localViewSize = 1
    screen = SimulationScreen(graphik, config)
    screen.simulation = MagicMock()
    screen.simulation.environment = Environment("test", gridSize)
    screen.simulation.locationWidth = 10
    screen.simulation.locationHeight = 20
    return screen

def getGrid(screen):
    return screen.simulation.environment.getGrid()

def place(screen, entity, x, y):
    getGrid(screen).addEntityToLocation(entity, getGrid(screen).getLocationByCoordinates(x, y))

def fillWithColoredEntities(screen):
    # one colour per location, so a location drawn in the wrong place cannot go unnoticed
    colors = {}
    for location in getGrid(screen).getLocations().values():
        x, y = location.getX(), location.getY()
        colors[(x, y)] = (x, y, 100)
        place(screen, DrawableEntity("marker", colors[(x, y)], False), x, y)
    return colors

def getRectangles(screen):
    return [call.args for call in screen._SimulationScreen__graphik.drawRectangle.call_args_list]

def getDrawnText(screen):
    return [call.args[0] for call in screen._SimulationScreen__graphik.drawText.call_args_list]

def test_everyLocationIsDrawnOnceAtItsGridPositionWithOverlap():
    screen = getDrawingScreen(gridSize=2)
    brown = getConfig(screen).brown

    screen._SimulationScreen__drawEnvironment()

    # a pixel of overlap on each side, so no seams show between locations
    assert sorted(getRectangles(screen)) == sorted([
        (-1, -1, 12, 22, brown),
        (9, -1, 12, 22, brown),
        (-1, 19, 12, 22, brown),
        (9, 19, 12, 22, brown),
    ])

def test_livingEntityOnTopOfALocationIsDrawnWithEyes():
    screen = getDrawingScreen()
    config = getConfig(screen)
    config.eyesEnabled = True
    chicken = Chicken("chicken")
    trackOldest(screen, chicken)

    screen._SimulationScreen__drawLocation(getLocationWith(Grass(), chicken), 0, 0, 80, 40)

    assert getRectangles(screen) == [
        (0, 0, 80, 40, chicken.getColor()),
        (10, 10, 20, 10, config.white),
        (40, 10, 20, 10, config.white),
        (15, 12.5, 10, 5, config.black),
        (45, 12.5, 10, 5, config.black),
    ]

def test_eyesAreOnlyDrawnForALivingEntityOnTop():
    screen = getDrawingScreen()
    getConfig(screen).eyesEnabled = True
    chicken = Chicken("chicken")
    trackOldest(screen, chicken)

    for location in [-1, getLocationWith(), getLocationWith(chicken, Grass())]:
        screen._SimulationScreen__drawLocation(location, 0, 0, 80, 40)

    assert len(getRectangles(screen)) == 3

def test_eyesCanBeTurnedOff():
    screen = getDrawingScreen()
    chicken = Chicken("chicken")
    trackOldest(screen, chicken)

    screen._SimulationScreen__drawLocation(getLocationWith(chicken), 0, 0, 80, 40)

    assert len(getRectangles(screen)) == 1

def drawLocalViewAround(screen, x, y):
    colors = fillWithColoredEntities(screen)
    selected = Chicken("selected")
    place(screen, selected, x, y)
    trackOldest(screen, selected)
    colors[(x, y)] = selected.getColor()
    screen._SimulationScreen__selectedEntity = selected
    screen._SimulationScreen__drawAreaAroundSelectedEntity()
    return colors

def test_localViewKeepsTheSelectedEntityCentredOnTheDisplay():
    screen = getDrawingScreen(gridSize=3)

    colors = drawLocalViewAround(screen, 1, 1)

    # 900x600 split into three cells a side, and the grid lines up with them exactly
    rectangles = getRectangles(screen)
    for (x, y), color in colors.items():
        assert (x * 300, y * 200, 300, 200, color) in rectangles

def test_localViewFollowsTheSelectedEntityToTheEdgeOfTheGrid():
    screen = getDrawingScreen(gridSize=3)

    colors = drawLocalViewAround(screen, 0, 0)

    # the corner the entity stands in stays at the centre; the grid extends down and right of it
    rectangles = getRectangles(screen)
    for (x, y), color in colors.items():
        assert (300 + x * 300, 200 + y * 200, 300, 200, color) in rectangles

def test_localViewFillsTheSpaceBeyondTheGridWithBlack():
    screen = getDrawingScreen(gridSize=3)

    drawLocalViewAround(screen, 0, 0)

    # the column left of the corner and the one right of the grid, for each of the three rows
    black = getConfig(screen).black
    blackCells = [rectangle[:2] for rectangle in getRectangles(screen) if rectangle[4] == black]
    assert sorted(blackCells) == sorted([(0, 200), (0, 400), (0, 600), (1200, 200), (1200, 400), (1200, 600)])

def test_localViewSizeSetsHowManyLocationsFitOnTheDisplay():
    screen = getDrawingScreen(gridSize=3)
    getConfig(screen).localViewSize = 2

    colors = drawLocalViewAround(screen, 1, 1)

    # five cells a side, centred on the third
    assert (360, 240, 180, 120, colors[(1, 1)]) in getRectangles(screen)
    assert (180, 120, 180, 120, colors[(0, 0)]) in getRectangles(screen)

# stats tests ----------------------------------------------------------------
def getStatsScreen():
    screen = getDrawingScreen()
    screen.simulation.numTicks = 7
    screen.simulation.entities = {"a": None, "b": None}
    screen.simulation.getNumLivingEntities.return_value = 6
    screen.simulation.getNumberOfEntitiesOfType.return_value = 4
    screen.simulation.getNumExcrement.return_value = 3
    species = {Chicken: 11, Pig: 12, Cow: 13, Wolf: 14, Fox: 15, Rabbit: 16}
    screen.simulation.getNumberOfLivingEntitiesOfType.side_effect = species.__getitem__
    return screen

def test_statsListEachCountUnderItsLabel():
    screen = getStatsScreen()
    getConfig(screen).limitTickSpeed = False

    screen._SimulationScreen__displayStats()

    assert getDrawnText(screen) == [
        "Num Ticks:", "7", "",
        "Entities:", "2", "",
        "Living Entities:", "6", "",
        "Grass:", "4", "",
        "Excrement:", "3", "",
        "Chickens:", "11", "",
        "Pigs:", "12", "",
        "Cows:", "13", "",
        "Wolves:", "14", "",
        "Foxes:", "15", "",
        "Rabbits:", "16", "",
    ]
    screen.simulation.getNumberOfEntitiesOfType.assert_called_once_with(Grass)

def test_statsShowTheTickSpeedOnlyWhenItIsLimited():
    screen = getStatsScreen()
    config = getConfig(screen)
    config.limitTickSpeed = True
    config.tickSpeed = 25

    screen._SimulationScreen__displayStats()

    assert getDrawnText(screen)[:3] == ["Tick Speed:", "25", ""]

def test_statsAreDrawnOneLineEachDownTheDisplay():
    screen = getStatsScreen()
    config = getConfig(screen)
    config.limitTickSpeed = False
    config.textSize = 20

    screen._SimulationScreen__displayStats()

    calls = screen._SimulationScreen__graphik.drawText.call_args_list
    assert calls[0].args[1:] == (100, 10, 20, config.black)
    assert calls[1].args[1:] == (100, 30, 20, config.black)
    assert calls[-1].args[1:3] == (100, 10 + 20 * (len(calls) - 1))

# initialization tests -------------------------------------------------------
def getInitializedScreen(muted):
    graphik = MagicMock()
    graphik.gameDisplay.get_size.return_value = (500, 500)
    config = Config()
    config.gridSize = 16
    config.muted = muted
    config.calculateValues()
    screen = SimulationScreen(graphik, config)
    with patch("screen.simulationScreen.pygame.display") as display, patch("builtins.print"):
        screen.initializeSimulation()
    return screen, display

def test_initializeSimulationGeneratesAndPlacesTheEntities():
    screen, _ = getInitializedScreen(muted=False)

    assert screen.simulation.getNumberOfEntitiesOfType(Water) == getConfig(screen).numWaterEntities
    assert screen.simulation.environment.getNumEntities() > 0

def test_initializeSimulationCaptionsTheWindowWithTheGridSize():
    _, display = getInitializedScreen(muted=False)

    display.set_caption.assert_called_once_with("Apex - Simulation - 16x16")

def test_captionSaysSoWhenMuted():
    _, display = getInitializedScreen(muted=True)

    display.set_caption.assert_called_once_with("Apex - Simulation - 16x16 (muted)")

"""The screen loops are coroutines (so the game runs as a pygbag build in a browser): each
has to hand control back once a frame, and must never block on a sleep."""
import asyncio
from unittest.mock import MagicMock

import pygame
import pytest

import screen.simulationScreen as simulationScreenModule
from screen.mainMenuScreen import MainMenuScreen
from screen.resultsScreen import ResultsScreen
from screen.screenType import ScreenType
from screen.setupScreen import SetupScreen
from screen.simulationScreen import SimulationScreen


# helper methods -------------------------------------------------------------
@pytest.fixture
def frames(monkeypatch):
    """Hands each frame the events listed for it, and records every await of asyncio.sleep.
    Once the list runs out every frame gets a QUIT, so a loop that ignored what it was given
    ends (returning ScreenType.NONE) instead of hanging the suite."""
    queued = []
    monkeypatch.setattr(
        pygame.event, "get", lambda: queued.pop(0) if queued else [pygame.event.Event(pygame.QUIT)]
    )
    monkeypatch.setattr(pygame.display, "update", lambda *args: None)
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (-1, -1))
    awaited = []
    realSleep = asyncio.sleep

    async def recordSleep(seconds):
        awaited.append(seconds)
        await realSleep(0)

    monkeypatch.setattr(asyncio, "sleep", recordSleep)
    return queued, awaited


def getGraphik():
    graphik = MagicMock()
    graphik.getGameDisplay.return_value.get_size.return_value = (1280, 720)
    graphik.gameDisplay.get_size.return_value = (1280, 720)
    return graphik


# menu screen tests ----------------------------------------------------------
def test_mainMenuYieldsEveryFrameAndAnyKeyStarts(frames):
    queued, awaited = frames
    queued.extend([[], [], [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a)]])

    result = asyncio.run(MainMenuScreen(getGraphik()).run())

    assert result == ScreenType.SETUP_SCREEN
    assert awaited == [0, 0, 0]


def test_mainMenuOffersQuitOnTheDesktopOnly(monkeypatch):
    graphik = getGraphik()
    MainMenuScreen(graphik).drawMenuButtons()
    labels = [call.args[7] for call in graphik.drawButton.call_args_list]
    assert labels == ["create new sim", "quit"]

    monkeypatch.setattr("screen.mainMenuScreen.sys.platform", "emscripten")
    graphik = getGraphik()
    MainMenuScreen(graphik).drawMenuButtons()
    labels = [call.args[7] for call in graphik.drawButton.call_args_list]
    assert labels == ["create new sim"]


def test_setupScreenYieldsEveryFrame(frames):
    queued, awaited = frames
    queued.extend([[], [pygame.event.Event(pygame.QUIT)]])

    result = asyncio.run(SetupScreen(getGraphik(), MagicMock()).run())

    assert result == ScreenType.NONE
    assert awaited == [0, 0]


def test_resultsScreenReturnsToSetupOnAKey(frames):
    queued, awaited = frames
    queued.extend([[pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a)]])
    screen = ResultsScreen(getGraphik())
    screen.initializeWithSimulation(MagicMock())

    assert asyncio.run(screen.run()) == ScreenType.SETUP_SCREEN
    assert awaited == [0]


def test_resultsScreenReturnsToSetupOnATap(frames):
    # a phone has no key to press; a tap arrives as a mouse press
    queued, awaited = frames
    queued.extend([[], [pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(10, 10), button=1)]])
    screen = ResultsScreen(getGraphik())
    screen.initializeWithSimulation(MagicMock())

    assert asyncio.run(screen.run()) == ScreenType.SETUP_SCREEN
    assert awaited == [0, 0]


# simulation screen tests ----------------------------------------------------
def getSimulationScreen(limitTickSpeed):
    config = MagicMock()
    config.limitTickSpeed = limitTickSpeed
    config.maxTickSpeed = 10
    config.tickSpeed = 8
    config.localView = False
    config.endSimulationUponAllLivingEntitiesDying = True
    config.randomizeGridSizeUponRestart = False
    screen = SimulationScreen(getGraphik(), config)
    screen.simulation = MagicMock()
    screen.simulation.numTicks = 0
    return screen


def test_simulationScreenAwaitsTheTickDelayInsteadOfSleeping(frames):
    queued, awaited = frames
    queued.extend([[], [], []])
    screen = getSimulationScreen(limitTickSpeed=True)
    # alive for two frames, then everything has died in the third (asked twice a frame:
    # once to decide what to draw, once to decide whether the simulation is over)
    screen.simulation.getNumLivingEntities.side_effect = [3, 3, 3, 3, 0, 0]

    result = asyncio.run(screen.run())

    assert result == ScreenType.RESULTS_SCREEN
    # (max - tick) / max each frame, then the one-second pause once all have died
    assert awaited == [0.2, 0.2, 0.2, 1]
    assert screen.simulation.numTicks == 3
    assert not hasattr(simulationScreenModule, "time")


def test_simulationScreenStillYieldsWithTheTickLimitOff(frames):
    queued, awaited = frames
    queued.extend([[], []])
    screen = getSimulationScreen(limitTickSpeed=False)
    screen.simulation.getNumLivingEntities.side_effect = [3, 3, 0, 0]

    asyncio.run(screen.run())

    assert awaited == [0, 0, 1]


def test_aTapOnCreateNewSimLeavesTheMainMenu(frames):
    # a tap is a press and release delivered together, which the held-button check in Graphik
    # never sees; the screen hands the press to the button instead
    from ui.clickableGraphik import ClickableGraphik

    pygame.font.init()
    queued, awaited = frames
    graphik = ClickableGraphik(pygame.Surface((1280, 720)))
    # "create new sim" is centred on the display
    queued.extend([[], [pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(640, 360), button=1)]])

    assert asyncio.run(MainMenuScreen(graphik).run()) == ScreenType.SETUP_SCREEN
    assert graphik.pendingClick is None


def test_aTapOnStartSimulationLeavesTheSetupScreen(frames):
    from ui.clickableGraphik import ClickableGraphik

    pygame.font.init()
    queued, awaited = frames
    graphik = ClickableGraphik(pygame.Surface((1280, 720)))
    # "start simulation" sits at the bottom centre
    queued.extend([[pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(640, 612), button=1)]])
    config = MagicMock()
    config.gridSize = config.grassFactor = config.grassGrowTime = 5

    assert asyncio.run(SetupScreen(graphik, config).run()) == ScreenType.SIMULATION_SCREEN


def test_simulationScreenRecordsEveryTickWhenRecording(frames):
    queued, awaited = frames
    queued.extend([[], [], []])
    screen = getSimulationScreen(limitTickSpeed=False)
    screen.simulation.getNumLivingEntities.side_effect = [3, 3, 3, 3, 0, 0]
    recording = MagicMock()
    screen.setRecording(recording)

    asyncio.run(screen.run())

    # one call per simulated tick, each after that tick's update
    assert recording.recordTick.call_count == 3
    recording.recordTick.assert_called_with(screen.simulation)


def test_simulationScreenRecordsNothingByDefault(frames):
    queued, awaited = frames
    queued.extend([[], []])
    screen = getSimulationScreen(limitTickSpeed=False)
    screen.simulation.getNumLivingEntities.side_effect = [3, 3, 0, 0]

    asyncio.run(screen.run())

    assert screen.getRecording() is None


# simulation screen event tests ----------------------------------------------
def keyDown(key):
    return pygame.event.Event(pygame.KEYDOWN, key=key)


def getRunningSimulationScreen():
    # alive throughout, so only the events a test queues can end the loop
    screen = getSimulationScreen(limitTickSpeed=False)
    screen.simulation.getNumLivingEntities.return_value = 3
    return screen


def getScreenGraphik(screen):
    return screen._SimulationScreen__graphik


def getScreenConfig(screen):
    return screen._SimulationScreen__config


def test_simulationScreenClosingTheWindowEndsTheGame(frames):
    queued, awaited = frames
    queued.extend([[pygame.event.Event(pygame.QUIT)]])
    screen = getRunningSimulationScreen()

    assert asyncio.run(screen.run()) == ScreenType.NONE
    # the frame the window closes on is still played out
    assert screen.simulation.numTicks == 1


def test_simulationScreenHandsKeysToItsControls(frames):
    queued, awaited = frames
    queued.extend([[keyDown(pygame.K_r)]])
    screen = getRunningSimulationScreen()

    assert asyncio.run(screen.run()) == ScreenType.SETUP_SCREEN


def test_simulationScreenRecalculatesLocationSizeWhenTheWindowIsResized(frames):
    queued, awaited = frames
    queued.extend([[pygame.event.Event(pygame.VIDEORESIZE, size=(640, 480), w=640, h=480)]])
    screen = getRunningSimulationScreen()

    asyncio.run(screen.run())

    screen.simulation.initializeLocationWidthAndHeight.assert_called_once_with()


def getClickableScreen(localView):
    screen = getRunningSimulationScreen()
    screen.simulation.locationWidth = 10
    screen.simulation.locationHeight = 10
    getScreenConfig(screen).localView = localView
    grid = screen.simulation.environment.getGrid.return_value
    grid.getLocationByCoordinates.return_value = -1
    return screen, grid


def test_simulationScreenSelectsOnAClickInTheGlobalView(frames):
    queued, awaited = frames
    queued.extend([[pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(25, 35), button=1)]])
    screen, grid = getClickableScreen(localView=False)

    asyncio.run(screen.run())

    grid.getLocationByCoordinates.assert_called_once_with(2, 3)


def test_simulationScreenIgnoresClicksInTheLocalView(frames):
    queued, awaited = frames
    queued.extend([[pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(25, 35), button=1)]])
    screen, grid = getClickableScreen(localView=True)

    asyncio.run(screen.run())

    grid.getLocationByCoordinates.assert_not_called()


def test_pausingStopsTheSimulationAndSaysSo(frames):
    queued, awaited = frames
    queued.extend([[keyDown(pygame.K_SPACE)], []])
    screen = getRunningSimulationScreen()

    asyncio.run(screen.run())

    screen.simulation.update.assert_not_called()
    assert screen.simulation.numTicks == 0
    config = getScreenConfig(screen)
    getScreenGraphik(screen).drawText.assert_any_call("PAUSED", 640, 360, 50, config.black)


def test_unpausingResumesTheSimulation(frames):
    queued, awaited = frames
    queued.extend([[keyDown(pygame.K_SPACE)], [keyDown(pygame.K_SPACE)], []])
    screen = getRunningSimulationScreen()

    asyncio.run(screen.run())

    # both frames after the unpause, the last of them the QUIT the fixture ends the run with
    assert screen.simulation.update.call_count == 3
    assert screen.simulation.numTicks == 3


def test_simulationStillEndsWhenEveryoneDiesWhilePaused(frames):
    queued, awaited = frames
    queued.extend([[keyDown(pygame.K_SPACE)]])
    screen = getSimulationScreen(limitTickSpeed=False)
    screen.simulation.getNumLivingEntities.return_value = 0

    assert asyncio.run(screen.run()) == ScreenType.RESULTS_SCREEN
    assert screen._SimulationScreen__paused == False


def test_simulationScreenDrawsNothingOnceEveryoneHasDied(frames):
    queued, awaited = frames
    queued.extend([[]])
    screen = getSimulationScreen(limitTickSpeed=False)
    screen.simulation.getNumLivingEntities.return_value = 0

    asyncio.run(screen.run())

    screen.simulation.environment.getGrid.assert_not_called()


def test_simulationScreenShowsStatsOnlyInDebugMode(frames):
    queued, awaited = frames
    queued.extend([[], [keyDown(pygame.K_d)], []])
    screen = getRunningSimulationScreen()
    getScreenConfig(screen).textSize = 20

    asyncio.run(screen.run())

    labels = [call.args[0] for call in getScreenGraphik(screen).drawText.call_args_list]
    # of the four frames, all but the one before the key press (the last is the QUIT)
    assert labels.count("Num Ticks:") == 3


def test_endedSimulationRerollsTheGridForTheNextOne(frames):
    queued, awaited = frames
    queued.extend([[]])
    screen = getSimulationScreen(limitTickSpeed=False)
    screen.simulation.getNumLivingEntities.return_value = 0
    config = getScreenConfig(screen)
    config.randomizeGridSizeUponRestart = True

    assert asyncio.run(screen.run()) == ScreenType.RESULTS_SCREEN

    config.randomizeGridSize.assert_called_once_with()
    config.randomizeGrassGrowTime.assert_called_once_with()
    config.calculateValues.assert_called_once_with()
    screen.simulation.cleanup.assert_called_once_with()


def getLocalViewScreen(selected, localView=True):
    screen = getRunningSimulationScreen()
    getScreenConfig(screen).localView = localView
    screen._SimulationScreen__selectedEntity = selected
    screen._SimulationScreen__drawAreaAroundSelectedEntity = MagicMock()
    screen._SimulationScreen__drawEnvironment = MagicMock()
    return screen


def test_localViewDrawsTheAreaAroundTheSelectedEntity(frames):
    queued, awaited = frames
    screen = getLocalViewScreen(MagicMock())

    asyncio.run(screen.run())

    screen._SimulationScreen__drawAreaAroundSelectedEntity.assert_called_once_with()
    screen._SimulationScreen__drawEnvironment.assert_not_called()


def test_localViewFallsBackToTheEnvironmentWithNothingSelected(frames):
    queued, awaited = frames
    screen = getLocalViewScreen(None)

    asyncio.run(screen.run())

    screen._SimulationScreen__drawAreaAroundSelectedEntity.assert_not_called()
    screen._SimulationScreen__drawEnvironment.assert_called_once_with()


def test_selectedEntityThatDiedIsDeselectedAndLocalViewEnds(frames):
    queued, awaited = frames
    screen = getLocalViewScreen(MagicMock())
    screen.simulation.environment.isEntityPresent.return_value = False

    asyncio.run(screen.run())

    assert screen._SimulationScreen__selectedEntity is None
    assert getScreenConfig(screen).localView == False


def test_selectedEntityThatLivesStaysSelected(frames):
    queued, awaited = frames
    selected = MagicMock()
    screen = getLocalViewScreen(selected)
    screen.simulation.environment.isEntityPresent.return_value = True

    asyncio.run(screen.run())

    assert screen._SimulationScreen__selectedEntity == selected
    assert getScreenConfig(screen).localView == True

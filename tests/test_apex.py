import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pygame
import pytest

from apex import Apex


# helper methods -------------------------------------------------------------
def setIcon(path):
    Apex._Apex__setIcon(MagicMock(), path)

# icon tests -----------------------------------------------------------------
def test_setIconUsesTheLoadedImage():
    with patch("pygame.display.set_icon") as setIconMock:
        setIcon(Apex.ICON_PATH)

    setIconMock.assert_called_once()

def test_missingIconDoesNotCrashStartup():
    with patch("pygame.display.set_icon") as setIconMock:
        setIcon("src/media/icon/does-not-exist.PNG")

    setIconMock.assert_not_called()

def test_unreadableIconDoesNotCrashStartup():
    with patch("pygame.image.load", side_effect=pygame.error("unsupported image format")), \
            patch("pygame.display.set_icon") as setIconMock:
        setIcon(Apex.ICON_PATH)

    setIconMock.assert_not_called()

# display tests --------------------------------------------------------------
def test_startupDrawsOnTheDisplayCreatedByGameDisplayFactory():
    # prepare
    newDisplay = MagicMock()

    # execute
    with patch("apex.UsageReportingService"), \
            patch("apex.GameDisplayFactory") as factoryClass, \
            patch("pygame.display.set_icon"):
        factoryClass.return_value.createGameDisplay.return_value = newDisplay
        apex = Apex()

    # assert
    factoryClass.return_value.createGameDisplay.assert_called_once_with(apex.config)
    assert apex.graphik.getGameDisplay() == newDisplay

# --record tests ---------------------------------------------------------------
from apex import parseArguments  # noqa: E402


def getTestApex(recordPath=None):
    with patch("apex.UsageReportingService"), \
            patch("apex.GameDisplayFactory"), \
            patch("pygame.display.set_icon"):
        return Apex(recordPath)

def test_noArgumentsRecordNothing():
    assert parseArguments([]).record is None

def test_recordArgumentTakesAPath():
    assert parseArguments(["--record", "out.usda"]).record == "out.usda"

def test_withoutRecordNoRecordingStarts():
    apex = getTestApex()

    with patch("apex.UsdRecording") as recordingClass:
        apex._Apex__startRecording()

    recordingClass.assert_not_called()
    assert apex.simulationScreen.getRecording() is None

def test_recordRecordsTheFirstSimulationOnly():
    apex = getTestApex("out.usda")

    with patch("apex.UsdRecording") as recordingClass:
        apex._Apex__startRecording()
        recording = recordingClass.return_value
        assert apex.simulationScreen.getRecording() is recording
        recordingClass.assert_called_once_with("out.usda", apex.config.gridSize)

        apex._Apex__finishRecording()
        recording.close.assert_called_once()
        assert apex.simulationScreen.getRecording() is None

        # a restarted or automatically restarted simulation is not recorded over the first
        apex._Apex__startRecording()
        recordingClass.assert_called_once()
        assert apex.simulationScreen.getRecording() is None

# text mode tests ------------------------------------------------------------
from apex import runTextMode  # noqa: E402

def test_textModeIsOffByDefault():
    assert parseArguments([]).text == False

def test_textArgumentSelectsTextMode():
    assert parseArguments(["--text"]).text == True

def test_textModeRunsTheTextRunnerAndReportsUsage():
    with patch("apex.UsageReportingService") as reportingClass, \
            patch("textSimulationRunner.TextSimulationRunner") as runnerClass, \
            patch("pygame.display.set_mode") as setMode:
        runTextMode()

    reporting = reportingClass.return_value
    reporting.reportStartup.assert_called_once()
    runnerClass.assert_called_once_with(onSimulationStarted=reporting.reportSimulationStarted)
    runnerClass.return_value.run.assert_called_once()
    reporting.close.assert_called_once()
    setMode.assert_not_called()  # no pygame window in text mode

def test_textModeClosesUsageReportingWhenTheRunnerFails():
    with patch("apex.UsageReportingService") as reportingClass, \
            patch("textSimulationRunner.TextSimulationRunner") as runnerClass:
        runnerClass.return_value.run.side_effect = KeyboardInterrupt
        try:
            runTextMode()
        except KeyboardInterrupt:
            pass

    reportingClass.return_value.close.assert_called_once()

def test_apexModuleDoesNotImportCurses():
    # the browser build and Windows Python have no curses; only --text may need it
    import apex
    import inspect
    source = inspect.getsource(apex)
    header = source.split("class Apex")[0]
    assert "curses" not in header and "textSimulationRunner" not in header

def test_textModeWithoutCursesExitsWithAHint():
    # a None entry in sys.modules makes importing textSimulationRunner raise ImportError
    with patch.dict("sys.modules", {"textSimulationRunner": None}), \
            patch("apex.UsageReportingService") as reportingClass:
        with pytest.raises(SystemExit) as exitInfo:
            runTextMode()

    assert "--text needs the curses module" in str(exitInfo.value)
    assert "windows-curses" in str(exitInfo.value)
    reportingClass.assert_not_called()  # nothing is reported when text mode cannot start

# screen routing tests ---------------------------------------------------------
from screen.screenType import ScreenType  # noqa: E402


class ApplicationQuit(Exception):
    pass

# Replaces every screen with a mock whose run() returns the next of the given results, whichever
# screen is current, then runs the application until it quits. Returns the screens run, in order,
# and the mocks standing in for pygame.quit and quit.
def runApexThrough(apex, results):
    results = iter(results)
    screensRun = []
    for name in ("mainMenuScreen", "setupScreen", "simulationScreen", "resultsScreen"):
        screen = MagicMock(name=name)
        screen.run = AsyncMock(side_effect=lambda screen=screen: screensRun.append(screen) or next(results))
        setattr(apex, name, screen)
    apex.currentScreen = apex.mainMenuScreen
    with patch("pygame.quit") as pygameQuit, \
            patch("builtins.quit", side_effect=ApplicationQuit, create=True) as quitMock:
        with pytest.raises(ApplicationQuit):
            asyncio.run(apex.run())
    return screensRun, pygameQuit, quitMock

def test_runStartsOnTheMainMenu():
    apex = getTestApex()

    screensRun, _, _ = runApexThrough(apex, [ScreenType.NONE])

    assert screensRun == [apex.mainMenuScreen]

def test_runSwitchesToTheScreenEachScreenReturns():
    apex = getTestApex()

    screensRun, _, _ = runApexThrough(apex, [
        ScreenType.SETUP_SCREEN,
        ScreenType.SIMULATION_SCREEN,
        ScreenType.RESULTS_SCREEN,
        ScreenType.MAIN_MENU_SCREEN,
        ScreenType.NONE,
    ])

    assert screensRun == [apex.mainMenuScreen, apex.setupScreen, apex.simulationScreen,
                          apex.resultsScreen, apex.mainMenuScreen]

def test_startingASimulationRecalculatesTheConfigInitializesItAndReportsIt():
    apex = getTestApex()
    apex.config = MagicMock()
    reporting = apex.usageReporting

    runApexThrough(apex, [ScreenType.SIMULATION_SCREEN, ScreenType.NONE])

    apex.config.calculateValues.assert_called_once()
    apex.simulationScreen.initializeSimulation.assert_called_once()
    reporting.reportSimulationStarted.assert_called_once()

def test_resultsScreenIsGivenTheSimulationThatJustRan():
    apex = getTestApex()

    runApexThrough(apex, [ScreenType.SIMULATION_SCREEN, ScreenType.RESULTS_SCREEN, ScreenType.NONE])

    apex.resultsScreen.initializeWithSimulation.assert_called_once_with(apex.simulationScreen.simulation)

def test_leavingTheSimulationScreenFinishesTheRecording():
    apex = getTestApex("out.usda")

    with patch("apex.UsdRecording") as recordingClass:
        runApexThrough(apex, [ScreenType.SIMULATION_SCREEN, ScreenType.RESULTS_SCREEN, ScreenType.NONE])

    recordingClass.assert_called_once_with("out.usda", apex.config.gridSize)
    recordingClass.return_value.close.assert_called_once()
    assert apex.recording is None
    assert apex.recordingFinished == True

def test_leavingAnotherScreenDoesNotFinishTheRecording():
    apex = getTestApex("out.usda")
    recording = MagicMock()
    apex.recording = recording

    runApexThrough(apex, [ScreenType.SETUP_SCREEN, ScreenType.NONE])

    recording.close.assert_not_called()
    assert apex.recording is recording

def test_quittingClosesUsageReportingAndPygame():
    apex = getTestApex()
    reporting = apex.usageReporting

    _, pygameQuit, quitMock = runApexThrough(apex, [ScreenType.NONE])

    reporting.close.assert_called_once()
    pygameQuit.assert_called_once()
    quitMock.assert_called_once()

def test_anUnrecognizedScreenQuitsTheApplication(capsys):
    apex = getTestApex()
    reporting = apex.usageReporting

    _, pygameQuit, _ = runApexThrough(apex, ["no_such_screen"])

    assert "unrecognized screen: no_such_screen" in capsys.readouterr().out
    reporting.close.assert_called_once()
    pygameQuit.assert_called_once()

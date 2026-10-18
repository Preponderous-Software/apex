from unittest.mock import MagicMock, patch

import pygame

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

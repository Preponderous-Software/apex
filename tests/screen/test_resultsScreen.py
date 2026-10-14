import asyncio
from unittest.mock import MagicMock

import pygame
import pytest

import screen.resultsScreen as resultsScreenModule
from screen.resultsScreen import ResultsScreen
from screen.screenType import ScreenType


# helper methods -------------------------------------------------------------
def getTestScreen():
    graphik = MagicMock()
    graphik.getGameDisplay.return_value.get_size.return_value = (1280, 720)
    return ResultsScreen(graphik)

def getSimulation(gridSize, numEntities, numTicks):
    simulation = MagicMock()
    simulation.getGridSize.return_value = gridSize
    simulation.getNumEntities.return_value = numEntities
    simulation.getNumTicks.return_value = numTicks
    return simulation


# navigation tests -----------------------------------------------------------
def test_initialization():
    screen = getTestScreen()
    assert screen.nextScreen == ScreenType.SETUP_SCREEN
    assert screen.changeScreen == False
    assert screen.simulation is None

def test_initializeWithSimulation():
    screen = getTestScreen()
    simulation = getSimulation(20, 5, 100)
    screen.initializeWithSimulation(simulation)
    assert screen.simulation is simulation

def test_switchToSetupScreen():
    screen = getTestScreen()
    screen.nextScreen = ScreenType.NONE
    screen.switchToSetupScreen()
    assert screen.nextScreen == ScreenType.SETUP_SCREEN
    assert screen.changeScreen == True

def test_handleKeyDownEventSwitchesToSetupScreenForAnyKey():
    screen = getTestScreen()
    screen.nextScreen = ScreenType.NONE
    screen.handleKeyDownEvent(12345)
    assert screen.nextScreen == ScreenType.SETUP_SCREEN
    assert screen.changeScreen == True

def test_quitApplicationQuitsPygameAndExits(monkeypatch):
    pygameQuit = MagicMock()
    monkeypatch.setattr(resultsScreenModule.pygame, "quit", pygameQuit)
    screen = getTestScreen()
    with pytest.raises(SystemExit):
        screen.quitApplication()
    pygameQuit.assert_called_once_with()


# drawing tests --------------------------------------------------------------
def test_drawTextShowsTheSimulationsResults():
    screen = getTestScreen()
    screen.initializeWithSimulation(getSimulation(24, 7, 350))
    screen.drawText()
    white = (255, 255, 255)
    assert [call.args for call in screen.graphik.drawText.call_args_list] == [
        ("Results", 640, 72, 64, white),
        ("simulation size: 24", 640, 240, 32, white),
        ("entities at end: 7", 640, 290, 32, white),
        ("ticks: 350", 640, 340, 32, white),
        ("press any key or tap to return to setup", 640, 648, 32, white),
    ]

def test_drawTextRequiresASimulation():
    # drawText reads from the simulation handed over by initializeWithSimulation
    screen = getTestScreen()
    with pytest.raises(AttributeError):
        screen.drawText()

def test_drawVersionDrawsNothingWithoutAVersionFile(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    screen = getTestScreen()
    screen.drawVersion()
    screen.graphik.drawText.assert_not_called()

def test_drawVersionDrawsTheVersionFileAtTheBottomCentre(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "version.txt").write_text("v1.2.3")
    screen = getTestScreen()
    screen.drawVersion()
    screen.graphik.drawText.assert_called_once_with("v1.2.3", 640, 710, 16, (255, 255, 255))


# run tests ------------------------------------------------------------------
def test_runReturnsNoneOnQuitAndResetsChangeScreen(monkeypatch):
    monkeypatch.setattr(pygame.event, "get", lambda: [pygame.event.Event(pygame.QUIT)])
    monkeypatch.setattr(pygame.display, "update", lambda *args: None)
    screen = getTestScreen()
    screen.initializeWithSimulation(getSimulation(20, 5, 100))
    assert asyncio.run(screen.run()) == ScreenType.NONE
    # reset so the screen can be shown again the next time it is switched to
    assert screen.changeScreen == False

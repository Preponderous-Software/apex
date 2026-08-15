from unittest.mock import MagicMock, patch

import pygame

from screen.screenType import ScreenType
from screen.simulationScreen import SimulationScreen


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

# quit key tests -------------------------------------------------------------
def test_quitKeyRequestsApplicationShutdown():
    # prepare
    screen = getTestScreen()

    # execute
    handleKey(screen, pygame.K_q)

    # assert
    assert getNextScreen(screen) == ScreenType.NONE
    assert getChangeScreen(screen) == True

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

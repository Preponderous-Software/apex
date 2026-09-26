from unittest.mock import MagicMock, patch

import pygame

from ui.gameDisplayFactory import GameDisplayFactory


# helper methods -------------------------------------------------------------
def getTestConfig(fullscreen):
    config = MagicMock()
    config.fullscreen = fullscreen
    config.displayWidth = 1280
    config.displayHeight = 720
    return config

# createGameDisplay tests ----------------------------------------------------
def test_createGameDisplayUsesFullscreenWhenConfigured():
    # prepare
    factory = GameDisplayFactory()
    newDisplay = MagicMock()

    # execute
    with patch("ui.gameDisplayFactory.pygame.display") as display:
        display.set_mode.return_value = newDisplay
        result = factory.createGameDisplay(getTestConfig(fullscreen=True))

    # assert
    display.set_mode.assert_called_once_with((1280, 720), pygame.FULLSCREEN)
    assert result == newDisplay

def test_createGameDisplayUsesAResizableWindowOtherwise():
    # prepare
    factory = GameDisplayFactory()
    newDisplay = MagicMock()

    # execute
    with patch("ui.gameDisplayFactory.pygame.display") as display:
        display.set_mode.return_value = newDisplay
        result = factory.createGameDisplay(getTestConfig(fullscreen=False))

    # assert
    display.set_mode.assert_called_once_with((1280, 720), pygame.RESIZABLE)
    assert result == newDisplay

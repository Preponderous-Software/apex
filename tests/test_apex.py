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

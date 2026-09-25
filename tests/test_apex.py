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

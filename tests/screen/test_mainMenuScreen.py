import asyncio
from unittest.mock import MagicMock

import pygame
import pytest

import screen.mainMenuScreen as mainMenuScreenModule
from screen.mainMenuScreen import MainMenuScreen
from screen.screenType import ScreenType


# helper methods -------------------------------------------------------------
def getTestScreen():
    graphik = MagicMock()
    graphik.getGameDisplay.return_value.get_size.return_value = (1280, 720)
    return MainMenuScreen(graphik)


# navigation tests -----------------------------------------------------------
def test_initialization():
    screen = getTestScreen()
    assert screen.nextScreen == ScreenType.SETUP_SCREEN
    assert screen.changeScreen == False

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
    monkeypatch.setattr(mainMenuScreenModule.pygame, "quit", pygameQuit)
    screen = getTestScreen()
    with pytest.raises(SystemExit):
        screen.quitApplication()
    pygameQuit.assert_called_once_with()


# drawing tests --------------------------------------------------------------
def test_drawText():
    screen = getTestScreen()
    screen.drawText()
    assert [call.args for call in screen.graphik.drawText.call_args_list] == [
        ("Apex", 640, 72, 64, (255, 255, 255)),
        ("press any key to start!", 640, 240, 32, (255, 255, 255)),
    ]

def test_drawMenuButtonsWiresEachButtonToItsHandler(monkeypatch):
    monkeypatch.setattr(mainMenuScreenModule.sys, "platform", "linux")
    screen = getTestScreen()
    screen.drawMenuButtons()
    # drawButton(xpos, ypos, width, height, backgroundColor, textColor, textSize, text, function)
    assert [call.args for call in screen.graphik.drawButton.call_args_list] == [
        (512, 324, 256, 72, (255, 255, 255), (0, 0, 0), 30, "create new sim", screen.switchToSetupScreen),
        # stacked below the first button with a 10 pixel margin
        (512, 406, 256, 72, (255, 255, 255), (0, 0, 0), 30, "quit", screen.quitApplication),
    ]

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
    assert asyncio.run(screen.run()) == ScreenType.NONE
    # reset so the screen can be shown again the next time it is switched to
    assert screen.changeScreen == False

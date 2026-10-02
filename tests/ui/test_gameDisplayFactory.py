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

# browser build tests --------------------------------------------------------
def test_browserBuildUsesTheConfiguredSizeAndRefitsTheCanvas(monkeypatch):
    # prepare: pygbag's `platform` module, which reaches the page
    monkeypatch.setattr("ui.gameDisplayFactory.sys.platform", "emscripten")
    page = MagicMock()
    monkeypatch.setitem(__import__("sys").modules, "platform", page)
    factory = GameDisplayFactory()
    newDisplay = MagicMock()

    # execute
    with patch("ui.gameDisplayFactory.pygame.display") as display:
        display.set_mode.return_value = newDisplay
        result = factory.createGameDisplay(getTestConfig(fullscreen=True))

    # assert: neither RESIZABLE (the page would pick a square) nor FULLSCREEN
    display.set_mode.assert_called_once_with((1280, 720))
    assert result == newDisplay
    page.window.eval.assert_called_once_with("window.dispatchEvent(new Event('resize'))")

def test_browserBuildStillStartsWhenTheCanvasCannotBeRefit(monkeypatch, capsys):
    monkeypatch.setattr("ui.gameDisplayFactory.sys.platform", "emscripten")
    page = MagicMock()
    page.window.eval.side_effect = RuntimeError("no page")
    monkeypatch.setitem(__import__("sys").modules, "platform", page)

    with patch("ui.gameDisplayFactory.pygame.display") as display:
        GameDisplayFactory().createGameDisplay(getTestConfig(fullscreen=False))

    display.set_mode.assert_called_once_with((1280, 720))
    assert "could not fit the canvas" in capsys.readouterr().out

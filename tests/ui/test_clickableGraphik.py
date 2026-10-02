from unittest.mock import MagicMock

import pygame
import pytest

from ui.clickableGraphik import ClickableGraphik


# helper methods -------------------------------------------------------------
@pytest.fixture
def graphik(monkeypatch):
    pygame.font.init()
    # the mouse is nowhere near, and not held: only a registered click can fire a button
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (-1, -1))
    monkeypatch.setattr(pygame.mouse, "get_pressed", lambda *args: (0, 0, 0))
    return ClickableGraphik(pygame.Surface((400, 300)))

def drawButton(graphik, function):
    graphik.drawButton(100, 100, 80, 40, (255, 255, 255), (0, 0, 0), 20, "go", function)


# click tests ----------------------------------------------------------------
def test_aClickOnTheButtonFiresItOnce(graphik):
    function = MagicMock()
    graphik.registerClick((140, 120))

    drawButton(graphik, function)
    drawButton(graphik, function)

    function.assert_called_once()
    assert graphik.pendingClick is None

def test_aClickBesideTheButtonDoesNotFireIt(graphik):
    function = MagicMock()
    graphik.registerClick((190, 120))

    drawButton(graphik, function)

    function.assert_not_called()

def test_aClearedClickFiresNothingLater(graphik):
    function = MagicMock()
    graphik.registerClick((140, 120))
    graphik.clearClick()

    drawButton(graphik, function)

    function.assert_not_called()

def test_aHeldButtonStillFiresWithoutAClick(graphik, monkeypatch):
    monkeypatch.setattr(pygame.mouse, "get_pos", lambda: (140, 120))
    monkeypatch.setattr(pygame.mouse, "get_pressed", lambda *args: (1, 0, 0))
    function = MagicMock()

    drawButton(graphik, function)

    function.assert_called_once()

def test_theButtonIsStillDrawn(graphik):
    graphik.registerClick((140, 120))

    drawButton(graphik, MagicMock())

    assert tuple(graphik.getGameDisplay().get_at((102, 102)))[:3] == (255, 255, 255)

"""Feature parity between the 2D window and the 3D one (src/strata_view).

None of these need Strata or graphik's 3D grid view, so they run everywhere
the rest of the suite does: the 3D window's key table and its stand-in for
graphik are plain Python.
"""

import os
import re
from unittest.mock import MagicMock

import pygame
import pytest

from screen.mainMenuScreen import MainMenuScreen
from screen.resultsScreen import ResultsScreen
from screen.setupScreen import SetupScreen
from simulation.config import Config
from strata_view.keys import STRATA_CONTROLS_HINT, STRATA_SCANCODE_KEYS, pygameKeyFor
from strata_view.ui import RecordingGraphik, UiButton, drawScreen

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src")


def keysHandledBy(path):
    with open(os.path.join(SRC, path)) as file:
        return set(re.findall(r"pygame\.(K_\w+)", file.read()))


def test_every_key_the_2d_simulation_screen_handles_has_a_3d_key():
    # parity is a requirement: a key added to the 2D screen fails here until
    # the 3D window has it too
    handled = keysHandledBy(os.path.join("screen", "simulationScreen.py"))
    assert handled  # the scan found the key handler
    assert handled <= set(STRATA_SCANCODE_KEYS.values())


def test_every_3d_key_is_a_real_pygame_key_and_each_scancode_is_distinct():
    for scancode, name in STRATA_SCANCODE_KEYS.items():
        assert pygameKeyFor(scancode, pygame) == getattr(pygame, name)
    assert len(set(STRATA_SCANCODE_KEYS.values())) == len(STRATA_SCANCODE_KEYS)
    assert pygameKeyFor(999, pygame) is None


def test_the_controls_hint_names_every_key_and_fits_a_1280_pixel_window():
    hint = " ".join(STRATA_CONTROLS_HINT)
    for word in ("Space", "Esc", "[ ]", "L ", "D ", "R ", "Q ", "C ", "P ", "K ", "W ", "F ", "B ",
                 "V ", "Up/Down", "H ", "E ", "M ", "F11", "Click"):
        assert word in hint
    for line in STRATA_CONTROLS_HINT:
        assert len(line) * 11 <= 1280 - 36


def mockGraphik():
    graphik = MagicMock()
    graphik.getGameDisplay.return_value.get_size.return_value = (1280, 720)
    return graphik


def drawn2d(screen):
    """Texts and buttons a 2D screen draws in one frame, through a mock graphik."""
    screen.drawText()
    if hasattr(screen, "drawMenuButtons"):
        screen.drawMenuButtons()
    screen.drawVersion()
    texts = [call.args[0] for call in screen.graphik.drawText.call_args_list]
    buttons = [(call.args[7], call.args[8]) for call in screen.graphik.drawButton.call_args_list]
    return texts, buttons


def drawn3d(screen):
    graphik = RecordingGraphik(1280, 720)
    screen.graphik = graphik
    items = drawScreen(screen, graphik)
    return graphik.texts(), [(b.text, b.function) for b in items if isinstance(b, UiButton)]


def menuScreens():
    config = Config()
    simulation = MagicMock()
    simulation.getGridSize.return_value = 20
    simulation.getNumEntities.return_value = 300
    simulation.getNumTicks.return_value = 42
    results = ResultsScreen(mockGraphik())
    results.initializeWithSimulation(simulation)
    return [MainMenuScreen(mockGraphik()), SetupScreen(mockGraphik(), config), results]


@pytest.mark.parametrize("index", range(3))
def test_the_3d_menus_show_every_text_and_button_of_the_2d_ones(index):
    screen = menuScreens()[index]
    texts2d, buttons2d = drawn2d(screen)
    texts3d, buttons3d = drawn3d(screen)
    assert texts3d == texts2d
    # the same buttons, running the 2D screen's own functions
    assert buttons3d == buttons2d


def test_a_click_on_a_3d_button_runs_the_2d_button(tmp_path):
    config = Config()
    config.gridSize = 20
    setup = SetupScreen(None, config)
    graphik = RecordingGraphik(1280, 720)
    setup.graphik = graphik
    items = drawScreen(setup, graphik)
    plus = [b for b in items if isinstance(b, UiButton) and b.text == "+"][0]  # gridSize's, drawn first
    assert graphik.click((plus.x + 1, plus.y + 1))
    assert config.gridSize == 21
    start = [b for b in items if isinstance(b, UiButton) and b.text == "start simulation"][0]
    graphik.click((start.x + start.width - 1, start.y + start.height - 1))
    assert setup.changeScreen
    # just past the box is not a click on it, as in ClickableGraphik
    assert not graphik.click((start.x + start.width, start.y))


def test_3d_is_the_default_on_linux_and_windows_desktops():
    from apex import chooseInterface, parseArguments

    assert chooseInterface(parseArguments([]), "linux") == "3d"
    assert chooseInterface(parseArguments([]), "win32") == "3d"
    assert chooseInterface(parseArguments([]), "darwin") == "2d"  # no Strata build there
    assert chooseInterface(parseArguments(["--2d"]), "linux") == "2d"
    assert chooseInterface(parseArguments(["--text"]), "linux") == "text"
    assert chooseInterface(parseArguments(["--strata"]), "darwin") == "3d"


def test_without_strata_the_2d_window_opens_and_says_why(capsys, monkeypatch):
    import apex
    import strata_view.app as app
    from strata_view import StrataUnavailable

    def unavailable(recordPath=None):
        raise StrataUnavailable("the strata-engine package isn't installed")

    monkeypatch.setattr(app, "runStrataApex", unavailable)
    assert apex.runStrataMode(apex.parseArguments([])) is False
    assert "strata-engine package isn't installed" in capsys.readouterr().out
    with pytest.raises(SystemExit) as stopped:
        apex.runStrataMode(apex.parseArguments(["--strata"]))
    assert "couldn't start" in str(stopped.value)

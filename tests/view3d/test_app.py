"""The 3D window's screens and simulation loop (src/strata_view/app.py),
driven without a window: StrataApex runs the 2D screen objects, so every key
and button goes through the same code as in the 2D window."""

from unittest.mock import MagicMock

import pygame
import pytest

from entity.chicken import Chicken
from screen.screenType import ScreenType
from strata_view.app import StrataApex
from strata_view.keys import STRATA_SCANCODE_KEYS
from strata_view.ui import UiButton

SCANCODE = {name: code for code, name in STRATA_SCANCODE_KEYS.items()}


class Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


@pytest.fixture
def app():
    return StrataApex(usageReporting=MagicMock(), clock=Clock())


def press(app, name):
    app.handleKeyDown(SCANCODE[name])


def button(app, text):
    return [b for b in app.drawMenu() if isinstance(b, UiButton) and b.text == text][0]


def click(app, text):
    target = button(app, text)
    app.handleClick((target.x + 1, target.y + 1))


def startSimulation(app, gridSize=16):
    app.goTo(ScreenType.SETUP_SCREEN)
    app.config.gridSize = gridSize
    click(app, "start simulation")
    assert app.currentScreen is app.simulationScreen


def test_the_screens_follow_one_another_as_in_2d(app):
    assert app.currentScreen is app.mainMenuScreen
    app.handleKeyDown(4)  # any key
    assert app.currentScreen is app.setupScreen
    click(app, "main menu")
    assert app.currentScreen is app.mainMenuScreen
    click(app, "create new sim")
    assert app.currentScreen is app.setupScreen
    app.handleKeyDown(4)  # the setup screen takes no keys
    assert app.currentScreen is app.setupScreen
    click(app, "start simulation")
    assert app.currentScreen is app.simulationScreen
    app.usageReporting.reportSimulationStarted.assert_called_once()


def test_the_quit_button_closes_the_window(app):
    click(app, "quit")
    assert app.running is False


def test_the_setup_buttons_change_the_settings(app):
    app.goTo(ScreenType.SETUP_SCREEN)
    app.config.gridSize, app.config.grassFactor, app.config.grassGrowTime = 20, 5, 200
    pluses = [b for b in app.drawMenu() if isinstance(b, UiButton) and b.text == "+"]
    minuses = [b for b in app.drawMenu() if isinstance(b, UiButton) and b.text == "-"]
    for b in pluses:
        app.handleClick((b.x + 1, b.y + 1))
    assert (app.config.gridSize, app.config.grassFactor, app.config.grassGrowTime) == (21, 6, 210)
    for b in minuses:
        app.handleClick((b.x + 1, b.y + 1))
        app.handleClick((b.x + 1, b.y + 1))
    assert (app.config.gridSize, app.config.grassFactor, app.config.grassGrowTime) == (19, 4, 190)


def test_every_key_goes_to_the_2d_simulation_screens_handler(app):
    startSimulation(app)
    seen = []
    app.simulationScreen.handleKeyDownEvent = seen.append
    for code, name in STRATA_SCANCODE_KEYS.items():
        app.handleKeyDown(code)
    assert seen == [getattr(pygame, name) for name in STRATA_SCANCODE_KEYS.values()]


def test_simulation_keys_do_what_they_do_in_2d(app):
    startSimulation(app)
    screen, config = app.simulationScreen, app.config
    press(app, "K_SPACE")
    assert screen.isPaused()
    press(app, "K_ESCAPE")
    assert not screen.isPaused()
    press(app, "K_d")
    assert screen.isDebugEnabled()
    chickens = screen.simulation.getNumberOfLivingEntitiesOfType(Chicken)
    press(app, "K_c")
    assert screen.simulation.getNumberOfLivingEntitiesOfType(Chicken) == chickens + 1
    speed = config.tickSpeed
    press(app, "K_RIGHTBRACKET")
    assert config.tickSpeed == speed + 1
    press(app, "K_LEFTBRACKET")
    assert config.tickSpeed == speed
    limit = config.limitTickSpeed
    press(app, "K_l")
    assert config.limitTickSpeed is not limit
    press(app, "K_v")
    assert config.localView
    size = config.localViewSize
    press(app, "K_UP")
    assert config.localViewSize == size + 1
    press(app, "K_DOWN")
    assert config.localViewSize == size
    press(app, "K_h")
    assert config.highlightOldestEntity
    press(app, "K_e")
    assert not config.eyesEnabled
    press(app, "K_m")
    assert config.muted and screen.caption.endswith("(muted)")
    press(app, "K_r")
    assert app.currentScreen is app.setupScreen


def test_q_quits(app):
    startSimulation(app)
    press(app, "K_q")
    assert app.running is False


def test_f11_without_a_fullscreen_capable_strata_says_so(app):
    renderer = MagicMock()
    renderer.isWindow = True
    renderer.setFullscreen.return_value = False
    app.renderer = renderer
    startSimulation(app)
    press(app, "K_F11")
    renderer.setFullscreen.assert_called_once_with(True)
    assert app.config.fullscreen is False
    assert "Fullscreen" in app.notice


def test_f11_switches_a_capable_window(app):
    renderer = MagicMock()
    renderer.isWindow = True
    renderer.setFullscreen.return_value = True
    app.renderer = renderer
    startSimulation(app)
    press(app, "K_F11")
    assert app.config.fullscreen is True


def test_steps_tick_at_the_2d_pace_and_hold_while_paused(app):
    startSimulation(app)
    simulation = app.simulationScreen.simulation
    app.config.limitTickSpeed = True
    app.advance()
    assert simulation.numTicks == 1
    app.advance()  # not due yet
    assert simulation.numTicks == 1
    app.clock.now += app.tickDelay()
    app.advance()
    assert simulation.numTicks == 2
    press(app, "K_SPACE")
    app.clock.now += 10
    app.advance()
    assert simulation.numTicks == 2


def test_the_results_follow_once_every_living_entity_is_gone(app):
    startSimulation(app)
    simulation = app.simulationScreen.simulation
    for entityId in list(simulation.livingEntityIds):
        simulation.removeEntity(simulation.entities[entityId])
    app.advance()
    assert app.currentScreen is app.simulationScreen  # the 2D window holds the last frame a second
    app.clock.now += 1.0
    app.advance()
    assert app.currentScreen is app.resultsScreen
    assert app.resultsScreen.simulation is simulation
    app.handleClick((5, 5))  # a click anywhere, or any key, returns to setup
    assert app.currentScreen is app.setupScreen


def test_a_dead_selected_entity_is_deselected_and_ends_local_view(app):
    startSimulation(app)
    screen = app.simulationScreen
    entity = screen.simulation.entities[screen.simulation.livingEntityIds[0]]
    screen.setSelectedEntity(entity)
    app.config.localView = True
    screen.simulation.removeEntity(entity)
    app.advance()
    assert screen.getSelectedEntity() is None
    assert app.config.localView is False


def test_closing_the_window_finishes_the_recording(app):
    recording = MagicMock()
    recording.close.return_value = "out.usda"
    app.recording = recording
    startSimulation(app)
    app.renderer = MagicMock()
    event = MagicMock()
    event.type = app.renderer.strata.EVENT_QUIT
    app.handleEvent(event)
    recording.close.assert_called_once()
    assert app.running is False

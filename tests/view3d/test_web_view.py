"""The browser's 3D view (src/strata_view/web.py), without a browser.

WebApex runs against the headless pygame driver and a stand-in page whose
grid relay is graphik's RecordingRelay, which keeps every message the game
sends; graphik's wire decoder reads them back. pygbag's own pieces (the
page's toggle and window) are the stand-in's. The 2D screens' loops aren't
run: the tests set the screen Apex.run would be on and call update3D(), one
display frame of the 3D view, as its task does.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402
import pytest  # noqa: E402

pytest.importorskip("preponderous.graphik.grid3d")

from preponderous.graphik.grid3d import Unavailable  # noqa: E402
from preponderous.graphik.grid3d import web as grid3dweb  # noqa: E402

from screen.screenType import ScreenType  # noqa: E402
from strata_view import web  # noqa: E402
from strata_view.keys import STRATA_CONTROLS_HINT, WEB_CONTROLS_HINT  # noqa: E402
from strata_view.web import WebApex, compactStats, layoutScale, touchButtons, unavailableMessage  # noqa: E402
from strata_view.ui import UiButton, UiText  # noqa: E402

PHONE = (390, 844)
PHONE_LANDSCAPE = (844, 390)
DESKTOP = (1280, 800)


class Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


class Page:
    """The page around the game: a 3D toggle, a size and a grid relay."""

    def __init__(self, size=PHONE, failOpen=None, relayState="ready", button=None):
        self.button = button
        self.on = False
        self.size_ = size
        self.failOpen = failOpen
        self.relay = grid3dweb.RecordingRelay(state=relayState)
        self.toggles = []
        self.opened = 0

    def wants3D(self):
        return self.on

    def set3D(self, on, reason=""):
        self.toggles.append((bool(on), reason))
        self.on = bool(on)

    def size(self):
        return self.size_

    def buttonArea(self):
        return self.button

    def openView(self, width, height):
        if self.failOpen:
            raise Unavailable(self.failOpen)
        self.opened += 1
        self.relay = grid3dweb.RecordingRelay(state=self.relay.status)
        return grid3dweb.Grid3DWebView.open(width, height, relay=self.relay)


@pytest.fixture
def page():
    return Page()


@pytest.fixture
def game(page, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TRACE_USAGE_REPORTING", "off")
    game = WebApex(page=page, clock=Clock())
    try:
        yield game
    finally:
        pygame.quit()


def decoded(page, kind=None):
    messages = [grid3dweb.decode(m) for m in page.relay.messages]
    return [body for k, body in messages if kind is None or k == kind]


def lastHud(page):
    huds = decoded(page, grid3dweb.HUD)
    return huds[-1] if huds else None


def texts(page):
    hud = lastHud(page)
    return [label["text"] for label in hud["labels"]] if hud else []


def labelCentre(page, text, nth=0):
    labels = [label for label in lastHud(page)["labels"] if label["text"] == text]
    label = labels[nth]
    return (label["x"] + label["pixelSize"] * len(text) / 2.0, label["y"] + label["pixelSize"] / 2.0)


def fitsWindow(page, size):
    width, height = size
    return all(
        label["x"] >= -0.5 and label["x"] + label["pixelSize"] * len(label["text"]) <= width + 0.5
        and label["y"] >= -0.5 and label["y"] + label["pixelSize"] <= height + 0.5
        for label in lastHud(page)["labels"]
    )


def go(game, screenType):
    """What Apex.run does with a screen's result."""
    if screenType == ScreenType.SETUP_SCREEN:
        game.currentScreen = game.setupScreen
    elif screenType == ScreenType.MAIN_MENU_SCREEN:
        game.currentScreen = game.mainMenuScreen
    elif screenType == ScreenType.SIMULATION_SCREEN:
        game.config.calculateValues()
        game.simulationScreen.initializeSimulation()
        game.currentScreen = game.simulationScreen
    elif screenType == ScreenType.RESULTS_SCREEN:
        game.currentScreen = game.resultsScreen
        game.resultsScreen.initializeWithSimulation(game.simulationScreen.simulation)


def startSimulation(game, gridSize=16):
    game.config.gridSize = gridSize
    go(game, ScreenType.SIMULATION_SCREEN)


def on3D(game, page):
    page.on = True
    game.update3D()
    assert game.view3d is not None


# -- the toggle


def test_the_game_starts_in_2d_and_opens_nothing_of_the_3d_view(game, page):
    game.update3D()
    assert game.view3d is None and page.opened == 0


def test_a_page_that_starts_in_3d_gets_the_main_menu_in_3d_and_its_first_press(tmp_path, monkeypatch):
    # the page may start in 3D (a remembered choice, ?view=3d): the game assumes nothing
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TRACE_USAGE_REPORTING", "off")
    page = Page()
    page.on = True
    game = WebApex(page=page, clock=Clock())
    try:
        game.update3D()  # the 3D task's very first frame
        assert game.view3d is not None and page.opened == 1
        assert "create new sim" in texts(page)
        game.press(labelCentre(page, "create new sim"))
        assert game.mainMenuScreen.changeScreen
        assert page.toggles == []  # the toggle was left as the page set it
    finally:
        pygame.quit()


def test_the_toggle_opens_the_3d_view_and_closes_it_again(game, page):
    on3D(game, page)
    assert page.opened == 1
    page.on = False
    game.update3D()
    assert game.view3d is None and page.relay.closed


def test_a_3d_view_that_cant_open_leaves_2d_and_says_why(page, game):
    page.failOpen = "WebGL 2 isn't available"
    page.on = True
    game.update3D()
    assert game.view3d is None
    assert page.toggles[-1][0] is False
    assert "WebGL 2 isn't available" in page.toggles[-1][1]
    assert page.toggles[-1][1] == unavailableMessage("WebGL 2 isn't available")


def test_a_3d_view_that_fails_while_loading_goes_back_to_2d_with_the_reason(game, page):
    on3D(game, page)
    page.relay.status = "failed:the engine didn't load"
    page.on = False
    game.update3D()
    assert game.view3d is None
    assert "the engine didn't load" in page.toggles[-1][1]


def test_an_error_in_the_3d_view_never_stops_the_2d_game(game, page, monkeypatch):
    on3D(game, page)
    monkeypatch.setattr(game, "draw3D", lambda: 1 / 0)
    game.update3D()  # does not raise
    assert game.view3d is None and page.on is False
    assert "division by zero" in page.toggles[-1][1]


def test_the_plain_words_reason():
    assert unavailableMessage("too big.") == "No 3D view here (too big). The 2D view stays."
    assert "could not load" in unavailableMessage("")


# -- the menus, setup and results


def test_the_3d_main_menu_shows_the_2d_one_and_its_button_works(game, page):
    on3D(game, page)
    shown = texts(page)
    assert "Apex" in shown and "press any key to start!" in shown and "create new sim" in shown
    view = decoded(page, grid3dweb.VIEW)[-1]
    assert view["clearColor"][:3] == pytest.approx((0.0, 0.0, 0.0))  # the 2D black
    game.press(labelCentre(page, "create new sim"))
    assert game.mainMenuScreen.changeScreen
    assert game.mainMenuScreen.nextScreen == ScreenType.SETUP_SCREEN


@pytest.mark.parametrize("size", [PHONE, PHONE_LANDSCAPE, DESKTOP])
def test_every_menu_fits_the_window(game, page, size):
    page.size_ = size
    on3D(game, page)
    assert fitsWindow(page, size)
    go(game, ScreenType.SETUP_SCREEN)
    game.update3D()
    assert fitsWindow(page, size)
    startSimulation(game)
    go(game, ScreenType.RESULTS_SCREEN)
    game.update3D()
    assert fitsWindow(page, size)


def test_setup_minus_and_plus_change_the_setting_in_3d(game, page):
    go(game, ScreenType.SETUP_SCREEN)
    game.config.gridSize = 30
    on3D(game, page)
    assert "gridSize: 30" in texts(page)
    game.press(labelCentre(page, "-", 0))  # gridSize's, drawn first
    assert game.config.gridSize == 29
    game.update3D()
    assert "gridSize: 29" in texts(page)
    game.press(labelCentre(page, "+", 0))
    game.press(labelCentre(page, "+", 0))
    assert game.config.gridSize == 31
    grass = game.config.grassFactor
    game.press(labelCentre(page, "+", 1))
    assert game.config.grassFactor == min(10, grass + 1)
    game.press(labelCentre(page, "start simulation"))
    assert game.setupScreen.changeScreen
    assert game.setupScreen.nextScreen == ScreenType.SIMULATION_SCREEN


@pytest.mark.parametrize("size", [PHONE, PHONE_LANDSCAPE, DESKTOP])
def test_buttons_are_big_enough_to_tap_and_cover_nothing(game, page, size):
    page.size_ = size
    go(game, ScreenType.SETUP_SCREEN)
    on3D(game, page)
    buttons = game.menuButtons
    assert len(buttons) == 8  # main menu, start, and - and + for three settings
    for button in buttons:
        # as tall as the room below allows: setup stacks its rows closer on smaller windows
        assert button.height >= {PHONE: 30, PHONE_LANDSCAPE: 18, DESKTOP: web.MIN_TAP}[size]
        assert 0 <= button.x and button.x + button.width <= size[0]
    buttonTexts = {button.text for button in buttons}
    for label in lastHud(page)["labels"]:
        if label["text"] in buttonTexts:
            continue
        right = label["x"] + label["pixelSize"] * len(label["text"])
        bottom = label["y"] + label["pixelSize"]
        for b in buttons:  # no setting's text is hidden under a button
            assert not (label["x"] < b.x + b.width and b.x < right
                        and label["y"] < b.y + b.height and b.y + 1 < bottom), (label["text"], b.text)
    for a in buttons:
        for b in buttons:
            if a is not b:
                assert not (a.x < b.x + b.width and b.x < a.x + a.width
                            and a.y < b.y + b.height and b.y < a.y + a.height), (a.text, b.text)


def test_a_press_off_every_button_does_nothing(game, page):
    go(game, ScreenType.SETUP_SCREEN)
    on3D(game, page)
    size = game.config.gridSize
    game.press((2, 2))
    assert game.config.gridSize == size and not game.setupScreen.changeScreen


def test_a_press_anywhere_on_the_3d_results_returns_to_setup(game, page):
    startSimulation(game)
    go(game, ScreenType.RESULTS_SCREEN)
    on3D(game, page)
    assert "Results" in texts(page)
    assert any(text.startswith("ticks: ") for text in texts(page))
    game.press((5, 5))
    assert game.resultsScreen.changeScreen
    assert game.resultsScreen.nextScreen == ScreenType.SETUP_SCREEN


def test_relay_presses_reach_the_screen(game, page):
    go(game, ScreenType.SETUP_SCREEN)
    on3D(game, page)
    x, y = labelCentre(page, "main menu")
    page.relay.events.append({"type": grid3dweb.EVENT_MOUSE_BUTTON_DOWN, "x": x, "y": y,
                              "button": 1, "pointer": "touch"})
    game.update3D()
    assert game.setupScreen.changeScreen
    assert game.setupScreen.nextScreen == ScreenType.MAIN_MENU_SCREEN


def test_a_resize_lays_the_screen_out_again(game, page):
    on3D(game, page)
    page.relay.events.append({"type": grid3dweb.EVENT_RESIZED, "width": 844, "height": 390})
    game.update3D()
    assert (game.view3d.width, game.view3d.height) == (844, 390)
    assert fitsWindow(page, (844, 390))


# -- the simulation


def test_the_simulation_is_sent_as_a_board_its_pieces_and_a_hud(game, page):
    startSimulation(game)
    on3D(game, page)
    kinds = [grid3dweb.decode(m)[0] for m in page.relay.messages]
    for kind in (grid3dweb.BOARD, grid3dweb.VIEW, grid3dweb.PIECES, grid3dweb.HUD):
        assert kind in kinds
    pieces = decoded(page, grid3dweb.PIECES)[-1]
    assert len(pieces["anchors"]) > 0
    assert decoded(page, grid3dweb.VIEW)[-1]["clearColor"][:3] == pytest.approx((0.0, 0.0, 0.0))
    shown = texts(page)
    assert any(text.startswith("Apex - S") for text in shown)  # the caption, cut to fit a phone
    assert any(text.startswith("Space/Esc pause") for text in shown)


def test_only_what_changed_is_sent(game, page):
    startSimulation(game)
    on3D(game, page)
    page.relay.messages.clear()
    game.update3D()
    assert page.relay.messages == []  # nothing changed, nothing sent
    simulation = game.simulationScreen.simulation
    simulation.update()
    simulation.numTicks += 1
    game.clock.now += web.MIN_STEP_SECONDS
    game.update3D()
    kinds = [grid3dweb.decode(m)[0] for m in page.relay.messages]
    assert grid3dweb.PIECES in kinds


def test_a_64_by_64_board_goes_as_merged_tiles(game, page):
    startSimulation(game, gridSize=64)
    on3D(game, page)
    board = decoded(page, grid3dweb.BOARD)[-1]
    assert 4 < len(board["shapes"]) < 64 * 64  # grass comes in shades, so runs are short


def test_the_board_follows_the_2d_keys(game, page):
    startSimulation(game)
    on3D(game, page)
    screen = game.simulationScreen
    page.relay.messages.clear()
    screen.handleKeyDownEvent(pygame.K_c)  # spawn a chicken, even while paused
    game.clock.now += web.MIN_STEP_SECONDS  # drawn as a step is, within MIN_STEP_SECONDS
    game.update3D()
    assert decoded(page, grid3dweb.PIECES)
    page.relay.messages.clear()
    screen.handleKeyDownEvent(pygame.K_e)  # eyes off
    game.update3D()
    assert decoded(page, grid3dweb.PIECES)


def test_statistics_and_pause_show_in_the_3d_hud(game, page):
    startSimulation(game)
    on3D(game, page)
    screen = game.simulationScreen
    screen.handleKeyDownEvent(pygame.K_d)
    game.update3D()
    shown = texts(page)
    for stat in ("Num Ticks:", "Living Entities:", "Grass:", "Rabbits:"):
        assert stat in shown
    assert "PAUSED" not in shown
    screen.handleKeyDownEvent(pygame.K_SPACE)
    game.update3D()
    assert "PAUSED" in texts(page)
    assert fitsWindow(page, PHONE)


def test_statistics_fit_a_short_window_on_one_line_each(game, page):
    page.size_ = PHONE_LANDSCAPE
    startSimulation(game)
    on3D(game, page)
    game.simulationScreen.handleKeyDownEvent(pygame.K_d)
    game.update3D()
    shown = texts(page)
    assert any(text.startswith("Num Ticks: ") for text in shown)
    assert fitsWindow(page, PHONE_LANDSCAPE)


def test_the_controls_hint_shows_at_the_start_and_while_paused(game, page):
    startSimulation(game)
    on3D(game, page)
    assert any(text.startswith("Space/Esc pause") for text in texts(page))
    game.clock.now += web.CONTROLS_SECONDS + 1
    game.update3D()
    assert not any(text.startswith("Space/Esc pause") for text in texts(page))
    game.simulationScreen.handleKeyDownEvent(pygame.K_SPACE)
    game.update3D()
    assert any(text.startswith("Space/Esc pause") for text in texts(page))


def test_a_press_on_a_tile_shows_its_contents_beside_it_and_selects_its_entity(game, page):
    startSimulation(game)
    on3D(game, page)
    screen = game.simulationScreen
    grid = screen.simulation.environment.getGrid()
    entity = screen.simulation.entities[screen.simulation.livingEntityIds[0]]
    location = grid.getLocation(entity.getLocationID())
    location.removeEntity(entity)
    location.addEntity(entity)  # on top
    column, row = location.getX(), location.getY()
    at = game.view3d.cellScreenPosition(column, row, y=0.06)
    assert game.selectAt(at) is location
    assert screen.getSelectedEntity() is entity
    game.update3D()
    hud = lastHud(page)
    alert = [label for label in hud["labels"] if label["text"] == "Location (%d, %d)" % (column, row)]
    assert alert
    assert abs(alert[0]["y"] + alert[0]["pixelSize"] / 2 - at[1]) < 60
    assert fitsWindow(page, PHONE)
    # the 2D alert keeps its 2D place
    assert screen.getTextAlerts()[-1].cell == (column, row)


def test_a_press_off_the_board_or_in_local_view_selects_nothing(game, page):
    startSimulation(game)
    on3D(game, page)
    screen = game.simulationScreen
    game.press((PHONE[0] / 2, 2))
    assert screen.getTextAlerts() == []
    game.config.localView = True
    game.press(game.view3d.cellScreenPosition(8, 8, y=0.06))
    assert screen.getTextAlerts() == []


def test_local_view_shows_the_square_around_the_selected_entity(game, page):
    startSimulation(game)
    on3D(game, page)
    screen = game.simulationScreen
    screen.setSelectedEntity(screen.simulation.entities[screen.simulation.livingEntityIds[0]])
    screen.handleKeyDownEvent(pygame.K_v)
    page.relay.messages.clear()
    game.update3D()
    assert game.view3d.board.shownSize() == (2 * game.config.localViewSize + 1,) * 2
    assert decoded(page, grid3dweb.BOARD)


def test_no_board_once_every_living_entity_is_gone(game, page):
    startSimulation(game)
    on3D(game, page)
    simulation = game.simulationScreen.simulation
    for entityId in list(simulation.livingEntityIds):
        simulation.removeEntity(simulation.entities[entityId])
    page.relay.messages.clear()
    game.update3D()
    assert decoded(page, grid3dweb.BOARD)[-1]["shapes"] == []
    assert decoded(page, grid3dweb.PIECES)[-1]["anchors"] == []


def test_back_to_a_menu_the_board_is_cleared_and_back_again_it_returns(game, page):
    startSimulation(game)
    on3D(game, page)
    go(game, ScreenType.RESULTS_SCREEN)
    page.relay.messages.clear()
    game.update3D()
    assert decoded(page, grid3dweb.BOARD)[-1]["shapes"] == []
    assert decoded(page, grid3dweb.PIECES)[-1]["anchors"] == []
    startSimulation(game)
    page.relay.messages.clear()
    game.update3D()
    assert decoded(page, grid3dweb.BOARD)[-1]["shapes"]
    assert decoded(page, grid3dweb.PIECES)[-1]["anchors"]


def test_switching_views_mid_simulation_keeps_the_same_simulation(game, page):
    startSimulation(game)
    simulation = game.simulationScreen.simulation
    on3D(game, page)
    simulation.update()
    page.on = False
    game.update3D()
    page.on = True
    game.update3D()
    assert game.simulationScreen.simulation is simulation
    assert decoded(page, grid3dweb.BOARD) and decoded(page, grid3dweb.PIECES)


# -- the pieces


def test_layout_scale():
    assert layoutScale(1280, 720) == 1.0
    assert layoutScale(390, 844) == pytest.approx(390 / 640.0)
    assert layoutScale(844, 390) == pytest.approx(390 / 720.0)


def test_touch_buttons_grow_to_their_label_and_a_tap():
    item = UiButton(185, 100, 20, 20, (255, 255, 255), (0, 0, 0), 30, "start simulation", None)
    (button,) = touchButtons([item], 390)
    assert button.width >= len("start simulation") * 15 and button.height >= web.MIN_TAP
    assert button.x + button.width / 2 == pytest.approx(195)
    # near an edge, it is moved inside the window
    (button,) = touchButtons([UiButton(0, 0, 20, 20, (0, 0, 0), (0, 0, 0), 30, "main menu", None)], 390)
    assert button.x >= 8


def test_compact_stats_only_on_a_short_window():
    items = [UiText(text, 100, 10 + 20 * i, 20, (0, 0, 0)) for i, text in
             enumerate(["Num Ticks:", "5", "", "Grass:", "9", ""] * 6)]
    assert compactStats(items, 844) == items
    lines = compactStats(items, 300)
    assert [line.text for line in lines[:2]] == ["Num Ticks: 5", "Grass: 9"]
    assert max(line.y for line in lines) < 300


def test_the_web_controls_hint_names_every_2d_key_a_browser_has():
    hint = " ".join(WEB_CONTROLS_HINT)
    for word in ("Space", "Esc", "[ ]", "L ", "D ", "R ", "Q ", "C ", "P ", "K ", "W ", "F ", "B ",
                 "V ", "Up/Down", "H ", "E ", "M ", "Tap"):
        assert word in hint
    # F11 is the browser's own
    assert "F11" in " ".join(STRATA_CONTROLS_HINT) and "F11" not in hint


def test_main_runs_webapex_only_in_a_browser():
    import runpy
    from unittest.mock import patch

    with patch("asyncio.run", side_effect=lambda coroutine: coroutine.close()):
        main = runpy.run_path(os.path.join(os.path.dirname(web.__file__), "..", "main.py"))
    from apex import Apex

    assert main["chooseGame"]("linux") is Apex
    assert main["chooseGame"]("emscripten") is WebApex


# -- the page's 2D/3D button, which the 3D text and buttons keep clear of

# where graphik's template puts the button on a 390-pixel phone (top right)
PHONE_BUTTON = (326, 8, 56, 36)


def underButton(page, area):
    x0, y0, w0, h0 = area
    return [label["text"] for label in lastHud(page)["labels"]
            if label["x"] < x0 + w0 and x0 < label["x"] + label["pixelSize"] * len(label["text"])
            and label["y"] < y0 + h0 and y0 < label["y"] + label["pixelSize"]]


def test_opening_the_view_and_a_resize_read_where_the_button_is(game, page):
    page.button = PHONE_BUTTON
    on3D(game, page)
    assert game.keepClear == PHONE_BUTTON
    page.button = (780, 8, 56, 36)
    page.relay.events.append({"type": grid3dweb.EVENT_RESIZED, "width": 844, "height": 390})
    game.update3D()
    assert game.keepClear == (780, 8, 56, 36)


@pytest.mark.parametrize("size,button", [(PHONE, PHONE_BUTTON), (PHONE_LANDSCAPE, (780, 8, 56, 36)),
                                         (DESKTOP, (1216, 8, 56, 36))])
def test_no_text_or_button_under_the_2d_3d_button(game, page, size, button):
    page.size_, page.button = size, button
    on3D(game, page)
    assert underButton(page, button) == []
    go(game, ScreenType.SETUP_SCREEN)
    game.update3D()
    assert underButton(page, button) == []
    startSimulation(game)
    game.simulationScreen.handleKeyDownEvent(pygame.K_d)
    game.update3D()
    assert underButton(page, button) == []
    assert any(text.startswith("Apex - S") for text in texts(page))  # the caption, moved aside
    go(game, ScreenType.RESULTS_SCREEN)
    game.update3D()
    assert underButton(page, button) == []
    assert fitsWindow(page, size)


def test_a_menu_button_under_the_2d_3d_button_moves_below_it():
    item = UiButton(300, 10, 80, 30, (255, 255, 255), (0, 0, 0), 20, "x", None)
    (moved,) = web.buttonsClearOfButton([item], PHONE_BUTTON)
    assert moved.y >= PHONE_BUTTON[1] + PHONE_BUTTON[3]


# -- the 2D canvas and a fast simulation


def test_the_hidden_2d_canvas_isnt_drawn_on_while_3d_shows_the_board(game, page):
    startSimulation(game)
    screen = game.simulationScreen
    assert screen.isDrawingBoard()
    on3D(game, page)
    assert not screen.isDrawingBoard()
    drawn = []
    screen.drawBoard = lambda: drawn.append(True)
    page.on = False
    game.update3D()
    # back in 2D: the board is drawn now (a paused simulation draws no new step) and every step
    assert drawn == [True] and screen.isDrawingBoard()


def test_a_3d_view_still_loading_leaves_the_board_to_2d(game, page):
    page.relay.status = "loading"
    startSimulation(game)
    on3D(game, page)
    assert game.simulationScreen.isDrawingBoard()


def test_simulation_steps_rebuild_the_board_at_most_every_min_step_seconds(game, page):
    startSimulation(game)
    on3D(game, page)
    simulation = game.simulationScreen.simulation
    rebuilt = []
    original = web.simulationBoard
    try:
        web.simulationBoard = lambda *a: rebuilt.append(1) or original(*a)
        for _ in range(5):  # five steps inside one MIN_STEP_SECONDS: one rebuild at its end
            simulation.update()
            simulation.numTicks += 1
            game.clock.now += web.MIN_STEP_SECONDS / 5 - 1e-6
            game.update3D()
        assert len(rebuilt) == 0
        game.clock.now += 1e-3
        game.update3D()
        assert len(rebuilt) == 1
        # a change the player makes is drawn at once
        game.simulationScreen.handleKeyDownEvent(pygame.K_e)
        game.update3D()
        assert len(rebuilt) == 2
    finally:
        web.simulationBoard = original


# -- the on-screen keys on a touch screen (graphik's TouchKeys)


class TouchPage(Page):
    """A phone's page: a touch screen."""

    def __init__(self, size=PHONE, **kwargs):
        super().__init__(size=size, **kwargs)
        self.fitted = 0

    def touchScreen(self):
        return True

    def fitCanvas(self):
        self.fitted += 1


@pytest.fixture
def phone(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TRACE_USAGE_REPORTING", "off")
    page = TouchPage()
    game = WebApex(page=page, clock=Clock())
    try:
        yield game, page
    finally:
        pygame.quit()


def centre(slot):
    return (slot.x + slot.width / 2.0, slot.y + slot.height / 2.0)


def keyEvents():
    return [e for e in pygame.event.get() if e.type == pygame.KEYDOWN]


def tapEveryKey(game, layout, press):
    """Taps each key of every page of the bar (paging with More); returns the
    pygame keys posted, in order."""
    posted = []
    pygame.event.clear()
    for _ in range(10):
        slots = layout()
        for slot in slots:
            if slot.key is not None:
                assert press(centre(slot))
                posted += [e.key for e in keyEvents()]
        more = [slot for slot in slots if slot.key is None]
        if not more:
            break
        press(centre(more[0]))
        if game.touchKeys.page == 0:
            break
    return posted


def test_the_keys_cover_every_simulation_key_a_browser_has():
    from strata_view.keys import STRATA_SCANCODE_KEYS, TOUCH_KEYS

    pressed = {"K_" + (name.upper() if len(name) > 1 else name) for _, name in TOUCH_KEYS}
    pressed = {{"K_[": "K_LEFTBRACKET", "K_]": "K_RIGHTBRACKET"}.get(k, k) for k in pressed}
    # F11 is the browser's own; Escape pauses as Space does
    assert pressed == set(STRATA_SCANCODE_KEYS.values()) - {"K_F11", "K_ESCAPE"}
    pygame.display.init()
    try:
        for _, name in TOUCH_KEYS:
            pygame.key.key_code(name)  # a name pygame knows
    finally:
        pygame.display.quit()


def test_without_a_touch_screen_there_is_no_bar(game, page):
    assert game.screen2D is None
    assert game.graphik.gameDisplay.get_size() == (game.config.displayWidth, game.config.displayHeight)
    startSimulation(game)
    on3D(game, page)
    assert "Pause" not in texts(page)
    assert game.view3d.insets is None


def test_on_a_touch_screen_the_2d_window_has_room_for_the_bar_below_the_screens(phone):
    game, page = phone
    width, height = game.config.displayWidth, game.config.displayHeight
    assert game.graphik.gameDisplay.get_size() == (width, height)
    assert game.screen2D.get_size() == (width, height + game.band2D)
    assert page.fitted == 1
    scale, portrait = game.scale2D()
    for slot in game.touchKeys.layout(width, height + game.band2D, scale, portrait):
        assert slot.y >= height
        assert slot.width * scale >= 44 - 1e-6 and slot.height * scale >= 44 - 1e-6


def test_the_2d_bar_shows_the_keys_only_in_the_simulation(phone):
    game, page = phone
    width, height = game.screen2D.get_size()
    game.drawTouchKeys2D()
    assert not game.pressTouchKey2D((20, height - 30))  # the main menu: no keys
    startSimulation(game)
    game.drawTouchKeys2D()
    scale, portrait = game.scale2D()
    slot = game.touchKeys.layout(width, height, scale, portrait)[0]
    assert game.screen2D.get_at((int(slot.x) + 2, int(slot.y) + 2))[:3] == game.touchKeys.color


def test_every_2d_key_posts_its_key_and_the_screen_handles_it(phone):
    from strata_view.keys import TOUCH_KEYS

    game, page = phone
    startSimulation(game)
    width, height = game.screen2D.get_size()
    scale, portrait = game.scale2D()
    posted = tapEveryKey(
        game,
        lambda: game.touchKeys.layout(width, height, scale, portrait),
        game.simulationScreen.handlePointerDown,
    )
    assert posted == [pygame.key.key_code(name) for _, name in TOUCH_KEYS]


def test_a_2d_key_runs_the_screens_own_handler(phone):
    game, page = phone
    startSimulation(game)
    screen = game.simulationScreen
    width, height = game.screen2D.get_size()
    scale, portrait = game.scale2D()
    slots = {s.label: s for s in game.touchKeys.layout(width, height, scale, portrait)}
    pygame.event.clear()
    assert screen.handlePointerDown(centre(slots["Pause"]))
    for event in keyEvents():
        screen.handleKeyDownEvent(event.key)
    assert screen.isPaused()
    # a press on the board is still a click on a location
    assert not screen.handlePointerDown((50, 50))


def test_on_a_touch_screen_the_3d_board_stands_above_the_keys(phone):
    from preponderous.graphik.grid3d import projectToScreen

    game, page = phone
    startSimulation(game)
    on3D(game, page)
    view = game.view3d
    band = game.touchBand3D()
    top, bottom = view.insets
    assert bottom == band + web.BOARD_BOTTOM and top == web.BOARD_TOP
    camera = view.camera()
    board = view.board
    columns, rows = board.shownSize()
    for x in (-columns / 2.0 - 0.35, columns / 2.0 + 0.35):
        for z in (-rows / 2.0 - 0.35, rows / 2.0 + 0.35):
            sx, sy = projectToScreen(camera, (x, -0.18, z), view.width, view.height)
            assert top - 1 <= sy <= view.height - bottom + 1
            assert -0.5 <= sx <= view.width + 0.5
    sent = decoded(page, grid3dweb.VIEW)[-1]
    assert sent["eye"] == pytest.approx(camera.eye, abs=1e-4)
    assert sent["clearColor"][:3] == pytest.approx((0.0, 0.0, 0.0))  # the 2D black kept


def test_the_3d_hud_carries_the_keys_and_keeps_its_text_above_them(phone):
    game, page = phone
    startSimulation(game)
    on3D(game, page)
    view = game.view3d
    keys = {s.label for s in game.touchKeys.layout(view.width, view.height)}
    assert {"Pause", "Stats", "More"} <= keys
    shown = texts(page)
    assert keys <= set(shown)
    assert "Tap a location for its contents" in shown
    band = game.touchBand3D()
    for label in lastHud(page)["labels"]:
        if label["text"] not in keys:
            assert label["y"] + label["pixelSize"] <= PHONE[1] - band + 0.5, label["text"]
    assert fitsWindow(page, PHONE)


def test_every_3d_key_posts_its_key(phone):
    from strata_view.keys import TOUCH_KEYS

    game, page = phone
    startSimulation(game)
    on3D(game, page)
    view = game.view3d

    def press(position):
        game.press(position)
        return True

    posted = tapEveryKey(game, lambda: game.touchKeys.layout(view.width, view.height), press)
    assert posted == [pygame.key.key_code(name) for _, name in TOUCH_KEYS]


def test_a_3d_key_tap_is_not_a_press_on_a_tile(phone, monkeypatch):
    game, page = phone
    startSimulation(game)
    on3D(game, page)
    view = game.view3d
    selected = []
    monkeypatch.setattr(game, "selectAt", lambda position: selected.append(position))
    slot = game.touchKeys.layout(view.width, view.height)[0]
    game.press(centre(slot))
    assert selected == []
    game.press((view.width / 2.0, view.height / 2.0))
    assert len(selected) == 1


def test_the_3d_bar_is_only_on_the_simulation(phone):
    game, page = phone
    on3D(game, page)  # the main menu
    assert "Pause" not in texts(page)
    go(game, ScreenType.SETUP_SCREEN)
    game.update3D()
    assert "Pause" not in texts(page)


def test_the_statistics_stay_above_the_keys(phone):
    game, page = phone
    startSimulation(game)
    on3D(game, page)
    game.simulationScreen.handleKeyDownEvent(pygame.K_d)
    game.update3D()
    view = game.view3d
    keys = {s.label for s in game.touchKeys.layout(view.width, view.height)}
    band = game.touchBand3D()
    assert any(text.startswith("Num Ticks:") for text in texts(page))
    for label in lastHud(page)["labels"]:
        if label["text"] not in keys:
            assert label["y"] + label["pixelSize"] <= PHONE[1] - band + 0.5, label["text"]

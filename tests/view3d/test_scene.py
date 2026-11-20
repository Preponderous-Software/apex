"""The 3D board (src/strata_view/scene.py). Built from graphik's 3D grid view,
which these skip without; only the last test renders, and it is skipped
wherever Strata can't load."""

from unittest.mock import MagicMock

import pytest

pytest.importorskip("preponderous.graphik.grid3d")

from entity.chicken import Chicken  # noqa: E402
from entity.grass import Grass  # noqa: E402
from screen.screenType import ScreenType  # noqa: E402
from strata_view import scene  # noqa: E402
from strata_view.app import StrataApex  # noqa: E402


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


@pytest.fixture
def app():
    app = StrataApex(usageReporting=MagicMock(), clock=Clock())
    app.goTo(ScreenType.SETUP_SCREEN)
    app.config.gridSize = 20
    app.goTo(ScreenType.SIMULATION_SCREEN)
    return app


def test_neighbouring_tiles_of_one_colour_share_a_box():
    green, soil = (0, 200, 0), (170, 120, 0)
    colors = {(0, 0): green, (1, 0): green, (2, 0): soil, (0, 1): green}
    shapes = scene.groundShapes(colors, 3, 2, soil)
    assert len(shapes) == 3
    widest = max(shapes, key=lambda s: s.scale[0])
    assert widest.scale[0] == pytest.approx(2 - scene.TILE_GAP)
    soilTile = [s for s in shapes if s.color[:3] == scene.rgb255(soil)][0]
    assert soilTile.scale[1] < widest.scale[1]  # grass stands proud of bare soil


def test_a_64_by_64_board_stays_far_under_one_shape_per_location(app):
    app.config.gridSize = 64
    app.goTo(ScreenType.SIMULATION_SCREEN)
    built = app.buildScene()
    # tiles and the frame are the shapes below the tiles' top face
    ground = [s for s in built.shapes if s.position[1] < 0]
    assert 4 < len(ground) < 64 * 64


def test_every_tile_picks_back_to_itself(app):
    camera = scene.cameraFor(20, 20, 1280, 720)
    for column in range(20):
        for row in range(20):
            x, z = scene.cellCenter(column, row, 20, 20)
            at = scene.projectToScreen(camera, (x, 0.0, z), 1280, 720)
            assert scene.screenToCell(camera, at, 1280, 720, 20, 20) == (column, row)
    assert scene.screenToCell(camera, (640, 0), 1280, 720, 20, 20) is None


def test_a_click_on_a_tile_shows_its_contents_and_selects_its_animal(app):
    screen = app.simulationScreen
    chicken = Chicken("clicked")
    grid = screen.simulation.environment.getGrid()
    location = grid.getLocationByCoordinates(5, 7)
    location.addEntity(chicken)
    screen.simulation.addEntityToTrackedEntities(chicken)
    camera = scene.cameraFor(20, 20, app.width, app.height)
    at = scene.cellScreenPosition(camera, 5, 7, 20, 20, app.width, app.height)
    assert app.selectAt(at) is location
    assert screen.getSelectedEntity() is chicken
    app.advance()
    labels, _ = app.hud()
    assert any(label.text == "Location (5, 7)" for label in labels)
    assert any(label.text == "clicked: 1" for label in labels)


def test_local_view_shows_the_square_around_the_selected_entity(app):
    screen = app.simulationScreen
    entity = screen.simulation.entities[screen.simulation.livingEntityIds[0]]
    screen.setSelectedEntity(entity)
    app.config.localView = True
    app.config.localViewSize = 3
    _, columns, rows = scene.boardShapes(screen, app.config)
    assert (columns, rows) == (7, 7)


def test_the_oldest_entity_is_highlighted_in_the_2d_colour(app):
    screen = app.simulationScreen
    app.config.highlightOldestEntity = True
    oldest = screen.simulation.entities[screen.simulation.livingEntityIds[0]]
    location = screen.simulation.environment.getGrid().getLocation(oldest.getLocationID())
    location.removeEntity(oldest)
    location.addEntity(oldest)  # on top, as the 2D window colours a location by its top entity
    shapes, _, _ = scene.boardShapes(screen, app.config)
    assert any(s.color[:3] == scene.rgb255(app.config.highlightColor) for s in shapes)


def test_eyes_follow_the_e_key(app):
    screen = app.simulationScreen
    eyes = lambda: len([s for s in scene.boardShapes(screen, app.config)[0] if s.color[:3] == scene.EYE_WHITE])
    assert eyes() == 2 * sum(
        1 for location in screen.simulation.environment.getGrid().getLocations().values()
        if location.getNumEntities() and screen.locationContainsLivingEntity(location)
    )
    app.config.eyesEnabled = False
    assert eyes() == 0


def test_the_hud_shows_the_statistics_caption_pause_and_version(app):
    screen = app.simulationScreen
    labels, _ = app.hud()
    texts = [label.text for label in labels]
    assert any(text.startswith("Apex - Simulation - 20x20") for text in texts)
    assert not any(text == "PAUSED" for text in texts)
    screen.handleKeyDownEvent(__import__("pygame").K_d)
    screen.handleKeyDownEvent(__import__("pygame").K_SPACE)
    texts = [label.text for label in app.hud()[0]]
    for stat in ("Num Ticks:", "Living Entities:", "Grass:", "Rabbits:"):
        assert stat in texts
    assert "PAUSED" in texts


def test_no_board_once_every_living_entity_is_gone(app):
    simulation = app.simulationScreen.simulation
    for entityId in list(simulation.livingEntityIds):
        simulation.removeEntity(simulation.entities[entityId])
    assert app.buildScene().shapes == []


def test_every_screen_renders_headless(tmp_path):
    try:
        from strata_view.renderer import StrataRenderer

        renderer = StrataRenderer(640, 360, window=False)
    except Exception as reason:  # no strata-engine, no library, no EGL
        pytest.skip("Strata can't render here: %s" % reason)
    try:
        app = StrataApex(renderer=renderer, usageReporting=MagicMock(), clock=Clock())
        for step, target in enumerate((None, ScreenType.SETUP_SCREEN, ScreenType.SIMULATION_SCREEN)):
            if target is not None:
                app.goTo(target)
            app.renderFrame(present=False)
            path = tmp_path / ("screen-%d.png" % step)
            renderer.savePng(str(path))
            assert path.stat().st_size > 1000
    finally:
        renderer.close()

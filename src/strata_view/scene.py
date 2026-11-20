"""A running Apex simulation as a 3D scene, as plain data.

buildSimulationScene() reads the simulation screen's state and returns a
graphik grid3d Scene: the grid as tiles, each location's top entity standing
on it, and the HUD. overlayFrom() turns what a 2D screen drew (ui.py) into
screen labels and panels. Nothing here imports Strata, so it is tested
without a GPU; renderer.py draws a Scene.

World axes follow graphik's grid3d: x along the grid's columns, z along its
rows (row 0 is the far edge, away from a camera south of the board), y up.
One location is one world unit.

Apex's grids reach 64x64 locations, most of them grass. Strata's 0.7.0
primitives aren't meshes (its 256-mesh limit doesn't apply to them), but one
shape per tile would be thousands per frame, so neighbouring tiles of the
same colour in a row are merged into one stretched box (groundShapes).
"""

import math

from entity.berries import Berries
from entity.berryBush import BerryBush
from entity.chicken import Chicken
from entity.cow import Cow
from entity.excrement import Excrement
from entity.fox import Fox
from entity.grass import Grass
from entity.livingEntity import LivingEntity
from entity.pig import Pig
from entity.rabbit import Rabbit
from entity.rock import Rock
from entity.water import Water
from entity.wolf import Wolf
from preponderous.graphik.grid3d import (
    CAPSULE,
    CUBE,
    CYLINDER,
    SPHERE,
    Camera,
    Label,
    Panel,
    Scene,
    Shape,
    cellCenter,
    fitCamera,
    rgb255,
    rgba,
    shade,
)
from strata_view.ui import UiButton, UiRect, UiText

TILE_HEIGHT = 0.2
GROUND_HEIGHT = 0.06  # grass and water sit this far above the soil
TILE_GAP = 0.04
FRAME_COLOR = (0.30, 0.20, 0.12)
FRAME_WIDTH = 0.35
EYE_WHITE = (0.97, 0.97, 0.95)
PUPIL = (0.04, 0.04, 0.05)
CLEAR_COLOR = (0.0, 0.0, 0.0, 1.0)  # the 2D window's black

# Strata's built-in font is monospaced: a character is about one pixel size
# wide. A pygame font size is about twice the width of one of its characters.
FONT_SCALE = 0.5
MIN_PIXEL_SIZE = 10

# How each kind of top entity stands on its tile: (shape, footprint, height).
# Grass and water are the ground itself (groundColor).
LIVING_SHAPES = {
    Chicken: (SPHERE, 0.5, 0.5),
    Rabbit: (SPHERE, 0.5, 0.45),
    Pig: (SPHERE, 0.75, 0.6),
    Cow: (CUBE, 0.8, 0.75),
    Wolf: (CAPSULE, 0.6, 0.9),
    Fox: (CAPSULE, 0.5, 0.75),
}
THING_SHAPES = {
    Rock: (CUBE, 0.85, 0.55),
    Excrement: (SPHERE, 0.35, 0.22),
    Berries: (SPHERE, 0.36, 0.36),
    BerryBush: (SPHERE, 0.85, 0.7),
}
DEFAULT_SHAPE = (CYLINDER, 0.6, 0.5)


def pixelSize(fontSize):
    return max(MIN_PIXEL_SIZE, fontSize * FONT_SCALE)


def textWidth(text, size):
    return len(text) * size


def centredLabel(text, x, y, size, color=(0.97, 0.96, 0.92, 1.0)):
    """A Label centred on (x, y), as graphik centres text."""
    return Label(text, x - textWidth(text, size) / 2.0, y - size * 0.45, size, color)


def overlayFrom(items, recolorBlack=None):
    """Labels and panels for what a 2D screen drew. `recolorBlack` replaces
    black text (drawn over the 2D window's brown board) with a colour that
    reads over the 3D scene."""
    labels, panels = [], []
    for item in items:
        if isinstance(item, UiText):
            color = rgb255(item.color)
            if recolorBlack is not None and item.color == (0, 0, 0):
                color = recolorBlack
            labels.append(centredLabel(item.text, item.x, item.y, pixelSize(item.size), rgba(color)))
        elif isinstance(item, UiRect):
            panels.append(Panel(item.x, item.y, item.width, item.height, rgba(rgb255(item.color), 0.92)))
        elif isinstance(item, UiButton):
            panels.append(Panel(item.x, item.y, item.width, item.height, rgba(rgb255(item.color))))
            labels.append(
                centredLabel(item.text, item.x + item.width / 2.0, item.y + item.height / 2.0,
                             pixelSize(item.textSize), rgba(rgb255(item.textColor)))
            )
    return labels, panels


def menuScene(items):
    """A menu, setup or results screen: only screen text and buttons."""
    labels, panels = overlayFrom(items)
    return Scene(labels=labels, panels=panels, clearColor=CLEAR_COLOR)


# -- the board ---------------------------------------------------------------

def topEntity(location):
    entities = location.getEntities()
    return entities[list(entities.keys())[-1]]


# Grass comes in 40 shades of green (entity/grass.py); its tiles are drawn in
# a few bands of them, so neighbouring tiles can share a box (groundShapes).
GRASS_BANDS = 4


def bandedGrass(color):
    low, high = 130, 169
    step = (high - low) / float(GRASS_BANDS - 1)
    band = round((min(max(color[1], low), high) - low) / step)
    return (color[0], int(round(low + band * step)), color[2])


def groundColor(location, config):
    """The colour of a location's tile: its water or grass, else bare soil."""
    color = None
    for entityId in location.getEntities():
        entity = location.getEntity(entityId)
        if type(entity) is Water:
            return entity.getColor()
        if type(entity) is Grass and color is None:
            color = bandedGrass(entity.getColor())
    return color if color is not None else config.brown


def viewCells(screen, config):
    """(location or -1, column, row) for every cell on show, with the board's
    size: the whole grid, or in local view (V) the square around the selected
    entity, localViewSize locations each way, as the 2D window shows it."""
    grid = screen.simulation.environment.getGrid()
    selected = screen.getSelectedEntity()
    if config.localView and selected is not None:
        n = int(config.localViewSize)
        centre = grid.getLocation(selected.getLocationID())
        cells = []
        for dy in range(-n, n + 1):
            for dx in range(-n, n + 1):
                location = grid.getLocationByCoordinates(centre.getX() + dx, centre.getY() + dy)
                cells.append((location, dx + n, dy + n))
        return cells, 2 * n + 1, 2 * n + 1
    cells = []
    for locationId in grid.getLocations():
        location = grid.getLocation(locationId)
        cells.append((location, location.getX(), location.getY()))
    return cells, grid.getColumns(), grid.getRows()


def groundShapes(colors, columns, rows, soil=None):
    """Tiles for a {(column, row): (r, g, b) 0-255} map, a row's neighbouring
    tiles of one colour merged into one box; `soil` tiles sit lower. Cells missing from the map (off
    the grid in local view) are left empty, as the 2D window leaves them black."""
    shapes = []
    for row in range(rows):
        column = 0
        while column < columns:
            color = colors.get((column, row))
            if color is None:
                column += 1
                continue
            end = column
            while end + 1 < columns and colors.get((end + 1, row)) == color:
                end += 1
            first, _ = cellCenter(column, row, columns, rows)
            last, z = cellCenter(end, row, columns, rows)
            # grass and water stand a little proud of bare soil
            height = TILE_HEIGHT + (0.0 if color == soil else GROUND_HEIGHT)
            shapes.append(
                Shape(CUBE, ((first + last) / 2.0, -TILE_HEIGHT + height / 2.0, z),
                      (end - column + 1 - TILE_GAP, height, 1.0 - TILE_GAP), rgba(rgb255(color)))
            )
            column = end + 1
    return shapes


def frameShapes(columns, rows):
    halfW, halfD = columns / 2.0, rows / 2.0
    rim, height = FRAME_WIDTH, TILE_HEIGHT + 0.12
    y = -TILE_HEIGHT + height / 2.0
    color = rgba(FRAME_COLOR)
    wide = columns + 2 * rim
    return [
        Shape(CUBE, (0.0, y, -halfD - rim / 2), (wide, height, rim), color),
        Shape(CUBE, (0.0, y, halfD + rim / 2), (wide, height, rim), color),
        Shape(CUBE, (-halfW - rim / 2, y, 0.0), (rim, height, rows), color),
        Shape(CUBE, (halfW + rim / 2, y, 0.0), (rim, height, rows), color),
    ]


def eyeShapes(x, z, size, height):
    """Two eyes with pupils on the side facing the camera, as the 2D window
    draws two on each living entity's square."""
    shapes = []
    front = z + size / 2.0
    eyeY = height * 0.7
    for side in (-1, 1):
        ex = x + side * size * 0.2
        shapes.append(Shape(SPHERE, (ex, eyeY, front - 0.02), (0.17, 0.17, 0.1), rgba(EYE_WHITE)))
        shapes.append(Shape(SPHERE, (ex, eyeY, front + 0.03), (0.08, 0.08, 0.05), rgba(PUPIL)))
    return shapes


def entityShapes(location, x, z, color, eyes):
    """The shape for a location's top entity (in the colour the 2D window
    gives the location), or none when the top entity is ground."""
    entity = topEntity(location)
    kind = type(entity)
    if kind in (Grass, Water):
        return []
    living = isinstance(entity, LivingEntity)
    kind, size, height = (LIVING_SHAPES if living else THING_SHAPES).get(kind, DEFAULT_SHAPE)
    base = GROUND_HEIGHT
    shapes = [Shape(kind, (x, base + height / 2.0, z), (size, height, size), rgba(rgb255(color)))]
    if living and eyes:
        shapes += eyeShapes(x, z, size, base + height)
    return shapes


def boardShapes(screen, config):
    """The tiles, frame and entities of what is on show, and the board's size."""
    cells, columns, rows = viewCells(screen, config)
    colors, things = {}, []
    for location, column, row in cells:
        if location == -1:
            continue
        colors[(column, row)] = groundColor(location, config)
        if location.getNumEntities() == 0:
            continue
        x, z = cellCenter(column, row, columns, rows)
        eyes = config.eyesEnabled and screen.locationContainsLivingEntity(location)
        things += entityShapes(location, x, z, screen.getColorOfLocation(location), eyes)
    return groundShapes(colors, columns, rows, config.brown) + frameShapes(columns, rows) + things, columns, rows


def cameraFor(columns, rows, width, height):
    return fitCamera(columns, rows, width / float(height))


# -- screen <-> board ----------------------------------------------------------

def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _unit(a):
    length = math.sqrt(_dot(a, a))
    return (a[0] / length, a[1] / length, a[2] / length)


def _basis(camera):
    forward = _unit(_sub(camera.target, camera.eye))
    right = _unit(_cross(forward, (0.0, 1.0, 0.0)))
    return forward, right, _cross(right, forward)


def projectToScreen(camera, point, width, height):
    """Where a world point lands in the window (pixels from the top-left), or
    None behind the camera: the look-at and perspective graphik asks Strata
    for (Strata 0.7.0 has no projection call of its own)."""
    forward, right, up = _basis(camera)
    offset = _sub(point, camera.eye)
    depth = _dot(offset, forward)
    if depth <= 0:
        return None
    focal = 1.0 / math.tan(math.radians(camera.fovDegrees) / 2.0)
    aspect = width / float(height)
    ndcX = focal / aspect * _dot(offset, right) / depth
    ndcY = focal * _dot(offset, up) / depth
    return ((ndcX + 1.0) / 2.0 * width, (1.0 - ndcY) / 2.0 * height)


def screenToCell(camera, position, width, height, columns, rows):
    """The (column, row) of the tile under a window position, or None: the
    3D window's answer to the 2D window's pixel-to-location division."""
    forward, right, up = _basis(camera)
    focal = 1.0 / math.tan(math.radians(camera.fovDegrees) / 2.0)
    aspect = width / float(height)
    ndcX = position[0] / float(width) * 2.0 - 1.0
    ndcY = 1.0 - position[1] / float(height) * 2.0
    direction = tuple(
        forward[i] + right[i] * ndcX * aspect / focal + up[i] * ndcY / focal for i in range(3)
    )
    if direction[1] >= 0:
        return None  # looking above the horizon
    t = (0.0 - camera.eye[1]) / direction[1]
    x = camera.eye[0] + direction[0] * t
    z = camera.eye[2] + direction[2] * t
    column = int(math.floor(x + columns / 2.0))
    row = int(math.floor(z + rows / 2.0))
    if 0 <= column < columns and 0 <= row < rows:
        return column, row
    return None


def cellScreenPosition(camera, column, row, columns, rows, width, height):
    x, z = cellCenter(column, row, columns, rows)
    return projectToScreen(camera, (x, 0.5, z), width, height)


def buildSimulationScene(screen, config, width, height, labels=(), panels=()):
    """Everything to draw for the simulation screen: the board (unless every
    living entity is gone, when the 2D window shows an empty screen too) and
    the HUD labels and panels the caller made."""
    scene = Scene(labels=list(labels), panels=list(panels), clearColor=CLEAR_COLOR)
    if screen.simulation.getNumLivingEntities() == 0:
        return scene
    shapes, columns, rows = boardShapes(screen, config)
    scene.shapes = shapes
    scene.camera = cameraFor(columns, rows, width, height)
    return scene

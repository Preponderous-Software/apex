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
same colour in a row are merged into one stretched box (grid3d's
GridBoard mergeTiles). The board, its tiles, the local view's window
(a grid3d Viewport), picking and the screen text and buttons are all
graphik's grid3d; this module only says what Apex's board looks like.
"""

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
# cellCenter and projectToScreen are re-exported for the tools and tests.
from preponderous.graphik.grid3d import (
    CAPSULE,
    CUBE,
    CYLINDER,
    SPHERE,
    Button,
    GridBoard,
    Panel,
    Piece,
    PieceStyle,
    Scene,
    Shape,
    Theme,
    Tile,
    Viewport,
    cellCenter,
    fitCamera,
    measureText,
    pickCell,
    projectToScreen,
    rgb255,
    rgba,
)
from preponderous.graphik.grid3d import cellScreenPosition as _cellScreenPosition
from preponderous.graphik.grid3d import centredLabel as _centredLabel
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


# Labels sit where the ink of Strata's glyphs looks centred on their point.
LABEL_RISE = 0.45


def textWidth(text, size):
    return measureText(text, size)


def centredLabel(text, x, y, size, color=(0.97, 0.96, 0.92, 1.0)):
    """A Label centred on (x, y), as graphik centres text."""
    return _centredLabel(text, x, y, size, color, rise=LABEL_RISE)


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
            panel, label = Button(item.x, item.y, item.width, item.height, item.text, item.color,
                                  item.textColor, pixelSize(item.textSize), rise=LABEL_RISE).draw()
            panels.append(panel)
            labels.append(label)
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
    # read straight from the location's map (a 64x64 grid holds tens of thousands of entities)
    for entity in location.getEntities().values():
        kind = type(entity)
        if kind is Water:
            return entity.getColor()
        if kind is Grass and color is None:
            color = bandedGrass(entity.getColor())
    return color if color is not None else config.brown


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


def _eyes(size, height):
    """A PieceStyle extras drawing eyeShapes on a piece `size` across and
    `height` tall (relative to the piece, as grid3d asks)."""
    return lambda piece, x, z, baseY: eyeShapes(x, z, size, baseY + height)


def _styles():
    """One PieceStyle per kind of top entity, standing on the ground (grass
    and water height), and an eyed one for each living kind."""
    styles = {}
    for kinds, living in ((LIVING_SHAPES, True), (THING_SHAPES, False)):
        for kind, (shape, size, height) in kinds.items():
            styles[kind.__name__] = PieceStyle(shape, size=size, height=height, lift=GROUND_HEIGHT)
            if living:
                styles[kind.__name__ + "+eyes"] = PieceStyle(
                    shape, size=size, height=height, lift=GROUND_HEIGHT, extras=_eyes(size, height))
    shape, size, height = DEFAULT_SHAPE
    styles["other"] = PieceStyle(shape, size=size, height=height, lift=GROUND_HEIGHT)
    styles["other+eyes"] = PieceStyle(shape, size=size, height=height, lift=GROUND_HEIGHT,
                                      extras=_eyes(size, height))
    styles[SELECTED_STYLE] = PieceStyle(CUBE, color=SELECTED_COLOR, size=0.98, height=0.01,
                                        lift=GROUND_HEIGHT, extras=_selectedFrame)
    return styles


# A location clicked for its contents is framed while its alert is up, so the
# box beside the board says which tile it describes
SELECTED_STYLE = "selected"
SELECTED_COLOR = (1.0, 1.0, 1.0)
SELECTED_BAR = 0.1


def _selectedFrame(piece, x, z, baseY):
    """Four raised bars along a selected tile's edges (relative to the piece)."""
    reach, bar, height = 0.5 - SELECTED_BAR / 2, SELECTED_BAR, 0.3
    y = baseY + height / 2
    color = rgba(SELECTED_COLOR)
    return [
        Shape(CUBE, (x, y, z - reach), (1.0, height, bar), color),
        Shape(CUBE, (x, y, z + reach), (1.0, height, bar), color),
        Shape(CUBE, (x - reach, y, z), (bar, height, 1.0), color),
        Shape(CUBE, (x + reach, y, z), (bar, height, 1.0), color),
    ]


def selectedPieces(screen, board):
    """A frame on each location whose alert (a click's contents) is still up
    and on show."""
    pieces, seen = [], set()
    for alert in screen.getTextAlerts():
        cell = getattr(alert, "cell", None)
        if cell is None or cell in seen or not board.contains(*cell) or not board.visible(*cell):
            continue
        seen.add(cell)
        pieces.append(Piece((SELECTED_STYLE,) + tuple(cell), cell[0], cell[1], SELECTED_STYLE))
    return pieces


THEME = Theme(
    tileHeight=TILE_HEIGHT,
    tileGap=TILE_GAP,
    frame=FRAME_COLOR,
    frameWidth=FRAME_WIDTH,
    pieces=_styles(),
)


def groundTile(color, soil):
    """A tile for a 0-255 ground colour: grass and water stand a little proud
    of bare soil."""
    return Tile(rgb255(color), 0.0 if color == soil else GROUND_HEIGHT)


def groundShapes(colors, columns, rows, soil=None):
    """Tiles for a {(column, row): (r, g, b) 0-255} map, a row's neighbouring
    tiles of one colour merged into one box; `soil` tiles sit lower. Cells missing from the map (off
    the grid in local view) are left empty, as the 2D window leaves them black."""
    tiles = {(column, row): None for row in range(rows) for column in range(columns)}
    tiles.update({cell: groundTile(color, soil) for cell, color in colors.items()})
    theme = Theme(tileHeight=TILE_HEIGHT, tileGap=TILE_GAP, frame=None)
    return GridBoard(columns, rows, theme, tiles=tiles, mergeTiles=True).boardShapes()


def entityPiece(location, column, row, color, eyes):
    """The piece for a location's top entity (in the colour the 2D window
    gives the location), or None when the top entity is ground."""
    entity = topEntity(location)
    kind = type(entity)
    if kind in (Grass, Water):
        return None
    living = isinstance(entity, LivingEntity)
    style = kind.__name__ if kind in (LIVING_SHAPES if living else THING_SHAPES) else "other"
    if living and eyes:
        style += "+eyes"
    return Piece((column, row), column, row, style, color=rgb255(color))


def simulationBoard(screen, config):
    """The board on show and its pieces: the whole grid, or in local view (V)
    the square around the selected entity, localViewSize locations each way,
    as the 2D window shows it (a grid3d Viewport; cells past the grid's edge
    stay empty, as the 2D window leaves them black)."""
    grid = screen.simulation.environment.getGrid()
    selected = screen.getSelectedEntity()
    viewport = None
    if config.localView and selected is not None:
        n = int(config.localViewSize)
        centre = grid.getLocation(selected.getLocationID())
        viewport = Viewport.around(centre.getX(), centre.getY(), n)
        locations = []
        for dy in range(-n, n + 1):
            for dx in range(-n, n + 1):
                location = grid.getLocationByCoordinates(centre.getX() + dx, centre.getY() + dy)
                if location != -1:
                    locations.append(location)
    else:
        locations = [grid.getLocation(locationId) for locationId in grid.getLocations()]
    tiles, pieces = {}, []
    for location in locations:
        column, row = location.getX(), location.getY()
        tiles[(column, row)] = groundTile(groundColor(location, config), config.brown)
        if location.getNumEntities() == 0:
            continue
        eyes = config.eyesEnabled and screen.locationContainsLivingEntity(location)
        piece = entityPiece(location, column, row, screen.getColorOfLocation(location), eyes)
        if piece is not None:
            pieces.append(piece)
    board = GridBoard(grid.getColumns(), grid.getRows(), THEME, tiles=tiles, mergeTiles=True,
                      viewport=viewport)
    return board, pieces + selectedPieces(screen, board)


def boardShapes(screen, config):
    """The tiles, frame and entities of what is on show, and the board's size."""
    board, pieces = simulationBoard(screen, config)
    columns, rows = board.shownSize()
    return board.boardShapes() + board.pieceShapes(pieces)[0], columns, rows


def cameraFor(columns, rows, width, height):
    return fitCamera(columns, rows, width / float(height))


# -- screen <-> board (grid3d's picking) ----------------------------------------

def screenToCell(camera, position, width, height, columns, rows):
    """The (column, row) of the tile under a window position, or None: the
    3D window's answer to the 2D window's pixel-to-location division."""
    return pickCell(camera, GridBoard(columns, rows), position[0], position[1], width, height)


def cellScreenPosition(camera, column, row, columns, rows, width, height):
    return _cellScreenPosition(camera, GridBoard(columns, rows), column, row, width, height, y=0.5)


def buildSimulationScene(screen, config, width, height, labels=(), panels=()):
    """Everything to draw for the simulation screen: the board (unless every
    living entity is gone, when the 2D window shows an empty screen too) and
    the HUD labels and panels the caller made."""
    if screen.simulation.getNumLivingEntities() == 0:
        return Scene(labels=list(labels), panels=list(panels), clearColor=CLEAR_COLOR)
    board, pieces = simulationBoard(screen, config)
    return board.scene(pieces, labels=labels, panels=panels, aspect=width / float(height),
                       clearColor=CLEAR_COLOR)

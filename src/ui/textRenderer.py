from entity.berries import Berries
from entity.berryBush import BerryBush
from entity.chicken import Chicken
from entity.cow import Cow
from entity.excrement import Excrement
from entity.fox import Fox
from entity.grass import Grass
from entity.pig import Pig
from entity.rabbit import Rabbit
from entity.rock import Rock
from entity.water import Water
from entity.wolf import Wolf

# What the text UI draws for each entity type: a glyph and a colour name (a curses COLOR_* suffix,
# or None for the terminal's default). Every entity type in src/entity has one, so nothing on the
# grid is drawn as UNKNOWN_GLYPH; the letters of the living entities match their spawn keys where
# they can (k is the cow, as c is the chicken; R is the rabbit, spawned with b).
GLYPHS = {
    Chicken: ("C", "WHITE"),
    Pig: ("P", "MAGENTA"),
    Cow: ("K", "YELLOW"),
    Wolf: ("W", "RED"),
    Fox: ("F", "RED"),
    Rabbit: ("R", "CYAN"),
    Grass: ('"', "GREEN"),
    BerryBush: ("&", "GREEN"),
    Berries: ("*", "MAGENTA"),
    Water: ("~", "BLUE"),
    Rock: ("#", None),
    Excrement: ("x", "YELLOW"),
}
EMPTY_GLYPH = (".", None)
UNKNOWN_GLYPH = ("?", None)

LEGEND = [
    "C chicken  P pig  K cow  W wolf  F fox  R rabbit",
    '" grass  & berry bush  * berries  ~ water  # rock  x excrement  . bare ground',
]
CONTROLS = "space/esc pause  c p k w f b spawn  [ ] speed  l limit  r restart  q quit"


def glyphFor(entity):
    return GLYPHS.get(type(entity), UNKNOWN_GLYPH)


# The entity a location is drawn as: the last one added, as on the pygame screen.
def topEntity(location):
    entities = location.getEntities()
    if len(entities) == 0:
        return None
    return next(reversed(entities.values()))


# The grid as rows of (glyph, colour) cells, row y and column x being the location at (x, y).
# One pass over the grid's locations, each placed by its own coordinates, so a frame costs
# O(locations + entities) rather than a coordinate lookup per cell.
def renderCells(grid):
    columns = grid.getColumns()
    rows = grid.getRows()
    cells = [[EMPTY_GLYPH] * columns for _ in range(rows)]
    for location in grid.getLocations().values():
        entity = topEntity(location)
        if entity is not None:
            cells[location.getY()][location.getX()] = glyphFor(entity)
    return cells


# The grid as plain text, one string per row, cells separated by a space so the grid is about as
# wide as it is tall in a terminal.
def renderRows(grid):
    return [" ".join(glyph for glyph, _ in row) for row in renderCells(grid)]


def statusLines(simulation, controller):
    config = controller.config
    state = "PAUSED" if controller.isPaused() else "running"
    speed = str(config.tickSpeed) + "/" + str(config.maxTickSpeed) if config.limitTickSpeed else "unlimited"
    counts = {}
    for entityId in simulation.livingEntityIds:
        entityType = type(simulation.entities[entityId])
        counts[entityType] = counts.get(entityType, 0) + 1
    living = "  ".join(GLYPHS[entityType][0] + ":" + str(counts.get(entityType, 0)) for entityType in (Chicken, Pig, Cow, Wolf, Fox, Rabbit))
    return [
        "Tick " + str(simulation.numTicks) + "  " + state + "  speed " + speed
        + "  living " + str(simulation.getNumLivingEntities()) + "  entities " + str(simulation.getNumEntities()),
        living + "  excrement:" + str(simulation.getNumExcrement()),
    ]


# A stand-in for sys.stdout while the text UI owns the terminal. The simulation reports events
# with print(), which arrives here in fragments (print writes its text and its newline
# separately); only complete lines are kept, so the UI always shows a whole message.
class EventLog:
    def __init__(self, maxLines=50):
        self.__partial = ""
        self.__lines = []
        self.__maxLines = maxLines

    def write(self, text):
        self.__partial += text
        while "\n" in self.__partial:
            line, self.__partial = self.__partial.split("\n", 1)
            line = line.strip()
            if line != "":
                self.__lines.append(line)
        del self.__lines[:-self.__maxLines]
        return len(text)

    def flush(self):
        pass

    def clear(self):
        self.__partial = ""
        self.__lines = []

    def getLines(self):
        return list(self.__lines)

    def getLatest(self):
        return self.__lines[-1] if self.__lines else ""

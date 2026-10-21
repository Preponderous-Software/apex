import contextlib
import curses
import io
import os
import sys
import time

from simulation.config import Config
from simulation.simulation import Simulation
from simulation.simulationController import SimulationController
from ui.textRenderer import CONTROLS, GLYPHS, LEGEND, EventLog, renderCells, statusLines


# What Simulation asks of its game display: only the size, used to scale locations for drawing,
# which the text UI does not need. One unit per location keeps the arithmetic meaningful.
class TextDisplay:
    def __init__(self, gridSize):
        self.__gridSize = gridSize

    def get_size(self):
        return (self.__gridSize, self.__gridSize)


# Runs Apex in a terminal instead of a pygame window (apex.py --text): the grid drawn as one
# character per location, a status panel, the latest simulation event and the controls, with
# keys read without blocking so the simulation keeps ticking. The gameplay itself goes through
# SimulationController.
#
# @author Daniel McCoy Stephenson
# @since October 18th, 2026
class TextSimulationRunner:
    # the screen is redrawn at most this often (seconds), however fast the simulation ticks
    FRAME_INTERVAL = 0.05
    ESCAPE = 27

    def __init__(self, config=None, onSimulationStarted=None, cursesModule=curses, clock=time.monotonic):
        self.config = config if config is not None else Config()
        self.config.muted = True  # sound needs the pygame mixer, which the text UI never starts
        self.simulation = None
        self.controller = None
        self.eventLog = EventLog()
        self.quitRequested = False
        self.__onSimulationStarted = onSimulationStarted
        self.__curses = cursesModule
        self.__clock = clock
        self.__colorAttributes = {}
        self.__cleanedUp = True
        self.__summary = ""  # the environment summary of the latest simulation to end
        self.__ended = False

    # public methods ---------------------------------------------------------
    def run(self):
        # curses waits a full second by default to tell a lone Escape from the start of an
        # escape sequence; Escape pauses here, so shorten that unless the user chose a value
        os.environ.setdefault("ESCDELAY", "25")
        try:
            self.__curses.wrapper(self.runInScreen)
        finally:
            # printed after curses has given the terminal back, so the summary stays readable
            self.__cleanup()
            sys.stdout.write(self.__summary)

    def runInScreen(self, stdscr):
        self.stdscr = stdscr
        self.initializeColors()
        try:
            self.__curses.curs_set(0)
        except self.__curses.error:
            pass  # some terminals cannot hide the cursor; that is cosmetic
        originalStdout = sys.stdout
        sys.stdout = self.eventLog  # the simulation's print() calls would scroll the screen
        try:
            self.newSimulation()
            self.__loop()
        finally:
            sys.stdout = originalStdout

    def initializeColors(self):
        self.__colorAttributes = {}
        c = self.__curses
        try:
            if not c.has_colors():
                return
            c.start_color()
            try:
                c.use_default_colors()
                background = -1
            except c.error:
                background = c.COLOR_BLACK
            names = sorted({color for _, color in GLYPHS.values() if color is not None})
            for pairNumber, name in enumerate(names, start=1):
                if pairNumber >= c.COLOR_PAIRS:
                    break
                c.init_pair(pairNumber, getattr(c, "COLOR_" + name), background)
                self.__colorAttributes[name] = c.color_pair(pairNumber)
        except c.error:
            # a terminal that claims colour but refuses it is drawn in monochrome
            self.__colorAttributes = {}

    def isMonochrome(self):
        return len(self.__colorAttributes) == 0

    def attributeFor(self, glyph, color):
        attribute = self.__colorAttributes.get(color, 0)
        if glyph.isalpha() and glyph.isupper():
            attribute |= self.__curses.A_BOLD  # living entities stand out in monochrome too
        return attribute

    def newSimulation(self):
        self.__cleanup()
        if self.simulation is not None and self.config.randomizeGridSizeUponRestart:
            self.config.randomizeGridSize()
            self.config.randomizeGrassGrowTime()
        self.config.calculateValues()
        self.simulation = Simulation("Simulation", self.config, TextDisplay(self.config.gridSize))
        self.simulation.generateInitialEntities()
        self.simulation.placeInitialEntitiesInEnvironment()
        self.controller = SimulationController(self.simulation, self.config)
        self.eventLog.clear()  # setup warnings (no sound in a terminal) are not events
        self.__cleanedUp = False
        self.__ended = False
        if self.__onSimulationStarted is not None:
            self.__onSimulationStarted()

    def handleKey(self, key):
        if key == ord("q"):
            self.quitRequested = True
            self.controller.end()
        elif key == ord("r"):
            self.controller.end()
            self.newSimulation()
        elif key == ord(" ") or key == self.ESCAPE:
            self.controller.togglePause()
        elif key == ord("]"):
            self.controller.increaseTickSpeed()
        elif key == ord("["):
            self.controller.decreaseTickSpeed()
        elif key == ord("l"):
            self.controller.toggleTickSpeedLimit()
        elif 0 <= key < 256 and chr(key) in SimulationController.SPAWNABLE and not self.__ended:
            self.controller.spawn(chr(key))

    def isEnded(self):
        return self.__ended

    # Advances one tick and ends the simulation once every living entity is gone.
    def step(self):
        ticked = self.controller.update()
        if ticked and self.controller.shouldEnd():
            self.controller.end()
            self.__ended = True
            self.__cleanup()
        return ticked

    def draw(self):
        c = self.__curses
        screen = self.stdscr
        screen.erase()  # every frame is drawn from blank, so nothing from the last one lingers
        height, width = screen.getmaxyx()
        cells = renderCells(self.simulation.environment.getGrid())
        gridRows = min(len(cells), max(height - 7, 0))
        gridColumns = min(len(cells[0]) if cells else 0, max(width // 2, 0))
        for y in range(gridRows):
            for x in range(gridColumns):
                glyph, color = cells[y][x]
                self.__put(y, x * 2, glyph, self.attributeFor(glyph, color), height, width)
        row = gridRows + 1
        lines = statusLines(self.simulation, self.controller)
        if gridRows < len(cells) or gridColumns < (len(cells[0]) if cells else 0):
            lines[0] += "  (grid clipped: enlarge the terminal)"
        if self.__ended:
            lines.append("Simulation over after " + str(self.simulation.numTicks) + " ticks: r for a new one, q to quit")
        else:
            lines.append("Event: " + self.eventLog.getLatest())
        lines += LEGEND + [CONTROLS]
        for line in lines:
            self.__put(row, 0, line, 0, height, width)
            row += 1
        screen.refresh()

    # private methods --------------------------------------------------------
    def __loop(self):
        screen = self.stdscr
        nextTick = self.__clock()
        lastDraw = None
        while not self.quitRequested:
            now = self.__clock()
            # wait for a key until the next tick is due, but never longer than a frame
            if self.controller.isPaused() or self.__ended:
                waitMs = int(self.FRAME_INTERVAL * 1000)
            else:
                waitMs = int(min(max(nextTick - now, 0), self.FRAME_INTERVAL) * 1000)
            screen.timeout(waitMs)
            key = screen.getch()
            dirty = False
            while key != -1:
                if key != self.__curses.KEY_RESIZE:
                    self.handleKey(key)
                dirty = True
                if self.quitRequested:
                    return
                screen.timeout(0)
                key = screen.getch()
            now = self.__clock()
            if not self.__ended and now >= nextTick and self.step():
                nextTick = now + self.controller.getTickDelay()
                dirty = True
            if lastDraw is None or (dirty and now - lastDraw >= self.FRAME_INTERVAL) or now - lastDraw >= 1:
                self.draw()
                lastDraw = now

    # Writes text at (y, x), cut to the screen: curses raises for anything past the edge, and for
    # the bottom-right cell itself.
    def __put(self, y, x, text, attribute, height, width):
        if y >= height or x >= width:
            return
        text = text[: max(width - x - (1 if y == height - 1 else 0), 0)]
        if text == "":
            return
        try:
            self.stdscr.addstr(y, x, text, attribute)
        except self.__curses.error:
            pass

    def __cleanup(self):
        if self.simulation is not None and not self.__cleanedUp:
            self.__cleanedUp = True
            # kept rather than printed: a simulation that ends while the UI owns the terminal
            # would otherwise print its summary into the event log, where nobody sees it
            summary = io.StringIO()
            with contextlib.redirect_stdout(summary):
                self.simulation.cleanup()
            self.__summary = summary.getvalue()

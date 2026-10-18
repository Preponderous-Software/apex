import sys
from unittest.mock import MagicMock

import pytest

from entity.chicken import Chicken
from simulation.config import Config
from textSimulationRunner import TextDisplay, TextSimulationRunner


# fakes ----------------------------------------------------------------------
class FakeCursesError(Exception):
    pass

class FakeCurses:
    """Stands in for the curses module, behaving like it where the review findings live: a colour
    pair used before start_color() raises, as it does on a real terminal."""
    error = FakeCursesError
    A_BOLD = 1 << 16
    KEY_RESIZE = 410
    COLOR_PAIRS = 64
    COLOR_BLACK, COLOR_RED, COLOR_GREEN, COLOR_YELLOW = 0, 1, 2, 3
    COLOR_BLUE, COLOR_MAGENTA, COLOR_CYAN, COLOR_WHITE = 4, 5, 6, 7

    def __init__(self, hasColors=True, startColorFails=False):
        self.hasColors = hasColors
        self.startColorFails = startColorFails
        self.started = False
        self.colorPairCalls = 0

    def has_colors(self):
        return self.hasColors

    def start_color(self):
        if self.startColorFails:
            raise FakeCursesError("start_color() failed")
        self.started = True

    def use_default_colors(self):
        pass

    def init_pair(self, number, foreground, background):
        if not self.started:
            raise FakeCursesError("must call start_color() first")

    def color_pair(self, number):
        if not self.started:
            raise FakeCursesError("must call start_color() first")
        self.colorPairCalls += 1
        return number << 8

    def curs_set(self, visibility):
        raise FakeCursesError("cursor visibility not supported")

    def wrapper(self, function):
        return function(FakeScreen())

class FakeScreen:
    """A character buffer with curses' edge rules: writing past the right edge, or into the
    bottom-right cell, raises."""
    def __init__(self, height=40, width=80, keys=()):
        self.height = height
        self.width = width
        self.keys = list(keys)
        self.erase()

    def erase(self):
        self.buffer = [[" "] * self.width for _ in range(self.height)]
        self.attributes = {}

    def getmaxyx(self):
        return (self.height, self.width)

    def addstr(self, y, x, text, attribute=0):
        if y >= self.height or x + len(text) > self.width or (y == self.height - 1 and x + len(text) == self.width):
            raise FakeCursesError("addstr() returned ERR")
        for i, character in enumerate(text):
            self.buffer[y][x + i] = character
            self.attributes[(y, x + i)] = attribute

    def refresh(self):
        pass

    def timeout(self, milliseconds):
        pass

    def getch(self):
        return self.keys.pop(0) if self.keys else -1

    def line(self, y):
        return "".join(self.buffer[y]).rstrip()

    def text(self):
        return [self.line(y) for y in range(self.height)]

# helper methods -------------------------------------------------------------
def getTestConfig(gridSize=8):
    config = Config()
    config.gridSize = gridSize
    config.randomizeGridSizeUponRestart = False
    return config

def getTestRunner(fakeCurses=None, screen=None, **kwargs):
    runner = TextSimulationRunner(getTestConfig(), cursesModule=fakeCurses or FakeCurses(), **kwargs)
    runner.stdscr = screen or FakeScreen()
    runner.initializeColors()
    runner.newSimulation()
    return runner

def lineStartingWith(screen, prefix):
    return next(line for line in screen.text() if line.startswith(prefix))

# colour tests ---------------------------------------------------------------
def test_terminalWithoutColoursDrawsInMonochrome():
    fakeCurses = FakeCurses(hasColors=False)
    runner = getTestRunner(fakeCurses)

    runner.draw()  # would raise if a colour pair were used without start_color()

    assert runner.isMonochrome()
    assert fakeCurses.colorPairCalls == 0

def test_terminalRefusingColoursFallsBackToMonochrome():
    fakeCurses = FakeCurses(hasColors=True, startColorFails=True)
    runner = getTestRunner(fakeCurses)

    runner.draw()

    assert runner.isMonochrome()

def test_colourTerminalGetsColourPairs():
    runner = getTestRunner(FakeCurses(hasColors=True))

    assert not runner.isMonochrome()
    assert runner.attributeFor('"', "GREEN") != runner.attributeFor("~", "BLUE")

def test_livingEntitiesAreBoldEvenInMonochrome():
    runner = getTestRunner(FakeCurses(hasColors=False))

    assert runner.attributeFor("W", "RED") == FakeCurses.A_BOLD
    assert runner.attributeFor('"', "GREEN") == 0

# drawing tests --------------------------------------------------------------
def test_drawShowsTheGridStatusLegendAndControls():
    screen = FakeScreen()
    runner = getTestRunner(screen=screen)

    runner.draw()

    text = screen.text()
    assert len(text[0].split(" ")) == 8  # one glyph per column of the 8x8 grid
    assert lineStartingWith(screen, "Tick 0")
    assert lineStartingWith(screen, "C chicken")
    assert lineStartingWith(screen, "space/esc pause")
    assert all("?" not in line for line in text[:8])

def test_shorterTextLeavesNoStaleCharacters():
    screen = FakeScreen()
    runner = getTestRunner(screen=screen)
    print("A very long event message that fills much of the line", file=runner.eventLog)
    runner.draw()
    print("Fox has died.", file=runner.eventLog)

    runner.draw()

    assert lineStartingWith(screen, "Event:") == "Event: Fox has died."

def test_eventLineShowsTheWholeMessage():
    screen = FakeScreen(width=120)
    runner = getTestRunner(screen=screen)
    print("Pig has reproduced with Pig at (", 3, ",", 4, ").", file=runner.eventLog)

    runner.draw()

    assert lineStartingWith(screen, "Event:") == "Event: Pig has reproduced with Pig at ( 3 , 4 )."

def test_smallTerminalClipsInsteadOfCrashing():
    screen = FakeScreen(height=10, width=12)
    runner = getTestRunner(screen=screen)

    runner.draw()  # the fake raises, like curses, on any write past an edge

    assert screen.line(0) != ""

def test_clippedGridIsReported():
    screen = FakeScreen(height=12, width=200)
    runner = getTestRunner(screen=screen)

    runner.draw()

    assert "grid clipped" in lineStartingWith(screen, "Tick")

# key tests ------------------------------------------------------------------
def test_quitEndsTheSimulationSoNoFurtherTickRuns():
    runner = getTestRunner()

    runner.handleKey(ord("q"))

    assert runner.quitRequested
    assert runner.step() == False
    assert runner.simulation.numTicks == 0

@pytest.mark.parametrize("key", [ord(" "), TextSimulationRunner.ESCAPE])
def test_spaceAndEscapeTogglePause(key):
    runner = getTestRunner()

    runner.handleKey(key)
    assert runner.controller.isPaused()
    runner.handleKey(key)
    assert not runner.controller.isPaused()

def test_spawnKeyAddsALivingEntity():
    runner = getTestRunner()
    before = runner.simulation.getNumberOfLivingEntitiesOfType(Chicken)

    runner.handleKey(ord("c"))

    assert runner.simulation.getNumberOfLivingEntitiesOfType(Chicken) == before + 1

def test_speedKeys():
    runner = getTestRunner()
    speed = runner.config.tickSpeed

    runner.handleKey(ord("]"))
    assert runner.config.tickSpeed == speed + 1
    runner.handleKey(ord("["))
    assert runner.config.tickSpeed == speed
    runner.handleKey(ord("l"))
    assert runner.config.limitTickSpeed == False

def test_restartCleansUpAndStartsANewSimulation():
    started = MagicMock()
    runner = getTestRunner(onSimulationStarted=started)
    old = runner.simulation
    old.cleanup = MagicMock()

    runner.handleKey(ord("r"))

    old.cleanup.assert_called_once()
    assert old.running == False
    assert runner.simulation is not old
    assert started.call_count == 2

# ending tests ---------------------------------------------------------------
def test_simulationEndsOnceEveryLivingEntityIsGone():
    screen = FakeScreen()
    runner = getTestRunner(screen=screen)
    runner.simulation.cleanup = MagicMock()
    for entityId in list(runner.simulation.livingEntityIds):
        runner.simulation.removeEntity(runner.simulation.entities[entityId])

    runner.step()

    assert runner.isEnded()
    runner.simulation.cleanup.assert_called_once()
    runner.handleKey(ord("c"))  # spawning does not revive an ended simulation
    assert runner.simulation.getNumLivingEntities() == 0
    runner.draw()
    assert lineStartingWith(screen, "Simulation over")

# loop tests -----------------------------------------------------------------
def test_runInScreenTicksUntilQuitAndRestoresStdout():
    originalStdout = sys.stdout
    times = iter(range(1000))
    runner = TextSimulationRunner(getTestConfig(), cursesModule=FakeCurses(), clock=lambda: next(times))
    runner.config.limitTickSpeed = False
    screen = FakeScreen(keys=[-1, -1, -1, ord("q")])

    runner.runInScreen(screen)

    assert sys.stdout is originalStdout
    assert runner.quitRequested
    assert runner.simulation.numTicks == 3

def test_runInScreenRestoresStdoutWhenSomethingFails():
    originalStdout = sys.stdout
    runner = TextSimulationRunner(getTestConfig(), cursesModule=FakeCurses())
    runner.newSimulation = MagicMock(side_effect=RuntimeError("boom"))

    with pytest.raises(RuntimeError):
        runner.runInScreen(FakeScreen())

    assert sys.stdout is originalStdout

def test_runPrintsTheSummaryAfterTheTerminalIsGivenBack(capsys):
    runner = TextSimulationRunner(getTestConfig(), cursesModule=FakeCurses())
    runner.runInScreen = lambda screen: (runner.newSimulation(), runner.handleKey(ord("q")))

    runner.run()

    assert "Length of simulation" in capsys.readouterr().out

def test_textModeIsMuted():
    assert TextSimulationRunner(getTestConfig(), cursesModule=FakeCurses()).config.muted == True

def test_textDisplayReportsTheGridSize():
    assert TextDisplay(12).get_size() == (12, 12)

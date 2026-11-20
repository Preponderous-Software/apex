"""Apex in a 3D Strata window (desktop Linux and Windows).

StrataApex runs the same screens as the 2D window (src/apex.py), in the same
order, with a Strata window in place of pygame's. The menu, setup and results
screens are the 2D screen objects themselves: they draw into a
RecordingGraphik (ui.py), the 3D window shows what they drew as screen-space
panels and labels, and a click runs the 2D button's own function. The
simulation screen is the 2D SimulationScreen too: keys go to its key handler,
a click on a tile selects that location through it, and its statistics and
location alerts are drawn from what it records. Only the board is new: it is
drawn in 3D by scene.py.
"""

import time

import pygame

from screen.mainMenuScreen import MainMenuScreen
from screen.resultsScreen import ResultsScreen
from screen.screenType import ScreenType
from screen.setupScreen import SetupScreen
from screen.simulationScreen import SimulationScreen
from service.usageReportingService import UsageReportingService
from simulation.config import Config
from simulation.usdRecording import UsdRecording
from strata_view import StrataUnavailable
from strata_view.hud import simulationHud
from strata_view.keys import STRATA_CONTROLS_HINT, pygameKeyFor
from strata_view.ui import RecordingGraphik, drawScreen

# How long the controls show at the start of a simulation (they come back
# whenever it is paused), and how long a notice stays up.
CONTROLS_SECONDS = 8.0
NOTICE_SECONDS = 4.0
# The 2D window waits this long on the last frame once every living entity is gone.
END_HOLD_SECONDS = 1.0

class StrataSimulationScreen(SimulationScreen):
    """The 2D simulation screen, with the window-level effects of M and F11
    sent to the Strata window instead of pygame's display."""

    def __init__(self, graphik, config, app):
        super().__init__(graphik, config)
        self.app = app
        self.caption = "Apex"

    def applyCaption(self, caption):
        self.caption = caption
        self.app.setTitle(caption)

    def applyFullscreen(self):
        self.app.applyFullscreen()


class StrataApex:
    def __init__(self, renderer=None, recordPath=None, usageReporting=None, clock=time.monotonic):
        self.renderer = renderer
        self.recordPath = recordPath
        self.recording = None
        self.recordingFinished = False
        self.clock = clock
        self.running = True
        # the pygame mixer plays the reproduce and death sounds; no pygame window is opened
        try:
            pygame.mixer.init()
        except pygame.error as error:
            print("Warning: no sound (the pygame mixer couldn't start): " + str(error))
        self.usageReporting = usageReporting if usageReporting is not None else UsageReportingService()
        self.usageReporting.reportStartup()
        self.config = Config()
        width = renderer.width if renderer is not None else self.config.displayWidth
        height = renderer.height if renderer is not None else self.config.displayHeight
        self.width, self.height = width, height
        self.graphik = RecordingGraphik(width, height)
        # the simulation screen records into its own graphik: its alerts are
        # kept from one simulation step to the next, its statistics per frame
        self.simulationGraphik = RecordingGraphik(width, height)
        self.simulationGraphik.gameDisplay = self.graphik.gameDisplay
        self.mainMenuScreen = MainMenuScreen(self.graphik)
        self.setupScreen = SetupScreen(self.graphik, self.config)
        self.simulationScreen = StrataSimulationScreen(self.simulationGraphik, self.config, self)
        self.resultsScreen = ResultsScreen(self.graphik)
        for screen in (self.mainMenuScreen, self.setupScreen, self.resultsScreen):
            # the quit button leaves the Strata window cleanly rather than calling quit()
            screen.quitApplication = self.quit
        self.currentScreen = self.mainMenuScreen
        self.menuItems = []
        self.alertItems = []
        self.nextStep = 0.0
        self.endingAt = None
        self.simulationStartedAt = 0.0
        self.notice = None
        self.noticeUntil = 0.0
        self.frameMs = []

    # -- screens ---------------------------------------------------------------

    def goTo(self, result):
        """What Apex.run does with a screen's result."""
        if self.currentScreen is self.simulationScreen:
            self.finishRecording()
        if result == ScreenType.MAIN_MENU_SCREEN:
            self.currentScreen = self.mainMenuScreen
        elif result == ScreenType.SETUP_SCREEN:
            self.currentScreen = self.setupScreen
        elif result == ScreenType.SIMULATION_SCREEN:
            self.config.calculateValues()
            self.simulationScreen.initializeSimulation()
            self.startRecording()
            self.usageReporting.reportSimulationStarted()
            self.currentScreen = self.simulationScreen
            self.alertItems = []
            self.endingAt = None
            self.nextStep = self.clock()
            self.simulationStartedAt = self.clock()
        elif result == ScreenType.RESULTS_SCREEN:
            self.currentScreen = self.resultsScreen
            self.resultsScreen.initializeWithSimulation(self.simulationScreen.simulation)
        else:
            self.quit()

    def checkScreenChange(self):
        screen = self.currentScreen
        if screen is self.simulationScreen:
            if screen.isChangingScreen():
                screen.finishScreenChange()
                self.goTo(screen.getNextScreen())
        elif screen.changeScreen:
            screen.changeScreen = False
            self.goTo(screen.nextScreen)

    def quit(self):
        self.running = False

    def startRecording(self):
        if self.recordPath is None or self.recordingFinished:
            return
        self.recording = UsdRecording(self.recordPath, self.config.gridSize)
        self.simulationScreen.setRecording(self.recording)

    def finishRecording(self):
        if self.recording is None:
            return
        self.simulationScreen.setRecording(None)
        path = self.recording.close()
        print("Recorded " + str(self.recording.getTicksRecorded()) + " ticks to " + str(path))
        self.recording = None
        self.recordingFinished = True

    # -- window-level effects ----------------------------------------------------

    def showNotice(self, text):
        self.notice = text
        self.noticeUntil = self.clock() + NOTICE_SECONDS

    def setTitle(self, title):
        # Strata 0.7.0 can't retitle an open window; the HUD shows the caption instead
        if self.renderer is not None and self.renderer.isWindow:
            self.renderer.setTitle(title)

    def applyFullscreen(self):
        """F11 flips config.fullscreen, as in the 2D window; here it switches
        the Strata window."""
        if self.renderer is None or not self.renderer.isWindow:
            return
        if not self.renderer.setFullscreen(self.config.fullscreen):
            self.config.fullscreen = False
            self.showNotice("Fullscreen needs a newer Strata library than this one.")

    def resize(self, width, height):
        self.width, self.height = width, height
        self.graphik.resize(width, height)
        if self.renderer is not None:
            self.renderer.resize(width, height)
        if self.currentScreen is self.simulationScreen:
            self.simulationScreen.simulation.initializeLocationWidthAndHeight()

    # -- input -------------------------------------------------------------------

    def handleKeyDown(self, scancode):
        screen = self.currentScreen
        if screen is self.simulationScreen:
            key = pygameKeyFor(scancode, pygame)
            if key is not None:
                screen.handleKeyDownEvent(key)
        elif screen is not self.setupScreen:
            # the main menu and results screens take any key
            screen.handleKeyDownEvent(scancode)
        self.checkScreenChange()

    def handleClick(self, position):
        screen = self.currentScreen
        if screen is self.resultsScreen:
            screen.switchToSetupScreen()  # a click or a tap anywhere, as in 2D
        elif screen is self.simulationScreen:
            if not self.config.localView:
                self.selectAt(position)
        else:
            self.drawMenu()
            self.graphik.click(position)
        self.checkScreenChange()

    def selectAt(self, position):
        """A click on a tile: the location's contents, as an alert beside it,
        and its top living entity selected (for V), as a click in 2D does."""
        from strata_view.scene import cameraFor, cellScreenPosition, screenToCell

        screen = self.simulationScreen
        grid = screen.simulation.environment.getGrid()
        columns, rows = grid.getColumns(), grid.getRows()
        camera = cameraFor(columns, rows, self.width, self.height)
        cell = screenToCell(camera, position, self.width, self.height, columns, rows)
        if cell is None:
            return None
        location = grid.getLocationByCoordinates(cell[0], cell[1])
        alerts = screen.getTextAlerts()
        before = len(alerts)
        screen.selectLocation(location)
        if len(alerts) > before:
            # the alert goes beside the tile as it appears on screen
            at = cellScreenPosition(camera, cell[0], cell[1], columns, rows, self.width, self.height)
            if at is not None:
                alert = alerts[-1]
                alert.x = at[0] + 20 + alert.size * 6
                alert.y = at[1]
        return location

    # -- the simulation ------------------------------------------------------------

    def tickDelay(self):
        if not self.config.limitTickSpeed:
            return 0.0
        return (self.config.maxTickSpeed - self.config.tickSpeed) / self.config.maxTickSpeed

    def simulationStep(self):
        """One pass of SimulationScreen.run's loop, minus its pygame drawing."""
        screen = self.simulationScreen
        simulation = screen.simulation
        if not screen.isPaused():
            simulation.update()
            recording = screen.getRecording()
            if recording is not None:
                recording.recordTick(simulation)
        self.simulationGraphik.reset()
        screen.drawTextAlerts()
        self.alertItems = list(self.simulationGraphik.items)
        selected = screen.getSelectedEntity()
        if selected is not None and not simulation.environment.isEntityPresent(selected):
            screen.setSelectedEntity(None)
            if self.config.localView:
                self.config.localView = False
        if not screen.isPaused():
            simulation.numTicks += 1
        if self.config.endSimulationUponAllLivingEntitiesDying and simulation.getNumLivingEntities() == 0:
            self.endingAt = self.clock() + END_HOLD_SECONDS

    def endSimulation(self):
        screen = self.simulationScreen
        screen.simulation.cleanup()
        if self.config.randomizeGridSizeUponRestart:
            self.config.randomizeGridSize()
            self.config.randomizeGrassGrowTime()
            self.config.calculateValues()
        screen.setPaused(False)
        self.endingAt = None
        screen.requestScreen(ScreenType.RESULTS_SCREEN)
        self.checkScreenChange()

    def advance(self, now=None):
        """Runs whatever simulation step is due at `now`."""
        if self.currentScreen is not self.simulationScreen:
            return
        now = self.clock() if now is None else now
        if self.endingAt is not None:
            if now >= self.endingAt:
                self.endSimulation()
        elif now >= self.nextStep:
            self.simulationStep()
            self.nextStep = now + self.tickDelay()

    # -- drawing -----------------------------------------------------------------

    def drawMenu(self):
        self.menuItems = list(drawScreen(self.currentScreen, self.graphik))
        return self.menuItems

    def versionItems(self):
        graphik = RecordingGraphik(self.width, self.height)
        MainMenuScreen(graphik).drawVersion()
        return graphik.items

    def hud(self):
        """Labels and panels over the board: everything the 2D simulation
        screen shows besides the board, and what the 2D window says in its
        title bar (strata_view.hud, shared with the browser's 3D view)."""
        screen = self.simulationScreen
        statsItems = []
        if screen.isDebugEnabled():
            self.simulationGraphik.reset()
            screen.displayStats()
            statsItems = list(self.simulationGraphik.items)
        now = self.clock()
        showControls = screen.isPaused() or now - self.simulationStartedAt < CONTROLS_SECONDS
        notice = self.notice if self.notice and now < self.noticeUntil else None
        return simulationHud(
            self.width, self.height, screen.caption, screen.isPaused(),
            statsItems=statsItems, alertItems=self.alertItems,
            controls=STRATA_CONTROLS_HINT if showControls else (),
            notice=notice, versionItems=self.versionItems())

    def buildScene(self):
        from strata_view.scene import buildSimulationScene, menuScene

        if self.currentScreen is self.simulationScreen:
            labels, panels = self.hud()
            return buildSimulationScene(self.simulationScreen, self.config, self.width, self.height, labels, panels)
        return menuScene(self.drawMenu())

    def renderFrame(self, present=True):
        if self.renderer is None:
            return
        started = time.perf_counter()
        self.renderer.draw(self.buildScene(), present=present)
        self.frameMs.append((time.perf_counter() - started) * 1000.0)

    # -- the window loop ---------------------------------------------------------

    def handleEvent(self, event):
        strata = self.renderer.strata
        if event.type == strata.EVENT_QUIT:
            if self.currentScreen is self.simulationScreen:
                self.finishRecording()
            self.quit()
        elif event.type == strata.EVENT_KEY_DOWN and not event.repeat:
            self.handleKeyDown(event.scancode)
        elif event.type == strata.EVENT_MOUSE_BUTTON_DOWN:
            self.handleClick((event.x, event.y))
        elif event.type == strata.EVENT_RESIZED:
            self.resize(event.width, event.height)

    def run(self):
        try:
            while self.running:
                for event in self.renderer.pollEvents():
                    self.handleEvent(event)
                    if not self.running:
                        break
                if not self.running:
                    break
                self.advance()
                if not self.running:
                    break
                self.renderFrame()
                time.sleep(1 / 120)
        finally:
            self.finishRecording()
            self.usageReporting.close()
            try:
                pygame.mixer.quit()
            except pygame.error:
                pass


def runStrataApex(recordPath=None):
    """Runs Apex in a Strata window; raises StrataUnavailable, with the
    reason, when one can't open here."""
    try:
        from strata_view.renderer import StrataRenderer

        config = Config()
        renderer = StrataRenderer(config.displayWidth, config.displayHeight, window=True, title="Apex")
    except ImportError as error:
        raise StrataUnavailable("%s; the README's 3D section says how to add it" % error)
    except Exception as error:  # no display, no GPU driver, unsupported platform
        raise StrataUnavailable(str(error))
    try:
        StrataApex(renderer=renderer, recordPath=recordPath).run()
    finally:
        renderer.close()

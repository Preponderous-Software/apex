"""Apex's 3D view in the browser (the arcade's pygbag build).

The browser game is the 2D game, Apex's async screens, and the page's 2D/3D
button (graphik's pygbag template) only changes how it is shown. The page
starts in 3D, as the desktop does, unless the player chose 2D there before
or the address says ?view=2d. While 3D is on, WebApex sends what the desktop 3D window draws (strata_view:
the board, its entities and the HUD over it, and the menu, setup and results
screens as screen text and buttons) to the page's Strata grid relay through
graphik's Grid3DWebView. The screens, their rules and their keys stay the 2D
game's own, so the view can be switched either way on any screen, in the
middle of a simulation, and every 2D control works in 3D:

- keys reach pygame's own SDL whichever view shows (it listens on the whole
  page), so the 2D screens read them as always;
- the mouse and touch land on the relay's canvas while the 3D view shows, so
  they are read from the relay: on a menu a press runs the 2D button's own
  function (the screen is drawn into graphik's ScreenRecorder to find it), on
  the results screen it returns to setup, and on the board it picks the tile
  under it and selects that location through the 2D screen, which shows its
  contents in an alert, as a click does in 2D.

The 3D view runs beside the 2D screens as its own task, once a display
frame: it follows the toggle, reads the relay's input and sends only what
changed. A 64x64 board's tiles go as merged runs (GridBoard mergeTiles) and
are sent again only when a tile changes; the entities at most once a
simulation step, and no more often than MIN_STEP_SECONDS, so a fast
simulation (the speed limit off) isn't slowed down by its own 3D view; the
HUD when its text does. While the 3D view shows the board, the hidden 2D
canvas isn't drawn on; it is drawn again when the 2D view comes back.

On a touch screen (graphik's touchScreen(): a phone, a tablet) the
simulation's keys - pause, statistics, tick speed and its limit, spawning
each animal, the local view and its size, highlighting the oldest, eyes,
mute, back to setup and to the results - are on-screen keys along the bottom
(graphik's TouchKeys, keys.TOUCH_KEYS; More pages through them), in both
views: a tap on one posts the key it names to pygame's queue, so the 2D
simulation screen's own handler does the rest. In 3D the keys are part of
the HUD and the board is framed above them (the view's insets); in 2D the
canvas is made taller by the bar's height and the screens draw on the part
above it (a subsurface), so the bar never covers the board.

If the 3D view can't start, the 2D view stays and the page says why; a page
in 2D downloads nothing of the 3D view until it is asked for. The 3D text
and buttons keep out from under the page's 2D/3D button (graphik's
buttonArea()).
"""

import asyncio
import copy
import time
import traceback
from dataclasses import replace

import pygame

from apex import Apex
from preponderous.graphik import Graphik
from preponderous.graphik.grid3d import Camera, Scene, TouchKeys, Unavailable
from preponderous.graphik.grid3d import web as grid3dweb
from screen.mainMenuScreen import MainMenuScreen
from screen.simulationScreen import SimulationScreen
from strata_view.hud import CAPTION_SIZE, fitLabels, simulationHud
from strata_view.keys import TOUCH_CONTROLS_HINT, TOUCH_KEYS, WEB_CONTROLS_HINT
from strata_view.scene import CLEAR_COLOR, overlayFrom, simulationBoard
from strata_view.ui import RecordingGraphik, UiButton, UiRect, UiText, drawScreen
from ui.textAlertDrawTool import TextAlertDrawTool

VIEW_TITLE = "Apex (3D)"
# the 3D view's size gate: Strata's relay is about 1.4 MB; anything far
# bigger than that is not the file this build was made with
MAX_3D_BYTES = 4000000
# how often the 3D view looks for changes and input (the relay draws on the
# page's own frames)
FRAME_SECONDS = 1 / 60.0
# How long the controls show at the start of a simulation (they come back
# whenever it is paused), as in the desktop 3D window.
CONTROLS_SECONDS = 8.0
# The 2D screens are laid out for a 1280x720 window. The 3D view lays them
# out at least this big and scales them down to fit a smaller one (a phone),
# as the browser scales the 2D canvas.
LAYOUT_MIN_WIDTH, LAYOUT_MIN_HEIGHT = 640, 720
# A 3D button is at least this big to tap where there is room (touchButtons)
MIN_TAP = 40
# the HUD's caption, top right (moved left of the page's 2D/3D button)
CAPTION_TOP = 12
# what is drawn keeps this far from the 2D/3D button
BUTTON_GAP = 6
# On a touch screen the board is framed below the caption and the page's 2D/3D
# button, and above the keys, the version and the controls line.
BOARD_TOP = 52
BOARD_BOTTOM = 66
# The board and its entities are rebuilt at most this often (a simulation
# step with the speed limit off can come every display frame). A key or a
# press that changes what is shown is drawn at once.
MIN_STEP_SECONDS = 0.15
# a camera for screens with no board: only its clear colour shows
NO_BOARD_CAMERA = Camera(eye=(0.0, 10.0, 10.0), target=(0.0, 0.0, 0.0))


class BrowserPage:
    """The page around the game under pygbag: its 3D toggle, its size and
    its grid relay (graphik's grid3d.web)."""

    def wants3D(self):
        return grid3dweb.wants3D()

    def set3D(self, on, reason=""):
        grid3dweb.set3D(on, reason)

    def size(self):
        window = _platformWindow()
        return int(window.innerWidth), int(window.innerHeight)

    def buttonArea(self):
        """Where the page's 2D/3D button is, (x, y, width, height), or None."""
        return grid3dweb.buttonArea()

    def touchScreen(self):
        """Whether the page is on a touch screen, where the simulation shows
        its on-screen keys."""
        return grid3dweb.touchScreen()

    def fitCanvas(self):
        """Has pygbag fit its canvas to the display's new shape (it does so
        only when the page is resized)."""
        _platformWindow().eval("window.dispatchEvent(new Event('resize'))")

    def openView(self, width, height):
        return grid3dweb.Grid3DWebView.open(width, height, title=VIEW_TITLE, maxBytes=MAX_3D_BYTES)


def _platformWindow():
    import platform  # pygbag's, not the standard library's

    return platform.window


def unavailableMessage(reason):
    """Why there is no 3D view, in words a player can act on."""
    return "No 3D view here ({}). The 2D view stays.".format(
        str(reason).strip().rstrip(".") or "it could not load"
    )


def layoutScale(width, height):
    """How much the 2D screens' layout is scaled to fit a window this size
    (1 for a window at least LAYOUT_MIN_WIDTH x LAYOUT_MIN_HEIGHT)."""
    return min(1.0, width / float(LAYOUT_MIN_WIDTH), height / float(LAYOUT_MIN_HEIGHT))


def scaleItems(items, scale):
    """What a 2D screen drew at the layout size, at the window's."""
    if scale == 1.0:
        return list(items)
    scaled = []
    for item in items:
        if isinstance(item, UiText):
            scaled.append(replace(item, x=item.x * scale, y=item.y * scale, size=item.size * scale))
        elif isinstance(item, UiRect):
            scaled.append(replace(item, x=item.x * scale, y=item.y * scale,
                                  width=item.width * scale, height=item.height * scale))
        elif isinstance(item, UiButton):
            scaled.append(replace(item, x=item.x * scale, y=item.y * scale, width=item.width * scale,
                                  height=item.height * scale, textSize=item.textSize * scale))
    return scaled


def touchButtons(items, width, minTap=MIN_TAP):
    """The items with every button big enough to read and to tap: wide
    enough for its label and at least minTap pixels each way, about the same
    middle across, the same top, and inside the window. A button grows down
    only until the next thing drawn below it (setup's settings are stacked
    close on a short window), and buttons that would overlap side by side
    (setup's - and +) meet halfway instead."""
    from strata_view.scene import LABEL_RISE, pixelSize, textWidth

    def box(item):
        if isinstance(item, UiText):
            size = pixelSize(item.size)
            wide = textWidth(item.text, size)
            return item.x - wide / 2.0, item.y - LABEL_RISE * size, wide, size
        return item.x, item.y, item.width, item.height

    out = []
    buttons = []
    for item in items:
        if not isinstance(item, UiButton):
            out.append(item)
            continue
        label = textWidth(item.text, pixelSize(item.textSize)) + 12
        newWidth = min(width - 16, max(item.width, minTap, label))
        middleX = item.x + item.width / 2.0
        x = min(max(8, middleX - newWidth / 2.0), max(8, width - 8 - newWidth))
        newHeight = max(item.height, minTap)
        for other in items:
            if other is item or isinstance(other, UiRect):
                continue
            ox, oy, ow, oh = box(other)
            if oy > item.y + item.height / 2.0 and ox < x + newWidth and x < ox + ow:
                newHeight = max(item.height, min(newHeight, oy - 2 - item.y))
        button = replace(item, x=x, width=newWidth, height=newHeight)
        buttons.append(button)
        out.append(button)
    for a in buttons:
        for b in buttons:
            if a is b or a.x >= b.x:
                continue
            overlapsY = a.y < b.y + b.height and b.y < a.y + a.height
            if overlapsY and a.x + a.width > b.x:
                meet = (a.x + a.width + b.x) / 2.0
                right = b.x + b.width
                a.width = meet - 1 - a.x
                b.x = meet + 1
                b.width = right - b.x
    return out


def _overlaps(x, y, width, height, area, gap=BUTTON_GAP):
    ax, ay, aw, ah = area
    return x < ax + aw + gap and ax - gap < x + width and y < ay + ah + gap and ay - gap < y + height


def clearOfButton(labels, area, windowWidth):
    """The labels, any under the page's 2D/3D button moved out from under it:
    to its left where it fits there, else below it."""
    if area is None:
        return list(labels)
    from preponderous.graphik.grid3d import Label, measureText

    ax, ay, aw, ah = area
    out = []
    for label in labels:
        wide = measureText(label.text, label.pixelSize)
        if not _overlaps(label.x, label.y, wide, label.pixelSize, area):
            out.append(label)
        elif ax - BUTTON_GAP - wide >= 8:
            out.append(Label(label.text, ax - BUTTON_GAP - wide, label.y, label.pixelSize, label.color))
        else:
            out.append(Label(label.text, label.x, ay + ah + BUTTON_GAP, label.pixelSize, label.color))
    return out


def buttonsClearOfButton(items, area):
    """Menu items, any button under the page's 2D/3D button moved below it."""
    if area is None:
        return items
    ax, ay, aw, ah = area
    return [replace(item, y=ay + ah + BUTTON_GAP)
            if isinstance(item, UiButton) and _overlaps(item.x, item.y, item.width, item.height, area)
            else item for item in items]


class WebSimulationScreen(SimulationScreen):
    """The 2D simulation screen, counting its simulation's steps, so the 3D
    view knows when the board has changed, and leaving the board to the 3D
    view while that shows it."""

    def __init__(self, graphik, config, game=None):
        super().__init__(graphik, config)
        self.steps = 0
        self.boardIn3D = False
        self.game = game

    def handlePointerDown(self, position):
        """A press on the 2D bar of on-screen keys is the key's, not a
        click on a location."""
        return self.game is not None and self.game.pressTouchKey2D(position)

    def isDrawingBoard(self):
        return not self.boardIn3D

    def initializeSimulation(self):
        super().initializeSimulation()
        simulation = self.simulation
        update = simulation.update

        def countedUpdate():
            update()
            self.steps += 1

        simulation.update = countedUpdate


class WebApex(Apex):
    """The browser game, with the page's 3D view when the player asks."""

    def __init__(self, page=None, clock=time.monotonic):
        self.page = page if page is not None else BrowserPage()
        self.clock = clock
        self.view3d = None
        # the simulation's on-screen keys on a touch screen; the 2D window
        # with the bar below the screens' part, its height, and the Graphik
        # that draws it (set before Apex makes the display)
        self.touchKeys = TouchKeys(TOUCH_KEYS)
        self.touch = self.readTouch()
        self.screen2D = None
        self.band2D = 0
        self.barGraphik = None
        super().__init__()
        self.simulationScreen = WebSimulationScreen(self.graphik, self.config, self)
        self.alertTool = TextAlertDrawTool()
        self.menuButtons = []
        self.simulationShown = None  # the simulation the controls hint was started for
        self.simulationShownAt = 0.0
        self.frameMs = []
        self.keepClear = None  # the page's 2D/3D button, (x, y, width, height)
        self.steppedAt = None  # when the board was last rebuilt for a simulation step
        self.forget3D()

    # -- the on-screen keys (touch screens)

    def readTouch(self):
        ask = getattr(self.page, "touchScreen", None)
        return bool(ask()) if ask is not None else False

    def createGameDisplay(self):
        """On a touch screen, the 2D window is the screens' size plus the
        bar of on-screen keys below it; the screens draw on the part above
        (a subsurface), so the bar never covers the board."""
        if not self.touch:
            return super().createGameDisplay()
        width, height = self.config.displayWidth, self.config.displayHeight
        pageWidth, pageHeight = self.page.size()
        self.band2D, _ = self.touchKeys.below(width, height, pageWidth, pageHeight)
        self.screen2D = pygame.display.set_mode((width, height + self.band2D))
        self.barGraphik = Graphik(self.screen2D)
        fit = getattr(self.page, "fitCanvas", None)
        if fit is not None:
            try:
                fit()
            except Exception as error:  # the canvas keeps its shape
                print("Warning: could not fit the canvas to the page: " + str(error))
        return self.screen2D.subsurface((0, 0, width, height))

    def keysShown(self):
        """The keys are the simulation's: shown while it is on screen."""
        return self.currentScreen is self.simulationScreen

    def scale2D(self):
        """(CSS pixels per 2D canvas pixel, portrait) as the page fits the
        canvas."""
        pageWidth, pageHeight = self.page.size()
        width, height = self.screen2D.get_size()
        return min(pageWidth / float(width), pageHeight / float(height)), pageHeight > pageWidth

    def drawTouchKeys2D(self):
        """The bar under the 2D screens: the simulation's keys, or empty."""
        if self.screen2D is None:
            return
        width, height = self.screen2D.get_size()
        self.barGraphik.drawRectangle(0, height - self.band2D, width, self.band2D,
                                      self.touchKeys.barColor)
        if self.keysShown():
            scale, portrait = self.scale2D()
            self.touchKeys.draw(self.barGraphik, width, height, scale, portrait)
        pygame.display.update((0, height - self.band2D, width, self.band2D))

    def pressTouchKey2D(self, position):
        """A press on the 2D bar: its key posted to pygame's queue (or the
        next page of keys). True when the press was on the bar."""
        if self.screen2D is None or not self.keysShown():
            return False
        width, height = self.screen2D.get_size()
        scale, portrait = self.scale2D()
        if self.touchKeys.press(position, width, height, pygame, scale, portrait) is None:
            return False
        self.drawTouchKeys2D()
        return True

    def pressTouchKey3D(self, position):
        """A press on the 3D view's bar, as pressTouchKey2D."""
        view = self.view3d
        if not self.touch or view is None or not self.keysShown():
            return False
        return self.touchKeys.press(position, view.width, view.height, pygame) is not None

    def touchBand3D(self):
        view = self.view3d
        if not self.touch or view is None or not self.keysShown():
            return 0
        return self.touchKeys.bandHeight(view.width, view.height)

    def frameBoard3D(self):
        """On a touch screen the board stands below the caption and above
        the keys; elsewhere it is framed as graphik frames it for the
        window's shape. A new camera is sent at once."""
        view = self.view3d
        if self.touch:
            changed = view.setInsets(top=BOARD_TOP, bottom=self.touchBand3D() + BOARD_BOTTOM)
        else:
            changed = view.setInsets()
        if changed and view.board is not None and self.mode3D == "board":
            self.sendView()

    # -- the toggle

    def forget3D(self):
        """Forgets what the 3D view was last sent, so it is all sent again."""
        self.mode3D = None  # "board", or "scene" (a menu, or a board with no one alive)
        self.sentBoard = None
        self.sentPieces = None
        self.sentState = None
        self.sentHud = None

    def follow3DToggle(self):
        """Opens or closes the 3D view to match the page's toggle."""
        wanted = self.page.wants3D()
        if wanted and self.view3d is None:
            self.open3D()
        elif not wanted and self.view3d is not None:
            self.close3D()

    def open3D(self):
        try:
            width, height = self.page.size()
            self.view3d = self.page.openView(width, height)
        except Unavailable as reason:
            self.view3d = None
            self.page.set3D(False, unavailableMessage(reason))
            print(unavailableMessage(reason))
            return
        self.readButtonArea()
        self.forget3D()

    def readButtonArea(self):
        """Where the page's 2D/3D button is now (read on opening and on a
        resize, as the page lays it out)."""
        area = getattr(self.page, "buttonArea", None)
        self.keepClear = area() if area is not None else None

    def close3D(self, reason=None):
        """Back to the 2D view; if the 3D view failed, the toggle says why."""
        view, self.view3d = self.view3d, None
        reason = reason or view.failure()
        view.close()
        self.showBoardIn2D()
        if reason:
            self.page.set3D(False, unavailableMessage(reason))
            print(unavailableMessage(reason))

    def showBoardIn2D(self):
        """The 2D loop draws the board again, and the hidden canvas is
        brought up to date now (a paused simulation draws no new step)."""
        screen = self.simulationScreen
        if screen.boardIn3D:
            screen.boardIn3D = False
            if self.currentScreen is screen:
                screen.drawBoard()

    # -- running beside the 2D screens

    async def run(self):
        task = asyncio.ensure_future(self.run3D())
        try:
            await super().run()
        finally:
            task.cancel()

    async def run3D(self):
        while True:
            self.drawTouchKeys2D()
            self.update3D()
            await asyncio.sleep(FRAME_SECONDS)

    def update3D(self):
        """One display frame of the 3D view. Whatever goes wrong in it, the
        2D game goes on, in the 2D view."""
        try:
            self.follow3DToggle()
            if self.view3d is None:
                return
            if self.view3d.ready:
                self.simulationScreen.boardIn3D = True
            elif self.simulationScreen.boardIn3D:
                self.showBoardIn2D()  # the 3D view went away while loading again
            self.read3DInput()
            started = time.perf_counter()
            self.draw3D()
            self.frameMs.append((time.perf_counter() - started) * 1000.0)
            del self.frameMs[:-600]
        except Exception as error:
            traceback.print_exc()
            if self.view3d is not None:
                self.close3D(str(error) or type(error).__name__)

    # -- input

    def read3DInput(self):
        """The relay's resizes, and its mouse and touch presses."""
        view = self.view3d
        for event in view.pollEvents():
            if event.type == grid3dweb.EVENT_RESIZED and event.width and event.height:
                view.resize(event.width, event.height)
                self.readButtonArea()
                self.forget3D()
            elif event.type == grid3dweb.EVENT_MOUSE_BUTTON_DOWN:
                self.press((event.x, event.y))

    def press(self, position):
        """A click or a tap on the 3D view: what the same press does in 2D."""
        screen = self.currentScreen
        if self.pressTouchKey3D(position):
            pass  # an on-screen key: its key is posted for the screen's handler
        elif screen is self.resultsScreen:
            screen.switchToSetupScreen()  # anywhere, as in 2D
        elif screen is self.simulationScreen:
            if not self.config.localView:  # 2D ignores clicks in local view
                self.selectAt(position)
        else:
            self.drawMenu()
            for button in self.menuButtons:
                if button.contains(position):
                    button.function()
                    break
        self.forget3DHud()

    def selectAt(self, position):
        """A press on a tile: the 2D screen selects that location (its
        contents in an alert, its top living entity selected for V)."""
        view = self.view3d
        screen = self.simulationScreen
        if self.mode3D != "board" or view.board is None:
            return None
        cell = view.pickCell(position[0], position[1])
        if cell is None:
            return None
        location = screen.simulation.environment.getGrid().getLocationByCoordinates(cell[0], cell[1])
        if location == -1:
            return None
        screen.selectLocation(location)
        return location

    def forget3DHud(self):
        self.sentHud = None
        self.sentState = None

    # -- drawing

    def draw3D(self):
        if self.currentScreen is self.simulationScreen:
            self.drawSimulation()
        else:
            self.showScene(*self.menuOverlay())

    def drawMenu(self):
        """Records the 2D menu screen at the layout size and scales it to the
        view; the buttons are kept to be pressed."""
        view = self.view3d
        scale = layoutScale(view.width, view.height)
        recorder = RecordingGraphik(view.width / scale, view.height / scale)
        screen = self.currentScreen
        graphik = screen.graphik
        screen.graphik = recorder
        try:
            items = drawScreen(screen, recorder)
        finally:
            screen.graphik = graphik
        items = buttonsClearOfButton(touchButtons(scaleItems(items, scale), view.width), self.keepClear)
        self.menuButtons = [item for item in items if isinstance(item, UiButton)]
        return items

    def menuOverlay(self):
        labels, panels = overlayFrom(self.drawMenu())
        width = self.view3d.width
        return clearOfButton(fitLabels(labels, width), self.keepClear, width), panels

    def showScene(self, labels, panels):
        """A screen with no board: the menus, and the simulation once every
        living entity is gone (the 2D screen shows no board then either)."""
        view = self.view3d
        if self.mode3D != "scene":
            view.lastSent.clear()  # setBoard and setPieces don't keep what they sent
            self.forget3D()
            self.mode3D = "scene"
        view.drawScene(Scene(labels=labels, panels=panels, camera=NO_BOARD_CAMERA,
                             clearColor=CLEAR_COLOR))

    def simulationState(self):
        """What the board shows changes only with these: the simulation's
        steps, and what the player changes (keys, a selection)."""
        screen, config = self.simulationScreen, self.config
        simulation = screen.simulation
        selected = screen.getSelectedEntity()
        # entities come and go with the steps (and the spawn keys, drawn
        # within MIN_STEP_SECONDS too)
        steps = (screen.steps, simulation.numTicks, len(simulation.entities))
        shown = (id(simulation), config.localView, config.localViewSize,
                 config.highlightOldestEntity, config.eyesEnabled,
                 None if selected is None else selected.getID(),
                 # a click frames its location while the alert is up
                 tuple(getattr(alert, "cell", None) for alert in screen.getTextAlerts()))
        return steps, shown

    def boardDue(self, state):
        """Whether to rebuild the board now: at once for a change the player
        made, at most every MIN_STEP_SECONDS for simulation steps alone."""
        if state == self.sentState:
            return False
        if self.sentState is None or state[1] != self.sentState[1]:
            return True
        return self.steppedAt is None or self.clock() - self.steppedAt >= MIN_STEP_SECONDS

    def drawSimulation(self):
        screen = self.simulationScreen
        simulation = screen.simulation
        if simulation is not self.simulationShown:
            self.simulationShown = simulation
            self.simulationShownAt = self.clock()
        if simulation.getNumLivingEntities() == 0:
            self.showScene(*self.simulationHud())
            return
        view = self.view3d
        if self.mode3D != "board":
            self.forget3D()
            self.mode3D = "board"
        self.frameBoard3D()
        state = self.simulationState()
        if self.boardDue(state):
            self.steppedAt = self.clock()
            board, pieces = simulationBoard(screen, self.config)
            boardKey = (board.columns, board.rows, board.viewport, board.tiles)
            if boardKey != self.sentBoard:
                # setBoard sends the pieces it last had again; they are about
                # to be replaced, so it is given none to encode
                view.pieces = []
                view.setBoard(board)
                self.sendView()
                self.sentBoard = boardKey
                self.sentPieces = None
            if pieces != self.sentPieces:
                view.setPieces(pieces, snap=True)
                self.sentPieces = pieces
            self.sentState = state
        self.sendHud(*self.simulationHud())

    def sendView(self):
        """The camera again, with the 2D window's black behind the board."""
        view = self.view3d
        status = view.relay.send(grid3dweb.encodeView(view.camera(), CLEAR_COLOR))
        if status < 0:
            raise grid3dweb.WireError(status, "the grid relay refused the view")

    def sendHud(self, labels, panels):
        hud = grid3dweb.encodeHud(labels, panels)
        if hud != self.sentHud:
            self.view3d.setLabels(labels, panels)
            self.sentHud = hud

    def simulationHud(self):
        """The desktop 3D window's HUD (strata_view.hud), with the browser's
        controls and the alerts placed beside their tiles."""
        view = self.view3d
        screen = self.simulationScreen
        scale = layoutScale(view.width, view.height)
        # laid out above the on-screen keys, which go on top
        band = self.touchBand3D()
        statsItems = []
        if screen.isDebugEnabled():
            recorder = RecordingGraphik(view.width, view.height)
            screen.displayStats(recorder)
            statsItems = compactStats(recorder.items, view.height - band)
        # kept above the on-screen keys, as the rest of the HUD is
        alerts = RecordingGraphik(view.width, view.height - band)
        for alert in screen.getTextAlerts():
            self.alertTool.drawTextAlert(self.alertIn3D(alert), alerts)
        version = RecordingGraphik(view.width / scale, (view.height - band) / scale)
        MainMenuScreen(version).drawVersion()  # the 2D screens draw it alike
        paused = screen.isPaused()
        showControls = paused or self.clock() - self.simulationShownAt < CONTROLS_SECONDS
        hint = TOUCH_CONTROLS_HINT if self.touch else WEB_CONTROLS_HINT
        labels, panels = simulationHud(
            view.width, view.height - band, screen.getCaption(), paused,
            statsItems=statsItems, alertItems=alerts.items,
            controls=hint if showControls else (),
            versionItems=scaleItems(version.items, scale), captionTop=CAPTION_TOP,
            captionRight=self.captionRight())
        labels = clearOfButton(labels, self.keepClear, view.width)
        if band:
            keyLabels, keyPanels = self.touchKeys.overlay(view.width, view.height)
            labels, panels = labels + keyLabels, panels + keyPanels
        return labels, panels

    def captionRight(self):
        """Where the caption must end to stay left of the page's 2D/3D button
        (when the button is on the caption's line), or None."""
        area = self.keepClear
        if area is None:
            return None
        ax, ay, aw, ah = area
        if ay >= CAPTION_TOP + CAPTION_SIZE or ay + ah <= CAPTION_TOP:
            return None
        return ax - BUTTON_GAP

    def alertIn3D(self, alert):
        """A copy of a location alert placed beside its tile as the 3D view
        draws it (the 2D one stays where 2D draws it)."""
        placed = copy.copy(alert)
        cell = getattr(alert, "cell", None)
        if cell is not None and self.mode3D == "board" and self.view3d.board is not None:
            board = self.view3d.board
            if board.visible(*cell):
                at = self.view3d.cellScreenPosition(cell[0], cell[1], y=0.5)
                if at is not None:
                    placed.x = at[0] + 20 + alert.size * 6
                    placed.y = at[1]
        return placed


def compactStats(items, height, margin=50):
    """The 2D statistics (a name, its value and a gap, a line each), or, on a
    window too short for them, each name and value on one line."""
    texts = [item for item in items if isinstance(item, UiText)]
    if not texts or max(item.y for item in texts) + margin <= height:
        return list(items)
    first = texts[0]
    lines = []
    for index in range(0, len(texts) - 1, 3):
        name, value = texts[index], texts[index + 1]
        lines.append(replace(name, text=name.text + " " + value.text, y=first.y + first.size * len(lines)))
    return lines

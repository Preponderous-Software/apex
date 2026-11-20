"""Apex's 3D view in the browser (the arcade's pygbag build).

The browser game is the 2D game, Apex's async screens, and the page's 3D
toggle (graphik's pygbag template) only changes how it is shown. While the
toggle is on, WebApex sends what the desktop 3D window draws (strata_view:
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
are sent again only when a tile changes; the entities are sent once a
simulation step; the HUD when its text does.

Nothing of the 3D view is downloaded until the player asks for it, and if it
can't load the 2D view stays and the toggle says why.
"""

import asyncio
import copy
import time
import traceback
from dataclasses import replace

from apex import Apex
from preponderous.graphik.grid3d import Camera, Scene, Unavailable
from preponderous.graphik.grid3d import web as grid3dweb
from screen.mainMenuScreen import MainMenuScreen
from screen.simulationScreen import SimulationScreen
from strata_view.hud import fitLabels, simulationHud
from strata_view.keys import WEB_CONTROLS_HINT
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
# the HUD's caption sits below the page's 2D/3D button, top right
CAPTION_TOP = 52
# a camera for screens with no board: only its clear colour shows
NO_BOARD_CAMERA = Camera(eye=(0.0, 10.0, 10.0), target=(0.0, 0.0, 0.0))


class BrowserPage:
    """The page around the game under pygbag: its 3D toggle, its size and
    its grid relay (graphik's grid3d.web)."""

    def __init__(self):
        # The page never scrolls. Without this a phone's browser widens it
        # once the 3D canvas shows (to fit pygbag's 50000-pixel-wide
        # measuring element), which pushes the 2D/3D button off screen.
        try:
            document = _platformWindow().document
            for element in (document.documentElement, document.body):
                element.style.overflow = "hidden"
        except Exception as error:  # a page without them: nothing to clip
            print("Page left as it is:", error)

    def wants3D(self):
        return grid3dweb.wants3D()

    def set3D(self, on, reason=""):
        grid3dweb.set3D(on, reason)

    def size(self):
        window = _platformWindow()
        return int(window.innerWidth), int(window.innerHeight)

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


class WebSimulationScreen(SimulationScreen):
    """The 2D simulation screen, counting its simulation's steps, so the 3D
    view knows when the board has changed."""

    def __init__(self, graphik, config):
        super().__init__(graphik, config)
        self.steps = 0

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
        super().__init__()
        self.simulationScreen = WebSimulationScreen(self.graphik, self.config)
        self.alertTool = TextAlertDrawTool()
        self.menuButtons = []
        self.simulationShown = None  # the simulation the controls hint was started for
        self.simulationShownAt = 0.0
        self.frameMs = []
        self.forget3D()

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
        self.forget3D()

    def close3D(self, reason=None):
        """Back to the 2D view; if the 3D view failed, the toggle says why."""
        view, self.view3d = self.view3d, None
        reason = reason or view.failure()
        view.close()
        if reason:
            self.page.set3D(False, unavailableMessage(reason))
            print(unavailableMessage(reason))

    # -- running beside the 2D screens

    async def run(self):
        task = asyncio.ensure_future(self.run3D())
        try:
            await super().run()
        finally:
            task.cancel()

    async def run3D(self):
        while True:
            self.update3D()
            await asyncio.sleep(FRAME_SECONDS)

    def update3D(self):
        """One display frame of the 3D view. Whatever goes wrong in it, the
        2D game goes on, in the 2D view."""
        try:
            self.follow3DToggle()
            if self.view3d is None:
                return
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
                self.forget3D()
            elif event.type == grid3dweb.EVENT_MOUSE_BUTTON_DOWN:
                self.press((event.x, event.y))

    def press(self, position):
        """A click or a tap on the 3D view: what the same press does in 2D."""
        screen = self.currentScreen
        if screen is self.resultsScreen:
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
        items = touchButtons(scaleItems(items, scale), view.width)
        self.menuButtons = [item for item in items if isinstance(item, UiButton)]
        return items

    def menuOverlay(self):
        labels, panels = overlayFrom(self.drawMenu())
        return fitLabels(labels, self.view3d.width), panels

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
        """What the board shows changes only with these."""
        screen, config = self.simulationScreen, self.config
        simulation = screen.simulation
        selected = screen.getSelectedEntity()
        return (id(simulation), screen.steps, simulation.numTicks, len(simulation.entities),
                config.localView, config.localViewSize, config.highlightOldestEntity,
                config.eyesEnabled, None if selected is None else selected.getID())

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
        state = self.simulationState()
        if state != self.sentState:
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
        statsItems = []
        if screen.isDebugEnabled():
            recorder = RecordingGraphik(view.width, view.height)
            screen.displayStats(recorder)
            statsItems = compactStats(recorder.items, view.height)
        alerts = RecordingGraphik(view.width, view.height)
        for alert in screen.getTextAlerts():
            self.alertTool.drawTextAlert(self.alertIn3D(alert), alerts)
        version = RecordingGraphik(view.width / scale, view.height / scale)
        MainMenuScreen(version).drawVersion()  # the 2D screens draw it alike
        paused = screen.isPaused()
        showControls = paused or self.clock() - self.simulationShownAt < CONTROLS_SECONDS
        return simulationHud(
            view.width, view.height, screen.getCaption(), paused,
            statsItems=statsItems, alertItems=alerts.items,
            controls=WEB_CONTROLS_HINT if showControls else (),
            versionItems=scaleItems(version.items, scale), captionTop=CAPTION_TOP)

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

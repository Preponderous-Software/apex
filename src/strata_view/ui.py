"""What the 2D screens draw, recorded rather than drawn.

RecordingGraphik stands in for graphik: a 2D screen (MainMenuScreen,
SetupScreen, ResultsScreen, SimulationScreen's statistics and location
alerts) draws into it with its usual calls, and the 3D window draws the
recorded text, rectangles and buttons as screen-space labels and panels.
A button keeps the 2D screen's own function, so a click on it in 3D runs the
same code a click in 2D does. Pure Python: no pygame display, no Strata.
"""

from dataclasses import dataclass
from typing import Callable, Tuple

Color = Tuple[int, int, int]


@dataclass
class UiText:
    """Text centred on (x, y), as graphik draws it; size is a pygame font size."""

    text: str
    x: float
    y: float
    size: float
    color: Color


@dataclass
class UiRect:
    x: float
    y: float
    width: float
    height: float
    color: Color


@dataclass
class UiButton:
    x: float
    y: float
    width: float
    height: float
    color: Color
    textColor: Color
    textSize: float
    text: str
    function: Callable

    def contains(self, position):
        # exactly the drawn box, as ClickableGraphik counts it
        px, py = position
        return self.x <= px < self.x + self.width and self.y <= py < self.y + self.height


class RecordedDisplay:
    """The parts of a pygame Surface the screens and Simulation ask for."""

    def __init__(self, width, height):
        self.width, self.height = width, height

    def get_size(self):
        return (self.width, self.height)

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    def fill(self, color):
        pass


class RecordingGraphik:
    def __init__(self, width, height):
        self.gameDisplay = RecordedDisplay(width, height)
        self.items = []

    def resize(self, width, height):
        self.gameDisplay.width, self.gameDisplay.height = width, height

    def getGameDisplay(self):
        return self.gameDisplay

    def reset(self):
        self.items = []

    def drawText(self, text, xpos, ypos, size, color):
        self.items.append(UiText(str(text), xpos, ypos, size, tuple(color[:3])))

    def drawRectangle(self, xpos, ypos, width, height, color):
        self.items.append(UiRect(xpos, ypos, width, height, tuple(color[:3])))

    def drawButton(self, xpos, ypos, width, height, colorBox, colorText, sizeText, text, function):
        self.items.append(
            UiButton(xpos, ypos, width, height, tuple(colorBox[:3]), tuple(colorText[:3]),
                     sizeText, str(text), function)
        )

    def buttons(self):
        return [item for item in self.items if isinstance(item, UiButton)]

    def texts(self):
        return [item.text for item in self.items if isinstance(item, UiText)]

    def click(self, position):
        """Runs the function of the button under `position`; returns whether one was hit."""
        for button in self.buttons():
            if button.contains(position):
                button.function()
                return True
        return False


def drawScreen(screen, graphik):
    """Records one frame of a 2D menu screen: what its run loop draws each frame."""
    graphik.reset()
    screen.drawText()
    if hasattr(screen, "drawMenuButtons"):
        screen.drawMenuButtons()
    screen.drawVersion()
    return graphik.items

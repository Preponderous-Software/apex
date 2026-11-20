"""What the 2D screens draw, recorded rather than drawn.

RecordingGraphik stands in for graphik: a 2D screen (MainMenuScreen,
SetupScreen, ResultsScreen, SimulationScreen's statistics and location
alerts) draws into it with its usual calls, and the 3D window draws the
recorded text, rectangles and buttons as screen-space labels and panels.
A button keeps the 2D screen's own function, so a click on it in 3D runs the
same code a click in 2D does. The recorder is graphik's grid3d
ScreenRecorder. Pure Python: no pygame display, no Strata.
"""

from preponderous.graphik.grid3d import (
    RecordedButton as UiButton,
    RecordedDisplay,
    RecordedRect as UiRect,
    RecordedText as UiText,
    ScreenRecorder,
)

__all__ = ["UiText", "UiRect", "UiButton", "RecordedDisplay", "RecordingGraphik", "drawScreen"]


class RecordingGraphik(ScreenRecorder):
    """graphik's ScreenRecorder at the window's size: items are UiText
    (text centred on (x, y), size a pygame font size), UiRect and UiButton
    (which keeps the 2D screen's function; contains() is drawButton's box)."""

    def __init__(self, width, height):
        super().__init__(width, height)


def drawScreen(screen, graphik):
    """Records one frame of a 2D menu screen: what its run loop draws each frame."""
    graphik.reset()
    screen.drawText()
    if hasattr(screen, "drawMenuButtons"):
        screen.drawMenuButtons()
    screen.drawVersion()
    return graphik.items

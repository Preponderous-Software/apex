from contextlib import contextmanager

import pygame
from preponderous.graphik import Graphik


# Where a surface sits in the window: (0, 0) for the window itself, the subsurface's offset for
# the part of the browser's 2D canvas the screens draw on beside a phone's on-screen keys
# (strata_view/web.py). Presses arrive in the window's pixels and are moved into the surface's.
def surfaceOffset(surface):
    try:
        offset = surface.get_abs_offset()
    except (AttributeError, pygame.error):
        return 0, 0
    if not isinstance(offset, tuple) or len(offset) != 2:
        return 0, 0
    return offset


# pygame.mouse.get_pos() in the surface's pixels while Graphik.drawButton reads it for hover and a
# held button (it reads the window's).
@contextmanager
def mouseInSurface(surface):
    left, top = surfaceOffset(surface)
    if (left, top) == (0, 0):
        yield
        return
    getPos = pygame.mouse.get_pos
    pygame.mouse.get_pos = lambda: (getPos()[0] - left, getPos()[1] - top)
    try:
        yield
    finally:
        pygame.mouse.get_pos = getPos


# Graphik, with buttons that also answer a click event rather than only a held mouse button.
#
# Graphik.drawButton fires when it finds the left button held over the button as it draws it, so a
# press shorter than a frame is never seen: a tap on a phone (a press and release delivered
# together) and a quick click in a browser both fall through. A screen hands each
# MOUSEBUTTONDOWN to registerClick() and calls clearClick() once its buttons are drawn; the
# button the click landed on fires once for it, and holding the button down works as before.
class ClickableGraphik(Graphik):
    def __init__(self, gameDisplay):
        super().__init__(gameDisplay)
        self.pendingClick = None

    def registerClick(self, pos):
        left, top = surfaceOffset(self.gameDisplay)
        self.pendingClick = (pos[0] - left, pos[1] - top)

    # Drops a click that landed on no button, so it cannot fire one drawn in a later frame.
    def clearClick(self):
        self.pendingClick = None

    def drawButton(self, xpos, ypos, width, height, colorBox, colorText, sizeText, text, function):
        click = self.pendingClick
        # the same clickable region as Graphik.drawButton: exactly the drawn box, so the left and
        # top edge pixels count and the pixel just past the right or bottom edge does not
        if click is not None and xpos <= click[0] < xpos + width and ypos <= click[1] < ypos + height:
            self.pendingClick = None
            # drawn as usual, but fired once here rather than again by the held-button check
            with mouseInSurface(self.gameDisplay):
                super().drawButton(xpos, ypos, width, height, colorBox, colorText, sizeText, text, lambda: None)
            function()
            return
        with mouseInSurface(self.gameDisplay):
            super().drawButton(xpos, ypos, width, height, colorBox, colorText, sizeText, text, function)

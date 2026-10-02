from lib.graphiklib.graphik import Graphik


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
        self.pendingClick = pos

    # Drops a click that landed on no button, so it cannot fire one drawn in a later frame.
    def clearClick(self):
        self.pendingClick = None

    def drawButton(self, xpos, ypos, width, height, colorBox, colorText, sizeText, text, function):
        click = self.pendingClick
        if click is not None and xpos + width > click[0] > xpos and ypos + height > click[1] > ypos:
            self.pendingClick = None
            # drawn as usual, but fired once here rather than again by the held-button check
            super().drawButton(xpos, ypos, width, height, colorBox, colorText, sizeText, text, lambda: None)
            function()
            return
        super().drawButton(xpos, ypos, width, height, colorBox, colorText, sizeText, text, function)

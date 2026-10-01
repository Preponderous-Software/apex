# This class is responsible for drawing text alerts on the screen.

from lib.graphiklib.graphik import Graphik


class TextAlertDrawTool():
    def __init__(self):
        self.backgroundColor = (255, 255, 255)
        self.backgroundWidth = 250

    def drawTextAlert(self, textAlert, graphik: Graphik):
        numLines = len(textAlert.text)
        backgroundHeight = 20*numLines + 20

        # ensure text will not be drawn outside of the screen
        if textAlert.y + backgroundHeight > graphik.gameDisplay.get_height():
            textAlert.y = graphik.gameDisplay.get_height() - 20*numLines - 20
        if textAlert.x + self.backgroundWidth > graphik.gameDisplay.get_width():
            textAlert.x = graphik.gameDisplay.get_width() - 250
        if textAlert.y < 0:
            textAlert.y = 0
        if textAlert.x < textAlert.size * 6:
            textAlert.x = textAlert.size * 6

        # prepare background at the clamped position so it stays behind the text
        self.prepareBackground(textAlert, graphik, numLines)

        # draw text
        for i in range(0, len(textAlert.text)):
            graphik.drawText(textAlert.text[i], textAlert.x, textAlert.y + 20*i, textAlert.size, textAlert.color)
    
    def prepareBackground(self, textAlert, graphik: Graphik, numLines):
        backgroundX = textAlert.x - textAlert.size * 6
        backgroundY = textAlert.y - textAlert.size
        backgroundHeight = 20*numLines + 20
        graphik.drawRectangle(backgroundX, backgroundY, self.backgroundWidth, backgroundHeight, self.backgroundColor)
        return backgroundHeight
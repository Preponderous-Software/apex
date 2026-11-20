# This file contains the TextAlert class, which is used to display text alerts on the screen.

class TextAlert:
    def __init__(self, x, y, size, color, duration):
        self.x = x
        self.y = y
        self.text = []
        self.size = size
        self.color = color
        self.duration = duration
        # the (column, row) of the location the alert describes, if it describes one: the 3D views
        # draw the alert beside that tile wherever their camera shows it
        self.cell = None
    
    def addLine(self, line):
        self.text.append(line)
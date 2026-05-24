import os
import pygame

from lib.graphiklib.graphik import Graphik
from screen.screenType import ScreenType
from simulation.config import Config

# @author Daniel McCoy Stephenson
class MainMenuScreen:
    def __init__(self, graphik: Graphik):
        self.graphik = graphik
        self.running = True
        self.nextScreen = ScreenType.SETUP_SCREEN
        self.changeScreen = False

    def switchToSetupScreen(self):
        self.nextScreen = ScreenType.SETUP_SCREEN
        self.changeScreen = True

    def quitApplication(self):
        pygame.quit()
        quit()

    def drawText(self):
        x, y = self.graphik.getGameDisplay().get_size()
        xpos = x / 2
        ypos = y / 10
        self.graphik.drawText("Apex", xpos, ypos, 64, (255, 255, 255))
        ypos = y / 3
        # Spell out the available keys instead of "press any key" so we
        # don't have to react to e.g. an accidental letter, and so the
        # affordance matches the buttons below it (Nielsen #4 / #5).
        self.graphik.drawText(
            "press ENTER to start  -  press Q to quit", xpos, ypos, 32, (255, 255, 255)
        )

    def drawMenuButtons(self):
        x, y = self.graphik.getGameDisplay().get_size()
        width = x / 5
        height = y / 10
        xpos = x / 2 - width / 2
        ypos = y / 2 - height / 2
        margin = 10
        backgroundColor = (255, 255, 255)
        self.graphik.drawButton(
            xpos,
            ypos,
            width,
            height,
            backgroundColor,
            (0, 0, 0),
            30,
            "create new sim",
            self.switchToSetupScreen,
        )
        ypos = ypos + height + margin
        self.graphik.drawButton(
            xpos,
            ypos,
            width,
            height,
            backgroundColor,
            (0, 0, 0),
            30,
            "quit",
            self.quitApplication,
        )

    def drawVersion(self):
        if os.path.isfile("version.txt"):
            with open("version.txt", "r") as file:
                version = file.read()

                # display centered at bottom of screen
                self.graphik.drawText(
                    version,
                    self.graphik.getGameDisplay().get_size()[0] / 2,
                    self.graphik.getGameDisplay().get_size()[1] - 10,
                    16,
                    (255, 255, 255),
                )

    def handleKeyDownEvent(self, key):
        if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            self.switchToSetupScreen()
        elif key in (pygame.K_q, pygame.K_ESCAPE):
            self.quitApplication()

    def run(self):
        while not self.changeScreen:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.nextScreen = ScreenType.NONE
                    self.changeScreen = True
                    break
                elif event.type == pygame.KEYDOWN:
                    self.handleKeyDownEvent(event.key)

            self.graphik.getGameDisplay().fill((0, 0, 0))
            self.drawText()
            self.drawMenuButtons()
            self.drawVersion()
            pygame.display.update()
        self.changeScreen = False
        return self.nextScreen

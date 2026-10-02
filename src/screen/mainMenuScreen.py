import asyncio
import os
import sys
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
        self.graphik.drawText(
            "press any key to start!", xpos, ypos, 32, (255, 255, 255)
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
        if sys.platform == "emscripten":
            # a browser tab has nothing to quit to: the button would only leave a dead canvas
            return
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
        self.switchToSetupScreen()

    # Async so it can run in a browser (pygbag): it yields to the event loop once a frame.
    async def run(self):
        while not self.changeScreen:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.nextScreen = ScreenType.NONE
                    self.changeScreen = True
                    break
                elif event.type == pygame.KEYDOWN:
                    self.handleKeyDownEvent(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.graphik.registerClick(event.pos)

            self.graphik.getGameDisplay().fill((0, 0, 0))
            self.drawText()
            self.drawMenuButtons()
            self.graphik.clearClick()
            self.drawVersion()
            pygame.display.update()
            await asyncio.sleep(0)
        self.changeScreen = False
        return self.nextScreen

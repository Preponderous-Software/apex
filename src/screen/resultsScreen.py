import asyncio
import os
import pygame

from lib.graphiklib.graphik import Graphik
from screen.screenType import ScreenType
from simulation.config import Config

# @author Daniel McCoy Stephenson
class ResultsScreen:
    def __init__(self, graphik: Graphik):
        self.graphik = graphik
        self.running = True
        self.nextScreen = ScreenType.SETUP_SCREEN
        self.changeScreen = False
        self.simulation = None

    def switchToSetupScreen(self):
        self.nextScreen = ScreenType.SETUP_SCREEN
        self.changeScreen = True

    def quitApplication(self):
        pygame.quit()
        quit()
    
    def initializeWithSimulation(self, simulation):
        self.simulation = simulation

    def drawText(self):
        x, y = self.graphik.getGameDisplay().get_size()
        xpos = x / 2
        ypos = y / 10
        self.graphik.drawText("Results", xpos, ypos, 64, (255, 255, 255))

        # display size of simulation
        ypos = y / 3
        self.graphik.drawText(
            "simulation size: " + str(self.simulation.getGridSize()), xpos, ypos, 32, (255, 255, 255)
        )
        
        # display number of entities at end of simulation
        ypos = y / 3 + 50
        self.graphik.drawText(
            "entities at end: " + str(self.simulation.getNumEntities()), xpos, ypos, 32, (255, 255, 255)
        )
        
        # display number of ticks
        ypos = y / 3 + 100
        self.graphik.drawText(
            "ticks: " + str(self.simulation.getNumTicks()), xpos, ypos, 32, (255, 255, 255)
        )
        
        # display text "press any key or tap to return to setup"
        ypos = y - y / 10
        self.graphik.drawText(
            "press any key or tap to return to setup", xpos, ypos, 32, (255, 255, 255)
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
                    # a click, or a tap on a phone, which has no key to press
                    self.switchToSetupScreen()

            self.graphik.getGameDisplay().fill((0, 0, 0))
            self.drawText()
            self.drawVersion()
            pygame.display.update()
            await asyncio.sleep(0)
        self.changeScreen = False
        return self.nextScreen

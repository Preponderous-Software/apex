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
        simulationSizeText = "simulation size: " + str(self.simulation.getGridSize()) + "x" + str(self.simulation.getGridSize())
        self.graphik.drawText(
            simulationSizeText, xpos, ypos, 32, (255, 255, 255)
        )
        
        # display number of ticks
        ypos = y / 3 + 50
        lengthOfSimulationText = "length of simulation: " + str(self.simulation.getNumTicks()) + " ticks"
        self.graphik.drawText(
            lengthOfSimulationText, xpos, ypos, 32, (255, 255, 255)
        )
        
        # display number of entities at start of simulation
        ypos = y / 3 + 100
        self.graphik.drawText(
            "entities at start: " + str(self.simulation.getNumEntitiesAtStart()), xpos, ypos, 32, (255, 255, 255)
        )
        
        # display number of entities at end of simulation
        ypos = y / 3 + 150
        self.graphik.drawText(
            "entities at end: " + str(self.simulation.getNumEntities()), xpos, ypos, 32, (255, 255, 255)
        )
        
        # display number of living entities at start of simulation
        ypos = y / 3 + 200
        self.graphik.drawText(
            "living at start: " + str(self.simulation.getNumLivingEntitiesAtStart()), xpos, ypos, 32, (255, 255, 255)
        )
        
        # display number of entities that died
        ypos = y / 3 + 250
        self.graphik.drawText(
            "deaths: " + str(self.simulation.getNumDeaths()), xpos, ypos, 32, (255, 255, 255)
        )
        
        # Prompt a specific key rather than "any key" so an accidental
        # keystroke (autorepeat from the simulation, stray bump of the
        # keyboard) doesn't immediately throw the user back into setup
        # before they've read their results (Nielsen #5: error prevention).
        ypos = y - y / 10
        self.graphik.drawText(
            "press ENTER or SPACE to return to setup", xpos, ypos, 32, (255, 255, 255)
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
            self.drawVersion()
            pygame.display.update()
        self.changeScreen = False
        return self.nextScreen

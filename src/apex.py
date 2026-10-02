import asyncio
import os
import sys

import pygame
from screen.mainMenuScreen import MainMenuScreen
from screen.resultsScreen import ResultsScreen
from screen.screenType import ScreenType
from screen.setupScreen import SetupScreen
from screen.simulationScreen import SimulationScreen
from service.usageReportingService import UsageReportingService
from simulation.config import Config
from ui.clickableGraphik import ClickableGraphik
from ui.gameDisplayFactory import GameDisplayFactory

# @author Daniel McCoy Stephenson
# @since July 31st, 2022
class Apex:
    # found next to this file rather than through the working directory, so the
    # icon loads from the repository root (run.sh), from src/, and in the browser
    # build, whose root is src/ itself
    ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media', 'icon', 'icon.PNG')

    # constructors -----------------------------------------------------------
    def __init__(self):
        pygame.init()
        self.usageReporting = UsageReportingService()
        self.usageReporting.reportStartup()
        self.config = Config()
        gameDisplay = GameDisplayFactory().createGameDisplay(self.config)
        self.__setIcon(self.ICON_PATH)
        self.graphik = ClickableGraphik(gameDisplay)
        self.debug = False
        self.mainMenuScreen = MainMenuScreen(self.graphik)
        self.simulationScreen = SimulationScreen(self.graphik, self.config)
        self.setupScreen = SetupScreen(self.graphik, self.config)
        self.resultsScreen = ResultsScreen(self.graphik)
        self.currentScreen = self.mainMenuScreen

    # public methods ---------------------------------------------------------
    # Runs the application. Async, as is each screen's loop, so the same code runs as a pygbag
    # build in a browser, which needs control back every frame (see src/main.py).
    async def run(self):
        while True:
            result = await self.currentScreen.run()
            if result == ScreenType.MAIN_MENU_SCREEN:
                self.currentScreen = self.mainMenuScreen
            elif result == ScreenType.SETUP_SCREEN:
                self.currentScreen = self.setupScreen
            elif result == ScreenType.SIMULATION_SCREEN:
                self.config.calculateValues()
                self.simulationScreen.initializeSimulation()
                self.usageReporting.reportSimulationStarted()
                self.currentScreen = self.simulationScreen
            elif result == ScreenType.RESULTS_SCREEN:
                self.currentScreen = self.resultsScreen
                self.resultsScreen.initializeWithSimulation(self.simulationScreen.simulation)
            elif result == ScreenType.NONE:
                self.__quitApplication()
            else:
                print("unrecognized screen: " + result)
                self.__quitApplication()

    # private methods --------------------------------------------------------
    # Sets the window icon, skipping it instead of crashing when the file is missing or unreadable.
    def __setIcon(self, path):
        try:
            pygame.display.set_icon(pygame.image.load(path))
        except (pygame.error, FileNotFoundError) as e:
            print("Warning: could not load window icon '" + path + "', continuing without it: " + str(e))

    # Shuts down the application.
    def __quitApplication(self):
        self.usageReporting.close()
        pygame.quit()
        quit()

if __name__ == "__main__":
    apex = Apex()
    asyncio.run(apex.run())
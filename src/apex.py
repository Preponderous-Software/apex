import argparse
import pygame
from lib.graphiklib.graphik import Graphik
from screen.mainMenuScreen import MainMenuScreen
from screen.resultsScreen import ResultsScreen
from screen.screenType import ScreenType
from screen.setupScreen import SetupScreen
from screen.simulationScreen import SimulationScreen
from simulation.config import Config

# @author Daniel McCoy Stephenson
# @since July 31st, 2022
class Apex:
    # constructors -----------------------------------------------------------
    def __init__(self):
        pygame.init()
        self.config = Config()
        self.__initializeGameDisplay()
        pygame.display.set_icon(pygame.image.load('src/media/icon/icon.PNG'))
        self.graphik = Graphik(self.gameDisplay)
        self.debug = False
        self.mainMenuScreen = MainMenuScreen(self.graphik)
        self.simulationScreen = SimulationScreen(self.graphik, self.config)
        self.setupScreen = SetupScreen(self.graphik, self.config)
        self.resultsScreen = ResultsScreen(self.graphik)
        self.currentScreen = self.mainMenuScreen

    # public methods ---------------------------------------------------------
    # Runs the application.
    def run(self):
        while True:
            result = self.currentScreen.run()
            if result == ScreenType.MAIN_MENU_SCREEN:
                self.currentScreen = self.mainMenuScreen
            elif result == ScreenType.SETUP_SCREEN:
                self.currentScreen = self.setupScreen
            elif result == ScreenType.SIMULATION_SCREEN:
                self.config.calculateValues()
                self.simulationScreen.initializeSimulation()
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
    def __initializeGameDisplay(self):
        if self.config.fullscreen:
            self.gameDisplay = pygame.display.set_mode((self.config.displayWidth, self.config.displayHeight), pygame.FULLSCREEN)
        else:
            self.gameDisplay = pygame.display.set_mode((self.config.displayWidth, self.config.displayHeight), pygame.RESIZABLE)

    # Shuts down the application.
    def __quitApplication(self):
        pygame.quit()
        quit()

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Apex Ecosystem Simulator')
    parser.add_argument('--text', action='store_true', 
                        help='Run simulation in text mode (no GUI)')
    args = parser.parse_args()
    
    if args.text:
        # Run in text mode
        from textSimulationRunner import TextSimulationRunner
        runner = TextSimulationRunner()
        runner.run()
    else:
        # Run in pygame GUI mode (default)
        apex = Apex()
        apex.run()
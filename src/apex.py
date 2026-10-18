import argparse
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
from simulation.usdRecording import REQUIREMENTS_HINT, UsdRecording
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
    def __init__(self, recordPath=None):
        # --record <path>: the first simulation is recorded to this .usda file (usdRecording.py)
        self.recordPath = recordPath
        self.recording = None
        self.recordingFinished = False
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
            if self.currentScreen is self.simulationScreen:
                self.__finishRecording()
            if result == ScreenType.MAIN_MENU_SCREEN:
                self.currentScreen = self.mainMenuScreen
            elif result == ScreenType.SETUP_SCREEN:
                self.currentScreen = self.setupScreen
            elif result == ScreenType.SIMULATION_SCREEN:
                self.config.calculateValues()
                self.simulationScreen.initializeSimulation()
                self.__startRecording()
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
    # Starts recording the simulation that is about to run, if --record was given and the first
    # simulation has not been recorded yet: one file holds one simulation's history.
    def __startRecording(self):
        if self.recordPath is None or self.recordingFinished:
            return
        self.recording = UsdRecording(self.recordPath, self.config.gridSize)
        self.simulationScreen.setRecording(self.recording)

    # Writes the recording once its simulation has ended (or the game is left).
    def __finishRecording(self):
        if self.recording is None:
            return
        self.simulationScreen.setRecording(None)
        path = self.recording.close()
        print("Recorded " + str(self.recording.getTicksRecorded()) + " ticks to " + str(path))
        self.recording = None
        self.recordingFinished = True

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

def parseArguments(argv=None):
    parser = argparse.ArgumentParser(description="Apex: a food-chain simulation.")
    parser.add_argument("--record", metavar="PATH",
                        help="record the first simulation as a time-sampled OpenUSD stage (.usda); "
                             "needs the optional usd-recorder package (" + REQUIREMENTS_HINT + ")")
    parser.add_argument("--text", action="store_true",
                        help="run in the terminal (curses) instead of a pygame window")
    return parser.parse_args(argv)

# Runs the text UI (--text): a simulation in the terminal, reported to trace the same way as one
# in the window. No pygame window is opened. curses is imported only here: Python on Windows does
# not ship it, and the browser build has no terminal, so neither should need it to start.
def runTextMode():
    try:
        from textSimulationRunner import TextSimulationRunner
    except ImportError as e:
        sys.exit("--text needs the curses module, which this Python lacks (" + str(e) + "); "
                 "on Windows, pip install windows-curses")
    usageReporting = UsageReportingService()
    usageReporting.reportStartup()
    try:
        TextSimulationRunner(onSimulationStarted=usageReporting.reportSimulationStarted).run()
    finally:
        usageReporting.close()

if __name__ == "__main__":
    arguments = parseArguments()
    if arguments.text:
        if arguments.record is not None:
            sys.exit("--record is not supported with --text")
        runTextMode()
        sys.exit(0)
    if arguments.record is not None and not UsdRecording.isAvailable():
        sys.exit("--record needs the optional usd-recorder package: " + REQUIREMENTS_HINT)
    apex = Apex(arguments.record)
    asyncio.run(apex.run())
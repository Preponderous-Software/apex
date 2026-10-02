import asyncio
import os
import pygame

from lib.graphiklib.graphik import Graphik
from screen.screenType import ScreenType
from simulation.config import Config

# @author Daniel McCoy Stephenson
class SetupScreen:
    # constructors -----------------------------------------------------------
    def __init__(self, graphik: Graphik, config: Config):
        self.graphik = graphik
        self.config = config
        self.running = True
        self.nextScreen = ScreenType.SIMULATION_SCREEN
        self.changeScreen = False

    def switchToSimulationScreen(self):
        self.nextScreen = ScreenType.SIMULATION_SCREEN
        self.changeScreen = True
    
    def switchToMainMenuScreen(self):
        self.nextScreen = ScreenType.MAIN_MENU_SCREEN
        self.changeScreen = True

    def quitApplication(self):
        pygame.quit()
        quit()

    def drawText(self):
        x, y = self.graphik.getGameDisplay().get_size()
        xpos = x / 2
        ypos = y / 10
        self.graphik.drawText("Setup", xpos, ypos, 64, (255, 255, 255))

    def drawMenuButtons(self):
        x, y = self.graphik.getGameDisplay().get_size()
        width = x / 5
        height = y / 10
        
        # draw button in top left to return to main menu
        xpos = x / 10
        ypos = y / 10
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
            "main menu",
            self.switchToMainMenuScreen,
        )
        
        # draw button at bottom center to start simulation
        xpos = x / 2 - width / 2
        ypos = y - height - y / 10
        self.graphik.drawButton(
            xpos,
            ypos,
            width,
            height,
            backgroundColor,
            (0, 0, 0),
            30,
            "start simulation",
            self.switchToSimulationScreen,
        )
    
        self.drawIntegerConfigOptionSetter(x, y, "gridSize", self.config.gridSize, self.decreaseGridSize, self.increaseGridSize)
        
        self.drawIntegerConfigOptionSetter(x, y - 150, "grassFactor", self.config.grassFactor, self.decreaseGrassFactor, self.increaseGrassFactor)
        
        self.drawIntegerConfigOptionSetter(x, y - 300, "grassGrowTime", self.config.grassGrowTime, self.decreaseGrassGrowTime, self.increaseGrassGrowTime)
    
    def drawIntegerConfigOptionSetter(self, x, y, configOptionName, configOptionValue, decreaseFunction, increaseFunction):
        # given x and y, draw text and buttons next to the text
        textSize = 30
        self.graphik.drawText(configOptionName + ": " + str(configOptionValue), x / 2, y / 2, textSize, (255, 255, 255))
        
        width = textSize
        height = textSize
        margin = 10
        backgroundColor = (255, 255, 255)
        
        # draw buttons to decrease and increase grid size
        xpos = x / 2 - width - margin
        ypos = y / 2 + margin
        self.graphik.drawButton(
            xpos,
            ypos,
            width,
            height,
            backgroundColor,
            (0, 0, 0),
            30,
            "-",
            decreaseFunction,
        )
        
        xpos = x / 2 + margin
        self.graphik.drawButton(
            xpos,
            ypos,
            width,
            height,
            backgroundColor,
            (0, 0, 0),
            30,
            "+",
            increaseFunction,
        )
        
    def decreaseGridSize(self):
        self.config.gridSize -= 1
        if self.config.gridSize < 16:
            self.config.gridSize = 16
            
    def increaseGridSize(self):
        self.config.gridSize += 1
        if self.config.gridSize > 64:
            self.config.gridSize = 64
    
    def decreaseGrassFactor(self):
        self.config.grassFactor -= 1
        if self.config.grassFactor < 1:
            self.config.grassFactor = 1
            
    def increaseGrassFactor(self):
        self.config.grassFactor += 1
        if self.config.grassFactor > 10:
            self.config.grassFactor = 10

    def decreaseGrassGrowTime(self):
        self.config.grassGrowTime -= 10
        if self.config.grassGrowTime < 10:
            self.config.grassGrowTime = 10
            
    def increaseGrassGrowTime(self):
        self.config.grassGrowTime += 10
        if self.config.grassGrowTime > 1000:
            self.config.grassGrowTime = 1000

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

    # Async so it can run in a browser (pygbag): it yields to the event loop once a frame.
    async def run(self):
        while not self.changeScreen:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.nextScreen = ScreenType.NONE
                    self.changeScreen = True
                    break
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

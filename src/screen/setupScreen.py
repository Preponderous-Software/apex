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
        
        y = y / 2
        self.drawIntegerConfigOptionSetter(x, y, "gridSize", self.config.gridSize, self.decreaseGridSize, self.increaseGridSize)
        y += 150
        self.drawIntegerConfigOptionSetter(x, y, "waterFactor", self.config.waterFactor, self.decreaseWaterFactor, self.increaseWaterFactor)
        y += 150
        self.drawIntegerConfigOptionSetter(x, y, "rockFactor", self.config.rockFactor, self.decreaseRockFactor, self.increaseRockFactor)
        y += 150
        self.drawIntegerConfigOptionSetter(x, y, "grassFactor", self.config.grassFactor, self.decreaseGrassFactor, self.increaseGrassFactor)
        y += 150
        self.drawIntegerConfigOptionSetter(x, y, "grassGrowTime", self.config.grassGrowTime, self.decreaseGrassGrowTime, self.increaseGrassGrowTime)

        # Place "randomize" mirroring the main-menu button position so the
        # two header affordances feel intentional. The original (0,0)
        # placement made it look like a stray debug control and gave no
        # spatial cue that it affected the config options below.
        screenX, screenY = self.graphik.getGameDisplay().get_size()
        randomizeWidth = screenX / 5
        randomizeHeight = screenY / 10
        randomizeX = screenX - randomizeWidth - screenX / 10
        randomizeY = screenY / 10
        self.graphik.drawButton(
            randomizeX,
            randomizeY,
            randomizeWidth,
            randomizeHeight,
            backgroundColor,
            (0, 0, 0),
            30,
            "randomize",
            self.randomizeConfig,
        )
        
    def randomizeConfig(self):
        # Mutate the shared Config in place so changes propagate to the rest
        # of the app — assigning a new Config() would drop the reference held
        # by Apex/Simulation/etc and silently do nothing visible to the user.
        fresh = Config()
        for attr, value in vars(fresh).items():
            setattr(self.config, attr, value)
    
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
    
    def decreaseWaterFactor(self):
        self.config.waterFactor -= 1
        if self.config.waterFactor < 1:
            self.config.waterFactor = 1
        
    def increaseWaterFactor(self):
        self.config.waterFactor += 1
        if self.config.waterFactor > 5:
            self.config.waterFactor = 5
    
    def decreaseRockFactor(self):
        self.config.rockFactor -= 1
        if self.config.rockFactor < 1:
            self.config.rockFactor = 1
            
    def increaseRockFactor(self):
        self.config.rockFactor += 1
        if self.config.rockFactor > 5:
            self.config.rockFactor = 5
    
    def decreaseGrassFactor(self):
        self.config.grassFactor -= 1
        if self.config.grassFactor < 1:
            self.config.grassFactor = 1
            
    def increaseGrassFactor(self):
        self.config.grassFactor += 1
        if self.config.grassFactor > 5:
            self.config.grassFactor = 5

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

    def run(self):
        while not self.changeScreen:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.nextScreen = ScreenType.NONE
                    self.changeScreen = True
                    break
                # Keyboard shortcuts for users who don't want to mouse over
                # to the buttons (Nielsen #7: flexibility & efficiency of
                # use). ESC mirrors the typical "back" affordance, and
                # ENTER mirrors "start simulation".
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.switchToMainMenuScreen()
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.switchToSimulationScreen()

            self.graphik.getGameDisplay().fill((0, 0, 0))
            self.drawText()
            self.drawMenuButtons()
            self.drawVersion()
            pygame.display.update()
        self.changeScreen = False
        return self.nextScreen

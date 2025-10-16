import os
import time
import pygame

from entity.chicken import Chicken
from entity.cow import Cow
from entity.fox import Fox
from entity.grass import Grass
from entity.livingEntity import LivingEntity
from entity.pig import Pig
from entity.rabbit import Rabbit
from entity.wolf import Wolf
from lib.graphiklib.graphik import Graphik
from screen.screenType import ScreenType
from simulation.config import Config
from simulation.simulation import Simulation
from simulation.simulationController import SimulationController
from ui.textAlertDrawTool import TextAlertDrawTool
from ui.textAlertFactory import TextAlertFactory

# @author Daniel McCoy Stephenson
class SimulationScreen:
    # constructors -----------------------------------------------------------
    def __init__(self, graphik: Graphik, config: Config):
        self.__graphik = graphik
        self.__config = config
        self.__nextScreen = ScreenType.RESULTS_SCREEN
        self.__changeScreen = False
        self.__controller = None
        self.__textAlerts = []
        self.__textAlertFactory = TextAlertFactory()
        self.__textAlertDrawTool = TextAlertDrawTool()
        self.__selectedEntity = None
    
    # public methods ---------------------------------------------------------
    # Invokes the simulation screen loop.
    def run(self):
        while not self.__changeScreen:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.__nextScreen = ScreenType.NONE
                    self.__changeScreen = True
                    break
                elif event.type == pygame.KEYDOWN:
                    self.__handleKeyDownEvent(event.key)
                elif event.type == pygame.VIDEORESIZE:
                    self.simulation.initializeLocationWidthAndHeight()
                elif event.type == pygame.MOUSEBUTTONDOWN and self.__config.localView == False:
                    self.__handleMouseClickEvent(event.pos)
            
            # Update simulation through controller
            self.__controller.update()
            
            self.__graphik.gameDisplay.fill(self.__config.black)
            if self.simulation.getNumLivingEntities() != 0:
                if self.__config.localView and self.__selectedEntity != None:
                    self.__drawAreaAroundSelectedEntity()
                else:
                    self.__drawEnvironment()

                if self.__controller.isDebug():
                    self.__displayStats()
            
            self.__drawTextAlerts()
            
            # if selected entity is no longer alive, deselect it
            if self.__selectedEntity != None and not self.simulation.environment.isEntityPresent(self.__selectedEntity):
                self.__selectedEntity = None
                
                # if local view, switch back to global view
                if self.__config.localView:
                    self.__config.localView = False

            self.__drawVersion()
            pygame.display.update()
            if (self.__config.limitTickSpeed):
                time.sleep((self.__config.maxTickSpeed - self.__config.tickSpeed)/self.__config.maxTickSpeed)
            
            if self.__controller.isPaused():
                x, y = self.__graphik.gameDisplay.get_size()
                self.__graphik.drawText("PAUSED", x/2, y/2, 50, self.__config.black)

            if self.__controller.shouldEnd():
                time.sleep(1)
                self.__controller.quit()
                if self.__config.randomizeGridSizeUponRestart:
                    self.__config.randomizeGridSize()
                    self.__config.randomizeGrassGrowTime()
                    self.__config.calculateValues()
                self.__nextScreen = ScreenType.RESULTS_SCREEN
                self.__changeScreen = True

        self.__changeScreen = False
        return self.__nextScreen
    
    def initializeSimulation(self):
        name = "Simulation"
        self.simulation = Simulation(name, self.__config, self.__graphik.gameDisplay)
        # Create controller to manage gameplay actions
        self.__controller = SimulationController(self.simulation, self.__config)
        self.simulation.generateInitialEntities()
        self.simulation.placeInitialEntitiesInEnvironment()
        self.simulation.environment.printInfo()
        self.__initializeCaption()

    # private methods --------------------------------------------------------
    def __initializeCaption(self):
        caption = "Apex - " + self.simulation.name + " - " + str(self.simulation.environment.getGrid().getColumns()) + "x" + str(self.simulation.environment.getGrid().getRows())
        if self.__config.muted:
            caption += " (muted)"
        pygame.display.set_caption(caption)

    def __drawVersion(self):
        if os.path.isfile("version.txt"):
            with open("version.txt", "r") as file:
                version = file.read()

                # display centered at bottom of screen
                self.__graphik.drawText(
                    version,
                    self.__graphik.getGameDisplay().get_size()[0] / 2,
                    self.__graphik.getGameDisplay().get_size()[1] - 10,
                    16,
                    (255, 255, 255),
                )

    # Draws the environment that belongs to the simulation in its entirety.
    def __drawEnvironment(self):
        for locationId in self.simulation.environment.getGrid().getLocations():
            location = self.simulation.environment.getGrid().getLocations()[locationId]
            self.__drawLocation(location, location.getX() * self.simulation.locationWidth - 1, location.getY() * self.simulation.locationHeight - 1, self.simulation.locationWidth + 2, self.simulation.locationHeight + 2)

    # Draws a location at a specified position.
    def __drawLocation(self, location, xPos, yPos, width, height):
        color = self.__getColorOfLocation(location)
        self.__graphik.drawRectangle(xPos, yPos, width, height, color)
        if self.__config.eyesEnabled and location != -1 and self.__locationContainsLivingEntity(location):
            eyeSizeFactor = 0.25
            pupilSizeFactor = 0.5
            self.__drawEyes(xPos, yPos, width, height, eyeSizeFactor, pupilSizeFactor)

    # Returns the color that a location should be displayed as.
    def __getColorOfLocation(self, location):
        if location == -1:
            color = self.__config.black
        else:
            color = self.__config.brown
            if location.getNumEntities() > 0:
                topEntityId = list(location.getEntities().keys())[-1]
                topEntity = location.getEntities()[topEntityId]
                oldestLivingEntityId = self.simulation.livingEntityIds[0]
                oldestLivingEntity = self.simulation.entities[oldestLivingEntityId]
                if self.__config.highlightOldestEntity and topEntity.getID() == oldestLivingEntity.getID():
                    color = self.__config.highlightColor
                else:
                    color = topEntity.getColor()
        return color

    def __locationContainsLivingEntity(self, location):
        if location.getNumEntities() == 0:
            return False
        topEntityId = list(location.getEntities().keys())[-1]
        topEntity = location.getEntities()[topEntityId]
        return location.getNumEntities() > 0 and isinstance(topEntity, LivingEntity)

    def __drawEyes(self, xPos, yPos, width, height, eyeSizeFactor, pupilSizeFactor):
        # draw eyes
        leftEyeXPos = xPos + width/8
        leftEyeYPos = yPos + height/4
        leftEyeWidth = width*eyeSizeFactor
        leftEyeHeight = height*eyeSizeFactor
        self.__graphik.drawRectangle(leftEyeXPos, leftEyeYPos, leftEyeWidth, leftEyeHeight, self.__config.white)
        
        rightEyeXPos = xPos + width/2
        rightEyeYPos = yPos + height/4
        rightEyeWidth = width*eyeSizeFactor
        rightEyeHeight = height*eyeSizeFactor
        self.__graphik.drawRectangle(rightEyeXPos, rightEyeYPos, rightEyeWidth, rightEyeHeight, self.__config.white)
        
        # draw pupils            
        leftPupilXPos = leftEyeXPos + leftEyeWidth/4
        leftPupilYPos = leftEyeYPos + leftEyeHeight/4
        leftPupilWidth = leftEyeWidth*pupilSizeFactor
        leftPupilHeight = leftEyeHeight*pupilSizeFactor
        self.__graphik.drawRectangle(leftPupilXPos, leftPupilYPos, leftPupilWidth, leftPupilHeight, self.__config.black)
        
        rightPupilXPos = rightEyeXPos + rightEyeWidth/4
        rightPupilYPos = rightEyeYPos + rightEyeHeight/4
        rightPupilWidth = rightEyeWidth*pupilSizeFactor
        rightPupilHeight = rightEyeHeight*pupilSizeFactor
        self.__graphik.drawRectangle(rightPupilXPos, rightPupilYPos, rightPupilWidth, rightPupilHeight, self.__config.black)

    # Draws the immediate area around the selected entity.
    def __drawAreaAroundSelectedEntity(self):
        locationID = self.__selectedEntity.getLocationID()
        grid = self.simulation.environment.getGrid()
        location = grid.getLocation(locationID)
        x, y = self.__graphik.gameDisplay.get_size()
        width = x/(self.__config.localViewSize*2 + 1)
        height = y/(self.__config.localViewSize*2 + 1)
        xpos = width*self.__config.localViewSize
        ypos = height*self.__config.localViewSize
        yBackup = ypos
        self.__drawRow(location, grid, xpos, ypos, width, height)
        self.__drawRowsAboveLocation(location, grid, xpos, ypos, width, height)
        ypos = yBackup
        self.__drawRowsBelowLocation(location, grid, xpos, ypos, width, height)

    # Draws locations to the left of a given location.
    def __drawLocationsToTheLeftOfLocation(self, location, grid, xpos, ypos, width, height):
        tempLoc = location
        while tempLoc != -1:
            xpos = xpos - width
            ypos = ypos
            self.__drawLocation(grid.getLeft(tempLoc), xpos, ypos, width, height)
            tempLoc = grid.getLeft(tempLoc)
    
    # Draws locations to the right of a given location.
    def __drawLocationsToTheRightOfLocation(self, location, grid, xpos, ypos, width, height):
        tempLoc = location
        while tempLoc != -1:
            xpos = xpos + width
            ypos = ypos
            self.__drawLocation(grid.getRight(tempLoc), xpos, ypos, width, height)
            tempLoc = grid.getRight(tempLoc)
    
    # Draws a row of locations starting at a given location.
    def __drawRow(self, location, grid, xpos, ypos, width, height):
        self.__drawLocation(location, xpos, ypos, width, height)
        xBackup = xpos
        self.__drawLocationsToTheLeftOfLocation(location, grid, xpos, ypos, width, height)
        xpos = xBackup
        self.__drawLocationsToTheRightOfLocation(location, grid, xpos, ypos, width, height)
    
    # Draws rows of locations starting above a given location.
    def __drawRowsAboveLocation(self, location, grid, xpos, ypos, width, height):
        nextLocation = grid.getUp(location)
        while nextLocation != -1:
            ypos = ypos - height
            self.__drawRow(nextLocation, grid, xpos, ypos, width, height)
            nextLocation = grid.getUp(nextLocation)

    # Draws rows of locations starting below a given location.
    def __drawRowsBelowLocation(self, location, grid, xpos, ypos, width, height):
        nextLocation = grid.getDown(location)
        while nextLocation != -1:
            ypos = ypos + height
            self.__drawRow(nextLocation, grid, xpos, ypos, width, height)
            nextLocation = grid.getDown(nextLocation)

    def __drawTextAlerts(self):
        for textAlert in self.__textAlerts:
            self.__textAlertDrawTool.drawTextAlert(textAlert, self.__graphik)
            textAlert.duration -= 1
            if textAlert.duration == 0:
                self.__textAlerts.remove(textAlert)

    # Draws some statistics to the screen, which are updated each tick. This can be laggy.
    def __displayStats(self):
        startingX = 100
        startingY = 10
        text = []
        if self.__config.limitTickSpeed:
            self.__addStatToText(text, "Tick Speed:", str(self.__config.tickSpeed))
        self.__addStatToText(text, "Num Ticks:", str(self.simulation.numTicks))
        self.__addStatToText(text, "Entities:", str(len(self.simulation.entities)))
        self.__addStatToText(text, "Living Entities:", str(self.simulation.getNumLivingEntities()))
        self.__addStatToText(text, "Grass:", str(self.simulation.getNumberOfEntitiesOfType(Grass)))
        self.__addStatToText(text, "Excrement:", str(self.simulation.getNumExcrement()))
        self.__addStatToText(text, "Chickens:", str(self.simulation.getNumberOfLivingEntitiesOfType(Chicken)))
        self.__addStatToText(text, "Pigs:", str(self.simulation.getNumberOfLivingEntitiesOfType(Pig)))
        self.__addStatToText(text, "Cows:", str(self.simulation.getNumberOfLivingEntitiesOfType(Cow)))
        self.__addStatToText(text, "Wolves:", str(self.simulation.getNumberOfLivingEntitiesOfType(Wolf)))
        self.__addStatToText(text, "Foxes:", str(self.simulation.getNumberOfLivingEntitiesOfType(Fox)))
        self.__addStatToText(text, "Rabbits:", str(self.simulation.getNumberOfLivingEntitiesOfType(Rabbit)))

        buffer = self.__config.textSize

        for i in range(0, len(text)):
            self.__graphik.drawText(text[i], startingX, startingY + buffer*i, self.__config.textSize, self.__config.black)

    def __addStatToText(self, text, key, value):
        text.append(key)
        text.append(value)
        text.append("")

    # Defines the controls of the application.
    def __handleKeyDownEvent(self, key):
        # Use controller for gameplay actions
        if key == pygame.K_d:
            self.__controller.toggleDebug()
        if key == pygame.K_q:
            self.__controller.quit()
        if key == pygame.K_r:
            self.__controller.quit()
            self.__nextScreen = ScreenType.RESULTS_SCREEN
            self.__changeScreen = True
        if key == pygame.K_c:
            self.__controller.spawnChicken()
        if key == pygame.K_p:
            self.__controller.spawnPig()
        if key == pygame.K_k:
            self.__controller.spawnCow()
        if key == pygame.K_w:
            self.__controller.spawnWolf()
        if key == pygame.K_f:
            self.__controller.spawnFox()
        if key == pygame.K_b:
            self.__controller.spawnRabbit()
        if key == pygame.K_RIGHTBRACKET:
            self.__controller.increaseTickSpeed()
        if key == pygame.K_LEFTBRACKET:
            self.__controller.decreaseTickSpeed()
        if key == pygame.K_l:
            self.__controller.toggleTickSpeedLimit()
        if key == pygame.K_SPACE or key == pygame.K_ESCAPE:
            self.__controller.togglePause()
        
        # UI-specific controls (not in controller)
        if key == pygame.K_v:
            if self.__config.localView:
                self.__config.localView = False
            else:
                self.__config.localView = True
        if key == pygame.K_h:
            if self.__config.highlightOldestEntity:
                self.__config.highlightOldestEntity = False
            else:
                self.__config.highlightOldestEntity = True
        if key == pygame.K_UP:
            if self.__config.localViewSize < self.__config.maxLocalViewSize:
                self.__config.localViewSize += 1
        if key == pygame.K_DOWN:
            if self.__config.localViewSize > 1:
                self.__config.localViewSize -= 1
        if key == pygame.K_F11:
            if self.__config.fullscreen:
                self.__config.fullscreen = False
            else:
                self.__config.fullscreen = True
            self.initializeGameDisplay()
        if key == pygame.K_m:
            if self.__config.muted:
                self.__config.muted = False
            else:
                self.__config.muted = True
            self.__initializeCaption()
        if key == pygame.K_e:
            if self.__config.eyesEnabled:
                self.__config.eyesEnabled = False
            else:
                self.__config.eyesEnabled = True

    def __retrieveLocationAtMousePosition(self, pos):
        x, y = pos
        grid = self.simulation.environment.getGrid()
        locationWidth = self.simulation.locationWidth
        locationHeight = self.simulation.locationHeight
        locationX = x // locationWidth
        locationY = y // locationHeight
        location = grid.getLocationByCoordinates(locationX, locationY)
        return location
                
    def __handleMouseClickEvent(self, pos):
        location = self.__retrieveLocationAtMousePosition(pos)
        if location != -1:
            self.__printLocationInfoToConsole(location)
            self.__createTextAlertForLocationInfo(location)
            pygame.display.update()
            if location.getNumEntities() > 0:
                topEntity = location.getEntities()[list(location.getEntities().keys())[-1]]
                if isinstance(topEntity, LivingEntity):
                    self.__selectedEntity = topEntity
                else:
                    self.__selectedEntity = None

    def __createTextAlertForLocationInfo(self, location):
        newAlert = self.__textAlertFactory.createTextAlertForLocationInfo(location, self.simulation, self.__config)
        self.__textAlerts.append(newAlert)

    def __printLocationInfoToConsole(self, location):
        if location != -1:
            print("")
            print("=== Location (" + str(location.getX()) + ", " + str(location.getY()) + ") ===")
            print("Number of entities: " + str(location.getNumEntities()))
            entityNames = []
            for entityId in location.getEntities():
                entity = location.getEntities()[entityId]
                entityNames.append(entity.getName())
            # print occurrences
            for entityName in set(entityNames):
                print(entityName + ": " + str(entityNames.count(entityName)))
            print("")
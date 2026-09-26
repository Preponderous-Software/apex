import pygame

# Creates the game display in the mode that Config.fullscreen calls for. Shared by Apex at startup
# and by SimulationScreen when F11 toggles Config.fullscreen, so that the two cannot drift apart.
# The non-fullscreen mode is RESIZABLE so that leaving fullscreen does not leave the user with a
# fixed-size window.
class GameDisplayFactory:

    def createGameDisplay(self, config):
        size = (config.displayWidth, config.displayHeight)
        if config.fullscreen:
            return pygame.display.set_mode(size, pygame.FULLSCREEN)
        return pygame.display.set_mode(size, pygame.RESIZABLE)

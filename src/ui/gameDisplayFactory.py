import sys

import pygame

# Creates the game display in the mode that Config.fullscreen calls for. Shared by Apex at startup
# and by SimulationScreen when F11 toggles Config.fullscreen, so that the two cannot drift apart.
# The non-fullscreen mode is RESIZABLE so that leaving fullscreen does not leave the user with a
# fixed-size window.
#
# In a browser (the pygbag build) the page owns the window: a RESIZABLE display is given whatever
# square the page picks, which squeezes the 1280x720 layout, so the display there is the
# configured size, scaled to fit the page by the browser.
class GameDisplayFactory:

    def createGameDisplay(self, config):
        size = (config.displayWidth, config.displayHeight)
        if sys.platform == "emscripten":
            gameDisplay = pygame.display.set_mode(size)
            self.__fitBrowserCanvas()
            return gameDisplay
        if config.fullscreen:
            return pygame.display.set_mode(size, pygame.FULLSCREEN)
        return pygame.display.set_mode(size, pygame.RESIZABLE)

    # pygbag sizes the page's canvas before the display exists and only fits it to the display's
    # aspect ratio again when the page is resized, so a resize is announced once the display is set.
    def __fitBrowserCanvas(self):
        try:
            import platform as browser  # pygbag's module for reaching the page

            browser.window.eval("window.dispatchEvent(new Event('resize'))")
        except Exception as e:
            print("Warning: could not fit the canvas to the page: " + str(e))

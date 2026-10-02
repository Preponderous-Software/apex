import os
import random
import sys
import pygame

# src/media/sounds, found next to this package rather than through the working directory,
# so the sounds load wherever the game is started from, the browser build included
SOUNDS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "media", "sounds")


# Each sound is shipped twice: the original .wav, and an .ogg (Vorbis) copy for the browser
# (pygbag) build, whose audio cannot play .wav and whose packager refuses a .wav without one.
def soundPath(name, platform=None):
    extension = "ogg" if (platform or sys.platform) == "emscripten" else "wav"
    return os.path.join(SOUNDS_DIR, name + "." + extension)


#  @author Daniel McCoy Stephenson
#  @since August 5th, 2022
class SoundService:
    REPRODUCE_SOUND_PATH = soundPath("pop")
    DEATH_SOUND_PATH = soundPath("pain")

    def __init__(self):
        self.reproduceSoundEffect = self.__loadSoundEffect(self.REPRODUCE_SOUND_PATH)
        self.deathSoundEffect = self.__loadSoundEffect(self.DEATH_SOUND_PATH)

        self.volumeFactor = 0.01
        self.minVolume = 1
        self.maxVolume = 10

    def playReproduceSoundEffect(self):
        self.__playSoundEffect(self.reproduceSoundEffect)

    def playDeathSoundEffect(self):
        self.__playSoundEffect(self.deathSoundEffect)

    # Returns None instead of raising when the file is missing or the mixer is unavailable.
    def __loadSoundEffect(self, path):
        try:
            return pygame.mixer.Sound(path)
        except (pygame.error, FileNotFoundError) as e:
            print("Warning: could not load sound effect '" + path + "', sound will be disabled for it: " + str(e))
            return None

    def __playSoundEffect(self, soundEffect):
        if soundEffect is None:
            return
        soundEffect.set_volume(self.volumeFactor * random.randrange(self.minVolume, self.maxVolume))
        pygame.mixer.Sound.play(soundEffect)

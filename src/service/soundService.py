import random
import pygame


#  @author Daniel McCoy Stephenson
#  @since August 5th, 2022
class SoundService:
    REPRODUCE_SOUND_PATH = "src/media/sounds/pop.wav"
    DEATH_SOUND_PATH = "src/media/sounds/pain.wav"

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

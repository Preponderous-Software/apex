from types import SimpleNamespace
from unittest.mock import MagicMock

import pygame
import pytest

from service import soundService
from service.soundService import SoundService


# helper methods -------------------------------------------------------------
def usePygameStub(monkeypatch, sound):
    sound = MagicMock(side_effect=sound)
    stub = SimpleNamespace(error=pygame.error, mixer=SimpleNamespace(Sound=sound))
    monkeypatch.setattr(soundService, "pygame", stub)
    return stub

def loadAll(path):
    return MagicMock()

def failFor(missingPath, error):
    def sound(path):
        if missingPath is None or path == missingPath:
            raise error
        return MagicMock()
    return sound

LOAD_ERRORS = [FileNotFoundError("missing"), pygame.error("mixer not initialized")]

# loading tests --------------------------------------------------------------
def test_loadsBothSoundEffectsWhenAssetsArePresent(monkeypatch):
    usePygameStub(monkeypatch, loadAll)

    service = SoundService()

    assert service.reproduceSoundEffect is not None
    assert service.deathSoundEffect is not None

@pytest.mark.parametrize("error", LOAD_ERRORS)
def test_missingReproduceSoundDoesNotCrashConstruction(monkeypatch, error):
    usePygameStub(monkeypatch, failFor(SoundService.REPRODUCE_SOUND_PATH, error))

    service = SoundService()

    assert service.reproduceSoundEffect is None
    assert service.deathSoundEffect is not None

@pytest.mark.parametrize("error", LOAD_ERRORS)
def test_missingDeathSoundDoesNotCrashConstruction(monkeypatch, error):
    usePygameStub(monkeypatch, failFor(SoundService.DEATH_SOUND_PATH, error))

    service = SoundService()

    assert service.reproduceSoundEffect is not None
    assert service.deathSoundEffect is None

def test_uninitializedMixerDoesNotCrashConstruction(monkeypatch):
    monkeypatch.setattr(soundService, "pygame", pygame)
    pygame.mixer.quit()

    service = SoundService()

    assert service.reproduceSoundEffect is None
    assert service.deathSoundEffect is None

# playback tests -------------------------------------------------------------
def test_playingAnUnloadedSoundEffectIsANoOp(monkeypatch):
    stub = usePygameStub(monkeypatch, failFor(None, pygame.error("no audio device")))
    service = SoundService()

    service.playReproduceSoundEffect()
    service.playDeathSoundEffect()

    stub.mixer.Sound.play.assert_not_called()

def test_playingALoadedSoundEffectSetsVolumeAndPlaysIt(monkeypatch):
    stub = usePygameStub(monkeypatch, loadAll)
    service = SoundService()

    service.playDeathSoundEffect()

    service.deathSoundEffect.set_volume.assert_called_once()
    stub.mixer.Sound.play.assert_called_once_with(service.deathSoundEffect)

# browser build tests --------------------------------------------------------
def test_desktopUsesTheWavFilesAndTheBrowserBuildTheOggCopies():
    assert soundService.soundPath("pop", "linux").endswith("pop.wav")
    assert soundService.soundPath("pain", "win32").endswith("pain.wav")
    assert soundService.soundPath("pop", "emscripten").endswith("pop.ogg")
    assert soundService.soundPath("pain", "emscripten").endswith("pain.ogg")

@pytest.mark.parametrize("name", ["pop", "pain"])
def test_everySoundShipsInBothFormatsAndBothDecode(name):
    # the browser build plays the .ogg copy; both have to be real, decodable audio
    try:
        pygame.mixer.init()
    except pygame.error as e:
        pytest.skip("no audio device to decode with: " + str(e))
    try:
        for platform in ("linux", "emscripten"):
            sound = pygame.mixer.Sound(soundService.soundPath(name, platform))
            assert sound.get_length() > 0.5
    finally:
        pygame.mixer.quit()

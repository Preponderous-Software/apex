from unittest.mock import MagicMock

import pytest

from screen.screenType import ScreenType
from screen.setupScreen import SetupScreen
from simulation.config import Config


# helper methods -------------------------------------------------------------
def getTestScreen():
    graphik = MagicMock()
    graphik.getGameDisplay.return_value.get_size.return_value = (1280, 720)
    return SetupScreen(graphik, Config())

def getButtons(screen):
    # drawButton(xpos, ypos, width, height, backgroundColor, textColor, textSize, text, function)
    return {call.args[7]: call.args[8] for call in screen.graphik.drawButton.call_args_list}

def getLabels(screen):
    return [call.args[0] for call in screen.graphik.drawText.call_args_list]


# navigation tests -----------------------------------------------------------
def test_initialization():
    screen = getTestScreen()
    assert screen.nextScreen == ScreenType.SIMULATION_SCREEN
    assert screen.changeScreen == False

def test_switchToSimulationScreen():
    screen = getTestScreen()
    screen.switchToSimulationScreen()
    assert screen.nextScreen == ScreenType.SIMULATION_SCREEN
    assert screen.changeScreen == True

def test_switchToMainMenuScreen():
    screen = getTestScreen()
    screen.switchToMainMenuScreen()
    assert screen.nextScreen == ScreenType.MAIN_MENU_SCREEN
    assert screen.changeScreen == True


# config setter tests --------------------------------------------------------
@pytest.mark.parametrize(
    "option, decrease, increase, start, step",
    [
        ("gridSize", "decreaseGridSize", "increaseGridSize", 20, 1),
        ("grassFactor", "decreaseGrassFactor", "increaseGrassFactor", 5, 1),
        ("grassGrowTime", "decreaseGrassGrowTime", "increaseGrassGrowTime", 200, 10),
    ],
)
def test_settersStepTheConfigOption(option, decrease, increase, start, step):
    screen = getTestScreen()
    setattr(screen.config, option, start)

    getattr(screen, increase)()
    assert getattr(screen.config, option) == start + step

    getattr(screen, decrease)()
    getattr(screen, decrease)()
    assert getattr(screen.config, option) == start - step


@pytest.mark.parametrize(
    "option, decrease, increase, minimum, maximum",
    [
        ("gridSize", "decreaseGridSize", "increaseGridSize", 16, 64),
        ("grassFactor", "decreaseGrassFactor", "increaseGrassFactor", 1, 10),
        ("grassGrowTime", "decreaseGrassGrowTime", "increaseGrassGrowTime", 10, 1000),
    ],
)
def test_settersClampTheConfigOption(option, decrease, increase, minimum, maximum):
    screen = getTestScreen()

    setattr(screen.config, option, minimum)
    getattr(screen, decrease)()
    assert getattr(screen.config, option) == minimum

    setattr(screen.config, option, maximum)
    getattr(screen, increase)()
    assert getattr(screen.config, option) == maximum


def test_gridSizeCanBeRaisedPastTheConfigsRandomizationRange():
    # the setup screen's bounds (16..64) are its own, not Config.minGridSize/maxGridSize (16..32)
    screen = getTestScreen()
    screen.config.gridSize = screen.config.maxGridSize
    screen.increaseGridSize()
    assert screen.config.gridSize == screen.config.maxGridSize + 1


# drawing tests --------------------------------------------------------------
def test_drawMenuButtonsWiresEachButtonToItsHandler():
    screen = getTestScreen()
    screen.drawMenuButtons()
    buttons = getButtons(screen)

    assert buttons["main menu"] == screen.switchToMainMenuScreen
    assert buttons["start simulation"] == screen.switchToSimulationScreen
    # each config option gets a "-" and a "+" button; the dict keeps only the last pair drawn
    labels = [call.args[7] for call in screen.graphik.drawButton.call_args_list]
    assert labels == ["main menu", "start simulation", "-", "+", "-", "+", "-", "+"]
    handlers = [call.args[8] for call in screen.graphik.drawButton.call_args_list[2:]]
    assert handlers == [
        screen.decreaseGridSize,
        screen.increaseGridSize,
        screen.decreaseGrassFactor,
        screen.increaseGrassFactor,
        screen.decreaseGrassGrowTime,
        screen.increaseGrassGrowTime,
    ]

def test_drawMenuButtonsShowsTheCurrentConfigValues():
    screen = getTestScreen()
    screen.config.gridSize = 24
    screen.config.grassFactor = 7
    screen.config.grassGrowTime = 150

    screen.drawMenuButtons()

    assert getLabels(screen) == ["gridSize: 24", "grassFactor: 7", "grassGrowTime: 150"]

def test_drawText():
    screen = getTestScreen()
    screen.drawText()
    screen.graphik.drawText.assert_called_once_with("Setup", 640, 72, 64, (255, 255, 255))

def test_drawVersionDrawsNothingWithoutAVersionFile(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    screen = getTestScreen()
    screen.drawVersion()
    screen.graphik.drawText.assert_not_called()

def test_drawVersionDrawsTheVersionFileAtTheBottomCentre(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "version.txt").write_text("v1.2.3")
    screen = getTestScreen()
    screen.drawVersion()
    screen.graphik.drawText.assert_called_once_with("v1.2.3", 640, 710, 16, (255, 255, 255))

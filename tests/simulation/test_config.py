from math import ceil
import random

import pytest

from simulation.config import Config


# helper methods -------------------------------------------------------------
def getSpeciesFactorsAndCounts(config):
    return [
        (config.chickenFactor, config.numChickensToStart),
        (config.pigFactor, config.numPigsToStart),
        (config.cowFactor, config.numCowsToStart),
        (config.wolfFactor, config.numWolvesToStart),
        (config.foxFactor, config.numFoxesToStart),
        (config.rabbitFactor, config.numRabbitsToStart),
    ]

# randomized factor tests ----------------------------------------------------
@pytest.mark.parametrize("seed", range(20))
def test_randomFactorsFallWithinTheirRanges(seed):
    random.seed(seed)

    config = Config()

    assert 2 <= config.waterFactor < 5
    assert 1 <= config.rockFactor < 4
    assert 3 <= config.grassFactor < 10
    assert 1 <= config.chickenFactor < 10
    assert 0 <= config.pigFactor < 10
    assert 0 <= config.cowFactor < 10
    assert 0 <= config.wolfFactor < 5
    assert 0 <= config.foxFactor < 5
    assert 0 <= config.rabbitFactor < 10

@pytest.mark.parametrize("seed", range(20))
def test_gridSizeAndGrassGrowTimeExcludeTheirMaximums(seed):
    random.seed(seed)

    config = Config()

    assert config.minGridSize <= config.gridSize < config.maxGridSize
    assert config.minGrassGrowTime <= config.grassGrowTime < config.maxGrassGrowTime

# static value tests ---------------------------------------------------------
def test_staticValues():
    config = Config()

    assert config.livingEntityFactor == 0.2
    assert config.minGridSize == 16
    assert config.maxGridSize == 32
    assert config.displayWidth == 1280
    assert config.displayHeight == 720
    assert config.tickSpeed == 30
    assert config.maxTickSpeed == 60
    assert config.chanceToExcrete == 0.10
    assert config.chanceToReproduce == 0.02
    assert config.berryBushGrowTime == 300
    assert config.localViewSize == 4
    assert config.endSimulationUponAllLivingEntitiesDying == True
    assert config.autoRestart == True
    assert config.randomizeGridSizeUponRestart == True
    assert config.limitTickSpeed == True
    assert config.eyesEnabled == True
    assert config.localView == False
    assert config.highlightOldestEntity == False
    assert config.fullscreen == False
    assert config.muted == False

def test_setStaticValuesRestoresToggledSettings():
    config = Config()
    config.muted = True
    config.tickSpeed = 5
    config.localView = True

    config.setStaticValues()

    assert config.muted == False
    assert config.tickSpeed == 30
    assert config.localView == False

# calculated value tests -----------------------------------------------------
def test_calculateValuesDerivesCountsFromGridSizeAndFactors():
    config = Config()
    config.gridSize = 20
    config.grassFactor = 4
    config.waterFactor = 3
    config.rockFactor = 2
    config.chickenFactor = 7
    config.pigFactor = 0
    config.cowFactor = 3
    config.wolfFactor = 1
    config.foxFactor = 2
    config.rabbitFactor = 9

    config.calculateValues()

    assert config.textSize == ceil(720/37)
    assert config.numGrassEntities == 20*20*4
    assert config.numWaterEntities == 20*3
    assert config.numRockEntities == 20*2
    assert config.numChickensToStart == ceil(20*0.2*7)
    assert config.numPigsToStart == 0
    assert config.numCowsToStart == ceil(20*0.2*3)
    assert config.numWolvesToStart == ceil(20*0.2*1)
    assert config.numFoxesToStart == ceil(20*0.2*2)
    assert config.numRabbitsToStart == ceil(20*0.2*9)
    assert config.maxLocalViewSize == 8
    assert config.numBerriesEntities == ceil(20*20*0.1)
    assert config.numBerryBushEntities == ceil(20*20*0.01)

def test_calculateValuesRoundsSpeciesCountsUp():
    config = Config()
    config.gridSize = 17
    config.chickenFactor = 1

    config.calculateValues()

    # 17 * 0.2 * 1 = 3.4 (approximately) rounds up to 4
    assert config.numChickensToStart == 4

def test_constructorCalculatesValuesFromItsRandomizedState():
    config = Config()

    assert config.numWaterEntities == ceil(config.gridSize*config.waterFactor)
    assert config.numGrassEntities == ceil(config.gridSize*config.gridSize*config.grassFactor)
    for factor, count in getSpeciesFactorsAndCounts(config):
        assert count == ceil(config.gridSize*config.livingEntityFactor*factor)

def test_aSpeciesWithAZeroFactorStartsWithNone():
    config = Config()
    config.wolfFactor = 0

    config.calculateValues()

    assert config.numWolvesToStart == 0

def test_calculateValuesIsNotTriggeredByRandomizingTheGridSize():
    config = Config()
    config.gridSize = 16
    config.calculateValues()
    numWaterEntities = config.numWaterEntities
    config.minGridSize = 30
    config.maxGridSize = 31

    config.randomizeGridSize()

    assert config.gridSize == 30
    assert config.numWaterEntities == numWaterEntities

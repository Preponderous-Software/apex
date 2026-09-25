import unittest
from simulation.simulationController import SimulationController
from simulation.simulation import Simulation
from simulation.config import Config
from entity.chicken import Chicken
from entity.pig import Pig

class MockSoundService:
    def playReproduceSoundEffect(self):
        pass
    def playDeathSoundEffect(self):
        pass

class MockDisplay:
    def __init__(self, config):
        self.config = config
    def get_size(self):
        return (self.config.displayWidth, self.config.displayHeight)

class TestSimulationController(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = Config()
        mockDisplay = MockDisplay(self.config)
        mockSoundService = MockSoundService()
        self.simulation = Simulation("Test", self.config, mockDisplay, mockSoundService)
        self.controller = SimulationController(self.simulation, self.config)
    
    def test_togglePause(self):
        """Test pause toggle functionality."""
        self.assertFalse(self.controller.isPaused())
        self.controller.togglePause()
        self.assertTrue(self.controller.isPaused())
        self.controller.togglePause()
        self.assertFalse(self.controller.isPaused())
    
    def test_toggleDebug(self):
        """Test debug toggle functionality."""
        self.assertFalse(self.controller.isDebug())
        self.controller.toggleDebug()
        self.assertTrue(self.controller.isDebug())
        self.controller.toggleDebug()
        self.assertFalse(self.controller.isDebug())
    
    def test_tickSpeedControl(self):
        """Test tick speed control."""
        initialSpeed = self.config.tickSpeed
        self.controller.increaseTickSpeed()
        self.assertEqual(self.config.tickSpeed, initialSpeed + 1)
        self.controller.decreaseTickSpeed()
        self.assertEqual(self.config.tickSpeed, initialSpeed)
    
    def test_tickSpeedLimit(self):
        """Test tick speed limit toggle."""
        initialLimit = self.config.limitTickSpeed
        self.controller.toggleTickSpeedLimit()
        self.assertEqual(self.config.limitTickSpeed, not initialLimit)
        self.controller.toggleTickSpeedLimit()
        self.assertEqual(self.config.limitTickSpeed, initialLimit)
    
    def test_spawnChicken(self):
        """Test chicken spawning."""
        initialCount = len(self.simulation.entities)
        chicken = self.controller.spawnChicken()
        self.assertIsInstance(chicken, Chicken)
        self.assertEqual(len(self.simulation.entities), initialCount + 1)
    
    def test_spawnPig(self):
        """Test pig spawning."""
        initialCount = len(self.simulation.entities)
        pig = self.controller.spawnPig()
        self.assertIsInstance(pig, Pig)
        self.assertEqual(len(self.simulation.entities), initialCount + 1)
    
    def test_update(self):
        """Test simulation update through controller."""
        initialTicks = self.simulation.numTicks
        self.controller.update()
        self.assertEqual(self.simulation.numTicks, initialTicks + 1)
    
    def test_updateWhenPaused(self):
        """Test that simulation doesn't update when paused."""
        self.controller.togglePause()
        initialTicks = self.simulation.numTicks
        self.controller.update()
        # When paused, ticks should not increase
        self.assertEqual(self.simulation.numTicks, initialTicks)
    
    def test_shouldEnd(self):
        """Test shouldEnd logic."""
        # With entities, should not end
        self.simulation.generateInitialEntities()
        self.assertFalse(self.controller.shouldEnd())

if __name__ == '__main__':
    unittest.main()

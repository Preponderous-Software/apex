from entity.chicken import Chicken
from entity.cow import Cow
from entity.fox import Fox
from entity.pig import Pig
from entity.rabbit import Rabbit
from entity.wolf import Wolf

# @author Daniel McCoy Stephenson
# @since October 16th, 2024
class SimulationController:
    """
    Controller that abstracts gameplay actions from UI implementation.
    This allows both pygame and text UIs to interact with the simulation
    in a consistent way without duplicating gameplay logic.
    """
    
    def __init__(self, simulation, config):
        self.simulation = simulation
        self.config = config
        self.paused = False
        self.debug = False
    
    # State control methods
    def togglePause(self):
        """Toggle pause state."""
        self.paused = not self.paused
        return self.paused
    
    def setPaused(self, paused):
        """Set pause state."""
        self.paused = paused
    
    def isPaused(self):
        """Get pause state."""
        return self.paused
    
    def toggleDebug(self):
        """Toggle debug mode."""
        self.debug = not self.debug
        return self.debug
    
    def isDebug(self):
        """Get debug state."""
        return self.debug
    
    def quit(self):
        """Quit the simulation."""
        self.simulation.cleanup()
        self.simulation.running = False
    
    # Speed control methods
    def toggleTickSpeedLimit(self):
        """Toggle tick speed limit."""
        self.config.limitTickSpeed = not self.config.limitTickSpeed
        return self.config.limitTickSpeed
    
    def increaseTickSpeed(self):
        """Increase tick speed if below max."""
        if self.config.tickSpeed < self.config.maxTickSpeed:
            self.config.tickSpeed += 1
        return self.config.tickSpeed
    
    def decreaseTickSpeed(self):
        """Decrease tick speed if above min."""
        if self.config.tickSpeed > 1:
            self.config.tickSpeed -= 1
        return self.config.tickSpeed
    
    # Entity spawning methods
    def spawnChicken(self):
        """Spawn a new chicken entity."""
        chicken = Chicken("player-created-chicken")
        self.simulation.environment.addEntity(chicken)
        self.simulation.addEntityToTrackedEntities(chicken)
        return chicken
    
    def spawnPig(self):
        """Spawn a new pig entity."""
        pig = Pig("player-created-pig")
        self.simulation.environment.addEntity(pig)
        self.simulation.addEntityToTrackedEntities(pig)
        return pig
    
    def spawnCow(self):
        """Spawn a new cow entity."""
        cow = Cow("player-created-cow")
        self.simulation.environment.addEntity(cow)
        self.simulation.addEntityToTrackedEntities(cow)
        return cow
    
    def spawnWolf(self):
        """Spawn a new wolf entity."""
        wolf = Wolf("player-created-wolf")
        self.simulation.environment.addEntity(wolf)
        self.simulation.addEntityToTrackedEntities(wolf)
        return wolf
    
    def spawnFox(self):
        """Spawn a new fox entity."""
        fox = Fox("player-created-fox")
        self.simulation.environment.addEntity(fox)
        self.simulation.addEntityToTrackedEntities(fox)
        return fox
    
    def spawnRabbit(self):
        """Spawn a new rabbit entity."""
        rabbit = Rabbit("player-created-rabbit")
        self.simulation.environment.addEntity(rabbit)
        self.simulation.addEntityToTrackedEntities(rabbit)
        return rabbit
    
    # Simulation update method
    def update(self):
        """Update simulation if not paused."""
        if not self.paused:
            self.simulation.update()
            self.simulation.numTicks += 1
    
    # Query methods
    def shouldEnd(self):
        """Check if simulation should end."""
        if self.config.endSimulationUponAllLivingEntitiesDying:
            return self.simulation.getNumLivingEntities() == 0
        return False
    
    def getSimulation(self):
        """Get the simulation instance."""
        return self.simulation
    
    def getConfig(self):
        """Get the config instance."""
        return self.config

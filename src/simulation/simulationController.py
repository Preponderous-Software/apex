from entity.chicken import Chicken
from entity.cow import Cow
from entity.fox import Fox
from entity.pig import Pig
from entity.rabbit import Rabbit
from entity.wolf import Wolf


# The gameplay actions a front end can take on a running simulation (pause, tick speed, spawning,
# stepping), kept apart from any one way of drawing it, so the text UI (textSimulationRunner.py)
# drives the same rules the pygame simulation screen does.
#
# @author Daniel McCoy Stephenson
# @since October 18th, 2026
class SimulationController:
    # the living entities a player can spawn, by the key that spawns them in both UIs
    SPAWNABLE = {
        "c": (Chicken, "player-created-chicken"),
        "p": (Pig, "player-created-pig"),
        "k": (Cow, "player-created-cow"),
        "w": (Wolf, "player-created-wolf"),
        "f": (Fox, "player-created-fox"),
        "b": (Rabbit, "player-created-rabbit"),
    }

    def __init__(self, simulation, config):
        self.simulation = simulation
        self.config = config
        self.paused = False

    def isPaused(self):
        return self.paused

    def togglePause(self):
        self.paused = not self.paused
        return self.paused

    def toggleTickSpeedLimit(self):
        self.config.limitTickSpeed = not self.config.limitTickSpeed
        return self.config.limitTickSpeed

    def increaseTickSpeed(self):
        if self.config.tickSpeed < self.config.maxTickSpeed:
            self.config.tickSpeed += 1
        return self.config.tickSpeed

    def decreaseTickSpeed(self):
        if self.config.tickSpeed > 1:
            self.config.tickSpeed -= 1
        return self.config.tickSpeed

    # Seconds to wait between ticks: the same formula the pygame screen sleeps for, or 0 when the
    # tick speed limit is off.
    def getTickDelay(self):
        if not self.config.limitTickSpeed:
            return 0
        return (self.config.maxTickSpeed - self.config.tickSpeed) / self.config.maxTickSpeed

    # Spawns the living entity bound to a key at a random location; returns it, or None for a key
    # that spawns nothing.
    def spawn(self, key):
        if key not in self.SPAWNABLE:
            return None
        entityClass, name = self.SPAWNABLE[key]
        entity = entityClass(name)
        self.simulation.environment.addEntity(entity)
        self.simulation.addEntityToTrackedEntities(entity)
        return entity

    # Advances the simulation one tick, unless it is paused or has been ended (quit, restart, or
    # every living entity gone), so no tick runs after cleanup. Returns whether a tick ran.
    def update(self):
        if self.paused or not self.simulation.running:
            return False
        self.simulation.update()
        self.simulation.numTicks += 1
        return True

    def shouldEnd(self):
        return self.config.endSimulationUponAllLivingEntitiesDying and self.simulation.getNumLivingEntities() == 0

    # Ends the simulation: no further update() runs.
    def end(self):
        self.simulation.running = False

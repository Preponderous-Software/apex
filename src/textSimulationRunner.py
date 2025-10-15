import time
import os
import sys
from entity.chicken import Chicken
from entity.cow import Cow
from entity.fox import Fox
from entity.grass import Grass
from entity.pig import Pig
from entity.rabbit import Rabbit
from entity.wolf import Wolf
from simulation.config import Config
from simulation.simulation import Simulation

# @author Daniel McCoy Stephenson
# @since October 15th, 2024

class MockSoundService:
    """Mock sound service that doesn't require pygame."""
    def playReproduceSoundEffect(self):
        pass
    
    def playDeathSoundEffect(self):
        pass


class TextSimulationRunner:
    """
    A text-based simulation runner that displays simulation stats to the console
    without using pygame graphics.
    """
    
    def __init__(self, config: Config = None):
        self.config = config if config else Config()
        self.simulation = None
        self.running = True
        self.paused = False
        self.updateInterval = 1.0  # seconds between display updates
        
    def run(self):
        """Runs the text-based simulation."""
        print("=" * 60)
        print("Apex Ecosystem Simulator - Text Mode")
        print("=" * 60)
        print()
        print("Commands:")
        print("  Ctrl+C: Quit simulation")
        print()
        
        # Initialize simulation
        self.initializeSimulation()
        
        # Main loop
        try:
            lastDisplayTime = time.time()
            while self.running:
                # Update simulation
                self.simulation.update()
                self.simulation.numTicks += 1
                
                # Display stats periodically
                currentTime = time.time()
                if currentTime - lastDisplayTime >= self.updateInterval:
                    self.displayStats()
                    lastDisplayTime = currentTime
                
                # Check if simulation should end
                if self.config.endSimulationUponAllLivingEntitiesDying:
                    if self.simulation.getNumLivingEntities() == 0:
                        print("\nAll living entities have died. Simulation ended.")
                        self.simulation.cleanup()
                        self.running = False
                
                # Apply tick speed limit
                if self.config.limitTickSpeed:
                    time.sleep((self.config.maxTickSpeed - self.config.tickSpeed) / self.config.maxTickSpeed)
                    
        except KeyboardInterrupt:
            print("\n\nSimulation interrupted by user.")
            self.simulation.cleanup()
            
    def initializeSimulation(self):
        """Initializes the simulation with a mock game display."""
        name = "Text-Based Simulation"
        
        # Create a mock display object for simulation initialization
        class MockDisplay:
            def get_size(self):
                return (self.config.displayWidth, self.config.displayHeight)
        
        mockDisplay = MockDisplay()
        mockDisplay.config = self.config
        
        # Create simulation with mock sound service
        mockSoundService = MockSoundService()
        self.simulation = Simulation(name, self.config, mockDisplay, mockSoundService)
        
        self.simulation.generateInitialEntities()
        self.simulation.placeInitialEntitiesInEnvironment()
        self.simulation.environment.printInfo()
        
        print(f"Simulation initialized: {name}")
        print(f"Grid size: {self.simulation.environment.getGrid().getColumns()}x{self.simulation.environment.getGrid().getRows()}")
        print()
        
    def displayStats(self):
        """Displays current simulation statistics to the console."""
        # Clear screen (works on Unix-like systems)
        if os.name != 'nt':
            os.system('clear')
        else:
            os.system('cls')
            
        print("=" * 60)
        print(f"Tick: {self.simulation.numTicks}")
        print("=" * 60)
        print()
        
        print(f"Total Entities:         {len(self.simulation.entities)}")
        print(f"Living Entities:        {self.simulation.getNumLivingEntities()}")
        print(f"Grass:                  {self.simulation.getNumberOfEntitiesOfType(Grass)}")
        print(f"Excrement:              {self.simulation.getNumExcrement()}")
        print()
        
        print("Living Entity Counts:")
        print(f"  Chickens:             {self.simulation.getNumberOfLivingEntitiesOfType(Chicken)}")
        print(f"  Pigs:                 {self.simulation.getNumberOfLivingEntitiesOfType(Pig)}")
        print(f"  Cows:                 {self.simulation.getNumberOfLivingEntitiesOfType(Cow)}")
        print(f"  Wolves:               {self.simulation.getNumberOfLivingEntitiesOfType(Wolf)}")
        print(f"  Foxes:                {self.simulation.getNumberOfLivingEntitiesOfType(Fox)}")
        print(f"  Rabbits:              {self.simulation.getNumberOfLivingEntitiesOfType(Rabbit)}")
        print()
        
        if self.config.limitTickSpeed:
            print(f"Tick Speed:             {self.config.tickSpeed}/{self.config.maxTickSpeed}")
        
        print()
        print("Press Ctrl+C to quit")
        print("=" * 60)
